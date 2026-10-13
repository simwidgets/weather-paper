#pragma once
// System headers needed by the deep-sleep time-restore lambda + SNTP restart.
#include <esp_rtc_time.h>
#include <sys/time.h>
#include <time.h>
#include <esp_sntp.h>
#include <esp_sleep.h>
#include <esp_system.h>
#include "esp_random.h"
#include "esphome/components/json/json_util.h"
#include "esphome/core/alloc_helpers.h"
#include "esphome/components/captive_portal/captive_portal.h"
#include <string>
#include <cctype>
#include <cstring>
#include <cmath>

// Map an NWS shortForecast/textDescription string to an Open-Meteo-style WMO
// code so the existing wmo_glyph() icon mapping in the display lambda keeps
// working unchanged (0 clear / 1 partly / 3 overcast / 45 fog / 51 rain /
// 71 snow / 95 thunderstorm). Case-insensitive keyword match.
static inline int nws_code_from_text(const char *sf) {
  if (sf == nullptr)
    return 1;
  std::string s(sf);
  for (auto &c : s)
    c = (char) tolower((unsigned char) c);
  if (s.find("thunder") != std::string::npos || s.find("tstm") != std::string::npos ||
      s.find("t-storm") != std::string::npos)
    return 95;
  if (s.find("snow") != std::string::npos || s.find("flurr") != std::string::npos ||
      s.find("sleet") != std::string::npos || s.find("freez") != std::string::npos ||
      s.find("ice") != std::string::npos)
    return 71;
  if (s.find("rain") != std::string::npos || s.find("shower") != std::string::npos ||
      s.find("drizzle") != std::string::npos)
    return 51;
  if (s.find("fog") != std::string::npos || s.find("haze") != std::string::npos)
    return 45;
  if (s.find("sunny") != std::string::npos || s.find("clear") != std::string::npos)
    return (s.find("mostly") != std::string::npos || s.find("partly") != std::string::npos) ? 1 : 0;
  if (s.find("partly") != std::string::npos)
    return 1;
  if (s.find("cloudy") != std::string::npos || s.find("overcast") != std::string::npos)
    return 3;
  return 1;
}

// NWS wind chill (°F, wind in mph) — valid only when T <= 50F and wind > 3 mph.
static inline float wind_chill_f(float tf, float wind_mph) {
  float v = powf(wind_mph, 0.16f);
  return 35.74f + 0.6215f * tf - 35.75f * v + 0.4275f * tf * v;
}

// NWS heat index (Rothfusz regression, °F and RH %). Valid above 80F.
static inline float heat_index_f(float tf, float rh) {
  float t = tf, r = rh;
  float hi = -42.379f + 2.04901523f * t + 10.14333127f * r
             - 0.22475541f * t * r - 0.00683783f * t * t
             - 0.05481717f * r * r + 0.00122874f * t * t * r
             + 0.00085282f * t * r * r - 0.00000199f * t * t * r * r;
  if (r < 13.0f && t >= 80.0f && t <= 112.0f) {
    float adj = ((13.0f - r) / 4.0f) * sqrtf((17.0f - fabsf(t - 95.0f)) / 17.0f);
    hi -= adj;
  } else if (r > 85.0f && t >= 80.0f && t <= 87.0f) {
    float adj = ((r - 85.0f) / 10.0f) * ((87.0f - t) / 5.0f);
    hi += adj;
  }
  return hi;
}

