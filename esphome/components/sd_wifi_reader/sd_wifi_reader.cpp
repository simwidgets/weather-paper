#include "sd_wifi_reader.h"

#include "esphome/core/log.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "esp_vfs_fat.h"
#include "sdmmc_cmd.h"
#include "driver/sdspi_host.h"
#include "driver/spi_common.h"
#include "driver/gpio.h"
#include "esp_rtc_time.h"
#include "esp_mac.h"
#include "nvs.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#ifdef USE_WIFI
#include "esphome/components/wifi/wifi_component.h"
#endif

namespace esphome {
namespace sd_wifi_reader {

static const char *const TAG = "sd_wifi_reader";

// Power on the microSD slot (GPIO 42 = SDCARD_PWR), init its SPI bus, mount.
static bool mount_card(sdmmc_card_t **card_out) {
  gpio_config_t pwr_conf = {
      .pin_bit_mask = 1ULL << 42,
      .mode = GPIO_MODE_OUTPUT,
      .pull_up_en = GPIO_PULLUP_DISABLE,
      .pull_down_en = GPIO_PULLDOWN_DISABLE,
      .intr_type = GPIO_INTR_DISABLE,
  };
  gpio_config(&pwr_conf);
  gpio_set_level(GPIO_NUM_42, 1);
  vTaskDelay(pdMS_TO_TICKS(100));  // let the card power up

  sdmmc_host_t host = SDSPI_HOST_DEFAULT();
  host.max_freq_khz = 1000;  // conservative; probing phase is 400kHz, data steps up

  spi_bus_config_t bus_cfg = {
      .mosi_io_num = 40,
      .miso_io_num = 13,
      .sclk_io_num = 39,
      .quadwp_io_num = -1,
      .quadhd_io_num = -1,
      .max_transfer_sz = 4000,
  };

  esp_err_t ret = spi_bus_initialize(SPI2_HOST, &bus_cfg, SPI_DMA_CH_AUTO);
  if (ret != ESP_OK) {
    ESP_LOGW(TAG, "SPI bus init failed: %s", esp_err_to_name(ret));
    return false;
  }

  sdspi_device_config_t slot_config = {
      .host_id = SPI2_HOST,
      .gpio_cs = GPIO_NUM_10,
      .gpio_cd = SDSPI_SLOT_NO_CD,
      .gpio_wp = SDSPI_SLOT_NO_WP,
      .gpio_int = SDSPI_SLOT_NO_INT,
  };

  esp_vfs_fat_mount_config_t mount_config = {
      .format_if_mount_failed = false,
      .max_files = 5,
      .allocation_unit_size = 16 * 1024,
  };

  ret = esp_vfs_fat_sdspi_mount("/sdcard", &host, &slot_config, &mount_config, card_out);
  if (ret != ESP_OK) {
    ESP_LOGW(TAG, "SD mount failed: %s", esp_err_to_name(ret));
    spi_bus_free(SPI2_HOST);
    return false;
  }
  return true;
}

static void unmount_card(sdmmc_card_t *card) {
  esp_vfs_fat_sdcard_unmount("/sdcard", card);
  spi_bus_free(SPI2_HOST);
}

// Append a diagnostic line to /sdcard/log.txt. Call only while the card is
// mounted. Timestamp = seconds since last full power-on (esp_rtc_get_time_us
// survives deep sleep, so it's a monotonic boot clock, not wall time).
static void sd_log(const char *msg) {
  FILE *f = fopen("/sdcard/log.txt", "a");
  if (f == nullptr)
    return;
  fprintf(f, "[%llu] %s\n", (unsigned long long) (esp_rtc_get_time_us() / 1000000ULL), msg);
  fclose(f);
}

void SDWiFiReader::parse_config_line(const std::string &section, const std::string &key,
                                     const std::string &value) {
  if (section == "wifi") {
    if (key == "ssid") {
      this->ssid_ = value;
    } else if (key == "password") {
      this->password_ = value;
    } else if (key == "enabled") {
      this->wifi_enabled_ = (value != "0" && value != "false" && value != "off" && value != "no");
    }
  } else if (section == "ruuvi") {
    if (key == "mac") {
      this->sensor_mac_ = value;
    } else if (key == "enabled") {
      this->ruuvi_enabled_ = (value != "0" && value != "false" && value != "off" && value != "no");
      this->ruuvi_enabled_set_ = true;
    }
  } else if (section == "units") {
    if (key == "temperature")
      this->temp_c_ = (value == "C" || value == "c");
    else if (key == "pressure")
      this->press_hpa_ = (value == "hPa" || value == "hpa");
    else if (key == "time_format") {
      if (value == "ampm" || value == "12h" || value == "12")
        this->time_fmt_ = 1;
      else if (value == "utc")
        this->time_fmt_ = 2;
      else
        this->time_fmt_ = 0;
    }
  } else if (section == "weather") {
    if (key == "zip")
      this->zip_ = value;
    else if (key == "source")
      this->weather_wifi_ = (value != "ruuvi");
    else if (key == "lat")
      this->lat_ = atof(value.c_str());
    else if (key == "lon")
      this->lon_ = atof(value.c_str());
    else if (key == "nws_wfo")
      this->nws_wfo_ = value;
    else if (key == "nws_x")
      this->nws_x_ = atoi(value.c_str());
    else if (key == "nws_y")
      this->nws_y_ = atoi(value.c_str());
    else if (key == "nws_station")
      this->nws_station_ = value;
    else if (key == "nws_station2")
      this->nws_station2_ = value;
  } else if (section == "power") {
    if (key == "refresh")
      this->full_refresh_ = (value == "full");
    else if (key == "update")
      this->update_min_ = atoi(value.c_str());
  }
}

void SDWiFiReader::setup() {
  // Device ID = last 3 bytes of the STA MAC (unique per chip), used for the
  // setup AP name so multiple stations stay distinct.
  uint8_t mac[6];
  if (esp_read_mac(mac, ESP_MAC_WIFI_STA) == ESP_OK) {
    char id[8];
    snprintf(id, sizeof(id), "%02X%02X%02X", mac[3], mac[4], mac[5]);
    this->device_id_ = id;
  } else {
    this->device_id_ = "UNKNOWN";
  }

#ifdef USE_WIFI
  // Name the fallback AP with the device ID.
  if (esphome::wifi::global_wifi_component != nullptr) {
    esphome::wifi::WiFiAP ap;
    std::string ap_ssid = "WeatherPaper-" + this->device_id_;
    ap.set_ssid(ap_ssid);
    esphome::wifi::global_wifi_component->set_ap(ap);
  }
#endif

  sdmmc_card_t *card = nullptr;
  if (!mount_card(&card)) {
    ESP_LOGW(TAG, "SD unavailable, running with defaults");
    return;
  }

  // --- config.txt ---
  FILE *f = fopen("/sdcard/config.txt", "r");
  if (f == nullptr) {
    ESP_LOGW(TAG, "config.txt not found on SD");
    sd_log("ERROR config.txt not found on SD");
  } else {
    char line[128];
    std::string section;
    while (fgets(line, sizeof(line), f)) {
      line[strcspn(line, "\r\n")] = 0;
      int len = (int) strlen(line);
      while (len > 0 && (line[len - 1] == ' ' || line[len - 1] == '\t'))
        line[--len] = 0;
      if (line[0] == 0 || line[0] == '#')
        continue;
      if (line[0] == '[') {
        char *end = strchr(line, ']');
        if (end) {
          *end = 0;
          section = line + 1;
        } else {
          sd_log("ERROR malformed section header (no ']')");
        }
        continue;
      }
      char *eq = strchr(line, '=');
      if (!eq) {
        sd_log("ERROR malformed config line (no '=')");
        continue;
      }
      *eq = 0;
      int klen = (int) strlen(line);
      while (klen > 0 && (line[klen - 1] == ' ' || line[klen - 1] == '\t'))
        line[--klen] = 0;
      char *v = eq + 1;
      while (*v == ' ' || *v == '\t')
        v++;
      this->parse_config_line(section, line, v);
    }
    fclose(f);
  }

  // --- state.txt (last-known readings) ---
  f = fopen("/sdcard/state.txt", "r");
  if (f != nullptr) {
    char line[64];
    while (fgets(line, sizeof(line), f)) {
      line[strcspn(line, "\r\n")] = 0;
      char *eq = strchr(line, '=');
      if (!eq)
        continue;
      *eq = 0;
      float val = atof(eq + 1);
      if (strcmp(line, "temp") == 0)
        this->last_temp_ = val;
      else if (strcmp(line, "hum") == 0)
        this->last_hum_ = val;
      else if (strcmp(line, "press") == 0)
        this->last_press_ = val;
      else if (strcmp(line, "batt") == 0)
        this->last_batt_ = val;
      else if (strcmp(line, "move") == 0)
        this->last_move_ = (int) val;
    }
    fclose(f);
    this->has_last_ = true;
  }

  // --- history.txt (hourly pressure samples, hPa, oldest first) ---
  f = fopen("/sdcard/history.txt", "r");
  if (f != nullptr) {
    char hline[32];
    while (this->press_hist_count_ < HIST_MAX && fgets(hline, sizeof(hline), f)) {
      float hv = atof(hline);
      if (hv > 500.0f && hv < 1200.0f)
        this->press_hist_[this->press_hist_count_++] = hv;
    }
    fclose(f);
  }

  // Ruuvi enabled defaults to "has a MAC" when the flag isn't explicit.
  if (!this->ruuvi_enabled_set_)
    this->ruuvi_enabled_ = !this->sensor_mac_.empty();

  this->has_creds_ = !this->ssid_.empty();
  if (this->ssid_.empty())
    sd_log("WARN no wifi ssid in config.txt");
  if (this->sensor_mac_.empty())
    sd_log("WARN no ruuvi mac in config.txt");
  if (this->zip_.empty() && this->weather_wifi_)
    sd_log("WARN no weather zip in config.txt");

  unmount_card(card);

  ESP_LOGI(TAG,
           "config.txt: ssid='%s' pw_len=%d mac='%s' wifi=%d tempC=%d hpa=%d zip='%s' weather=%s",
           this->ssid_.c_str(), (int) this->password_.size(), this->sensor_mac_.c_str(),
           (int) this->wifi_enabled_, (int) this->temp_c_, (int) this->press_hpa_, this->zip_.c_str(),
           this->weather_wifi_ ? "wifi" : "ruuvi");

  if (!this->has_creds_) {
    ESP_LOGW(TAG, "no wifi credentials in config.txt");
    return;
  }

#ifdef USE_WIFI
  if (esphome::wifi::global_wifi_component != nullptr) {
    esphome::wifi::WiFiAP ap;
    ap.set_ssid(this->ssid_);
    ap.set_password(this->password_);
    esphome::wifi::global_wifi_component->set_sta(ap);
    ESP_LOGI(TAG, "WiFi credentials applied from config.txt");
  }
#endif
}

void SDWiFiReader::save_config(bool wifi_on, bool temp_c, bool press_hpa, bool weather_wifi,
                               bool full_refresh, int update_min, bool ruuvi_enabled, int time_fmt) {
  this->wifi_enabled_ = wifi_on;
  this->temp_c_ = temp_c;
  this->press_hpa_ = press_hpa;
  this->weather_wifi_ = weather_wifi;
  this->full_refresh_ = full_refresh;
  this->update_min_ = update_min;
  this->ruuvi_enabled_ = ruuvi_enabled;
  this->time_fmt_ = time_fmt;
  this->rewrite_config();
}

void SDWiFiReader::save_lat_lon(float lat, float lon) {
  this->lat_ = lat;
  this->lon_ = lon;
  this->rewrite_config();
}

void SDWiFiReader::save_wifi_creds(const std::string &ssid, const std::string &psk,
                                   const std::string &zip) {
  this->ssid_ = ssid;
  this->password_ = psk;
  this->zip_ = zip;
  this->wifi_enabled_ = true;
  this->has_creds_ = true;
  this->rewrite_config();
}

void SDWiFiReader::factory_reset() {
  this->ssid_.clear();
  this->password_.clear();
  this->wifi_enabled_ = true;
  this->has_creds_ = false;
  this->sensor_mac_.clear();
  this->ruuvi_enabled_ = false;
  this->ruuvi_enabled_set_ = false;
  this->temp_c_ = false;
  this->press_hpa_ = false;
  this->time_fmt_ = 0;
  this->zip_.clear();
  this->weather_wifi_ = true;
  this->lat_ = 0.0f;
  this->lon_ = 0.0f;
  this->nws_wfo_.clear();
  this->nws_x_ = 0;
  this->nws_y_ = 0;
  this->nws_station_.clear();
  this->nws_station2_.clear();
  this->full_refresh_ = false;
  this->update_min_ = 60;
  this->rewrite_config();
}

void SDWiFiReader::save_nws_grid(const std::string &wfo, int x, int y) {
  this->nws_wfo_ = wfo;
  this->nws_x_ = x;
  this->nws_y_ = y;
  this->rewrite_config();
}

void SDWiFiReader::save_nws_station(const std::string &station) {
  this->nws_station_ = station;
  this->rewrite_config();
}

void SDWiFiReader::save_nws_station2(const std::string &station) {
  this->nws_station2_ = station;
  this->rewrite_config();
}

void SDWiFiReader::clear_nws_cache() {
  this->nws_wfo_.clear();
  this->nws_x_ = 0;
  this->nws_y_ = 0;
  this->nws_station_.clear();
  this->nws_station2_.clear();
  this->rewrite_config();
}

void SDWiFiReader::rewrite_config() {
  sdmmc_card_t *card = nullptr;
  if (!mount_card(&card)) {
    ESP_LOGW(TAG, "rewrite_config: SD mount failed");
    return;
  }
  FILE *f = fopen("/sdcard/config.txt", "w");
  if (f != nullptr) {
    fprintf(f, "[wifi]\nssid=%s\npassword=%s\nenabled=%d\n\n", this->ssid_.c_str(),
            this->password_.c_str(), this->wifi_enabled_ ? 1 : 0);
    fprintf(f, "[ruuvi]\nmac=%s\nenabled=%d\n\n", this->sensor_mac_.c_str(), this->ruuvi_enabled_ ? 1 : 0);
    const char *tf = this->time_fmt_ == 1 ? "ampm" : (this->time_fmt_ == 2 ? "utc" : "24h");
    fprintf(f, "[units]\ntemperature=%s\npressure=%s\ntime_format=%s\n\n", this->temp_c_ ? "C" : "F",
            this->press_hpa_ ? "hPa" : "inHg", tf);
    fprintf(f, "[weather]\nzip=%s\nsource=%s\nlat=%.4f\nlon=%.4f\nnws_wfo=%s\nnws_x=%d\nnws_y=%d\nnws_station=%s\nnws_station2=%s\n\n",
            this->zip_.c_str(), this->weather_wifi_ ? "wifi" : "ruuvi", this->lat_, this->lon_,
            this->nws_wfo_.c_str(), this->nws_x_, this->nws_y_, this->nws_station_.c_str(),
            this->nws_station2_.c_str());
    fprintf(f, "[power]\nrefresh=%s\nupdate=%d\n", this->full_refresh_ ? "full" : "partial",
            this->update_min_);
    fclose(f);
    ESP_LOGI(TAG, "config.txt saved");
  } else {
    ESP_LOGW(TAG, "rewrite_config: could not open config.txt for write");
  }
  unmount_card(card);
}

void SDWiFiReader::save_state(float temp, float hum, float press, float batt, int move) {
  sdmmc_card_t *card = nullptr;
  if (!mount_card(&card)) {
    ESP_LOGW(TAG, "save_state: SD mount failed");
    return;
  }
  FILE *f = fopen("/sdcard/state.txt", "w");
  if (f != nullptr) {
    fprintf(f, "temp=%.2f\nhum=%.1f\npress=%.1f\nbatt=%.2f\nmove=%d\n", temp, hum, press, batt, move);
    fclose(f);
  }
  unmount_card(card);
}

void SDWiFiReader::save_pressure_sample(float hpa) {
  // Ring buffer: shift left when full, else append.
  if (this->press_hist_count_ >= HIST_MAX) {
    for (size_t i = 1; i < HIST_MAX; i++)
      this->press_hist_[i - 1] = this->press_hist_[i];
    this->press_hist_[HIST_MAX - 1] = hpa;
  } else {
    this->press_hist_[this->press_hist_count_++] = hpa;
  }

  // Rewrite history.txt with the current ring buffer.
  sdmmc_card_t *card = nullptr;
  if (!mount_card(&card)) {
    ESP_LOGW(TAG, "save_pressure_sample: SD mount failed");
    return;
  }
  FILE *f = fopen("/sdcard/history.txt", "w");
  if (f != nullptr) {
    for (uint16_t i = 0; i < this->press_hist_count_; i++)
      fprintf(f, "%.1f\n", this->press_hist_[i]);
    fclose(f);
  }
  unmount_card(card);
}

static const char *const FRAME_NS = "frame";
static const char *const FRAME_KEY = "prev";

bool SDWiFiReader::read_frame(uint8_t *buf) {
  if (buf == nullptr)
    return false;
  nvs_handle_t handle;
  if (nvs_open(FRAME_NS, NVS_READONLY, &handle) != ESP_OK)
    return false;
  size_t len = FRAME_BYTES;
  esp_err_t err = nvs_get_blob(handle, FRAME_KEY, buf, &len);
  nvs_close(handle);
  return err == ESP_OK && len == FRAME_BYTES;
}

void SDWiFiReader::write_frame(const uint8_t *buf) {
  if (buf == nullptr)
    return;
  nvs_handle_t handle;
  if (nvs_open(FRAME_NS, NVS_READWRITE, &handle) != ESP_OK)
    return;
  esp_err_t err = nvs_set_blob(handle, FRAME_KEY, buf, FRAME_BYTES);
  if (err == ESP_OK)
    nvs_commit(handle);
  nvs_close(handle);
  static bool logged = false;
  if (!logged) {
    ESP_LOGI(TAG, "frame write %s (%u bytes)", err == ESP_OK ? "ok" : esp_err_to_name(err),
             (unsigned) FRAME_BYTES);
    logged = true;
  }
}

}  // namespace sd_wifi_reader
}  // namespace esphome
