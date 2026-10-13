#pragma once

#include "esphome/core/component.h"

#include <string>

namespace esphome {
namespace sd_wifi_reader {

// Reads/writes the SD-card config on the CrowPanel 5.79".
//
//   config.txt  — user settings, INI-style sections:
//                  [wifi]    ssid=... password=... enabled=0|1
//                  [ruuvi]   mac=DE:31:C3:1E:52:31
//                  [units]   temperature=F|C   pressure=inHg|hPa
//                  [weather] zip=75001  source=wifi|ruuvi
//   state.txt   — last-known Ruuvi readings (flat key=value), rewritten
//                 periodically so a reboot can show the last values before
//                 fresh BLE data arrives:
//                  temp=23.5 hum=42.0 press=1015.2 batt=2.94 move=137
class SDWiFiReader : public Component {
 public:
  void setup() override;
  float get_setup_priority() const override { return setup_priority::DATA; }

  bool has_credentials() const { return has_creds_; }
  const std::string &get_ssid() const { return ssid_; }
  const std::string &get_password() const { return password_; }
  const std::string &get_sensor_mac() const { return sensor_mac_; }
  bool get_wifi_enabled() const { return wifi_enabled_; }
  bool get_temp_c() const { return temp_c_; }
  bool get_press_hpa() const { return press_hpa_; }
  const std::string &get_zip() const { return zip_; }
  bool get_weather_wifi() const { return weather_wifi_; }
  bool get_full_refresh() const { return full_refresh_; }
  int get_update_min() const { return update_min_; }
  float get_lat() const { return lat_; }
  float get_lon() const { return lon_; }
  const std::string &get_nws_wfo() const { return nws_wfo_; }
  int get_nws_x() const { return nws_x_; }
  int get_nws_y() const { return nws_y_; }
  const std::string &get_nws_station() const { return nws_station_; }
  const std::string &get_nws_station2() const { return nws_station2_; }
  bool get_ruuvi_enabled() const { return ruuvi_enabled_; }
  const std::string &get_device_id() const { return device_id_; }
  int get_time_fmt() const { return time_fmt_; }

  bool has_last() const { return has_last_; }
  float get_last_temp() const { return last_temp_; }
  float get_last_hum() const { return last_hum_; }
  float get_last_press() const { return last_press_; }
  float get_last_batt() const { return last_batt_; }
  int get_last_move() const { return last_move_; }

  // Pressure history (14 days x 24 hourly samples, oldest first, hPa).
  static constexpr size_t HIST_MAX = 336;
  uint16_t get_press_hist_count() const { return press_hist_count_; }
  const float *get_press_hist() const { return press_hist_; }
  // Append an hourly pressure sample (hPa) to the ring buffer + SD history.txt.
  void save_pressure_sample(float hpa);

  // Rewrite config.txt with the runtime-togglable settings (ssid/pw/mac/zip are
  // kept from the values read at boot). Re-mounts the SD card, writes, unmounts.
  void save_config(bool wifi_on, bool temp_c, bool press_hpa, bool weather_wifi, bool full_refresh,
                   int update_min, bool ruuvi_enabled, int time_fmt);
  // Persist a geocoded lat/lon to config.txt (rewrites [weather] lat=/lon=).
  void save_lat_lon(float lat, float lon);
  // Persist WiFi credentials + zip (from the setup portal) to config.txt.
  void save_wifi_creds(const std::string &ssid, const std::string &psk, const std::string &zip);
  // Wipe all settings back to defaults (empty wifi/zip, default units) + rewrite config.txt.
  void factory_reset();
  // Persist the NWS gridpoint (WFO/x/y) and station id to config.txt.
  void save_nws_grid(const std::string &wfo, int x, int y);
  void save_nws_station(const std::string &station);
  void save_nws_station2(const std::string &station);
  // Clear the cached NWS gridpoint + stations (called after a zip change).
  void clear_nws_cache();
  // Rewrite state.txt with the given readings. Re-mounts, writes, unmounts.
  void save_state(float temp, float hum, float press, float batt, int move);

  // Persist/restore the display frame (792*272/8 bytes) in NVS, so a partial
  // refresh can seed the controller's OLD RAM after a deep-sleep wake.
  static constexpr size_t FRAME_BYTES = 792 * 272 / 8;
  bool read_frame(uint8_t *buf);
  void write_frame(const uint8_t *buf);

 protected:
  void parse_config_line(const std::string &section, const std::string &key, const std::string &value);
  void rewrite_config();

  bool has_creds_{false};
  std::string ssid_, password_, sensor_mac_;
  bool wifi_enabled_{true};
  bool temp_c_{false};
  bool press_hpa_{false};
  std::string zip_;
  float lat_{0.0f}, lon_{0.0f};
  std::string nws_wfo_, nws_station_, nws_station2_;
  int nws_x_{0}, nws_y_{0};
  bool weather_wifi_{true};
  bool full_refresh_{false};
  int update_min_{60};
  bool ruuvi_enabled_{false};
  bool ruuvi_enabled_set_{false};
  std::string device_id_;
  int time_fmt_{0};  // 0 = 24h, 1 = AM/PM, 2 = UTC

  bool has_last_{false};
  float last_temp_{0.0f}, last_hum_{0.0f}, last_press_{0.0f}, last_batt_{0.0f};
  int last_move_{0};

  float press_hist_[HIST_MAX];
  uint16_t press_hist_count_{0};
};

}  // namespace sd_wifi_reader
}  // namespace esphome
