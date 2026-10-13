#include "crowpanel_epaper.h"
#include "ssd1683.h"
#include "esphome/core/log.h"

namespace esphome {
namespace crowpanel_epaper {

static const char *const TAG = "epd_5p79";

// Dual SSD1683 in cascade mode.
// Primary  = left 400px, scans left-to-right.
// Secondary = right 400px, scans right-to-left (mirrored).
// The 8-pixel overlap (byte 49) is shared between both halves.
static const uint8_t SEQ_INIT[] = {
    CMD_SOFT_RESET, DELAY_BIT, 10,
    // Primary — left half
    CMD_DATA_ENTRY_MODE | TGT_PRIMARY, 0x01, ENTRY_X_INC_Y_INC,
    CMD_SET_X_ADDR | TGT_PRIMARY, 0x02, 0x00, 0x31,            // X: 0..49
    CMD_SET_Y_ADDR | TGT_PRIMARY, 0x04, 0x00, 0x00, 0x0F, 0x01, // Y: 0..271
    // Secondary — right half (mirrored)
    CMD_DATA_ENTRY_MODE | TGT_SECONDARY, 0x01, ENTRY_X_DEC_Y_INC,
    CMD_SET_X_ADDR | TGT_SECONDARY, 0x02, 0x31, 0x00,          // X: 49..0
    CMD_SET_Y_ADDR | TGT_SECONDARY, 0x04, 0x00, 0x00, 0x0F, 0x01,
    SEQ_END, SEQ_END,
};

static constexpr uint16_t ROW_BYTES  = WIDTH_5P79 / 8;      // 99
static constexpr uint16_t HALF_CEIL  = (ROW_BYTES + 1) / 2; // 50
static constexpr uint16_t HALF_FLOOR = ROW_BYTES / 2;       // 49
static constexpr uint16_t PARTIAL_ROWS = 88;  // clock strip height (above divider y=88)

void CrowPanelEPaper5P79In::init_display_() {
  ESP_LOGD(TAG, "Initialising 5.79\" cascade display");
  spi_send_sequence_(SEQ_INIT);
}

void CrowPanelEPaper5P79In::prepare_update_() {
  spi_command_(CMD_BORDER_WAVEFORM);
  spi_data_(is_full_update_ ? BORDER_FULL : BORDER_PARTIAL);

  spi_command_(CMD_UPDATE_CTRL1);
  spi_data_(is_full_update_ ? 0x40 : 0x00);
  spi_data_(CTRL1_CASCADE);

  // Y window: full refresh = whole panel, partial = clock strip only (top 88
  // rows), so the DU never touches the bottom (which otherwise ghosts).
  uint16_t y_start = 0;
  uint16_t y_end = is_full_update_ ? (HEIGHT_5P79 - 1) : (PARTIAL_ROWS - 1);
  spi_command_(CMD_SET_Y_ADDR | TGT_PRIMARY);
  spi_data_(y_start & 0xFF);
  spi_data_((y_start >> 8) & 0xFF);
  spi_data_(y_end & 0xFF);
  spi_data_((y_end >> 8) & 0xFF);
  spi_command_(CMD_SET_Y_ADDR | TGT_SECONDARY);
  spi_data_(y_start & 0xFF);
  spi_data_((y_start >> 8) & 0xFF);
  spi_data_(y_end & 0xFF);
  spi_data_((y_end >> 8) & 0xFF);

  // Primary cursor → top-left
  spi_command_(CMD_SET_X_CTR | TGT_PRIMARY);
  spi_data_(0x00);
  spi_command_(CMD_SET_Y_CTR | TGT_PRIMARY);
  spi_data_(0x00);
  spi_data_(0x00);

  // Secondary cursor → top-right
  spi_command_(CMD_SET_X_CTR | TGT_SECONDARY);
  spi_data_(0x31);
  spi_command_(CMD_SET_Y_CTR | TGT_SECONDARY);
  spi_data_(0x00);
  spi_data_(0x00);

  // Seed OLD RAM (0x26) on both cascade chips so the refresh diffs against a
  // valid baseline: full refresh seeds the current frame, partial seeds the
  // previous frame (persisted across deep sleep).
  seed_old_ram_(is_full_update_ ? buffer_ : previous_frame_);

  // Open primary RAM for writing
  spi_command_(CMD_WRITE_RAM | TGT_PRIMARY);
  spi_start_data_();
}

void CrowPanelEPaper5P79In::seed_old_ram_(const uint8_t *frame) {
  if (frame == nullptr)
    return;
  uint16_t rows = is_full_update_ ? HEIGHT_5P79 : PARTIAL_ROWS;

  // Primary OLD RAM - left half (bytes 0..HALF_CEIL-1)
  spi_command_(CMD_WRITE_RAM_OLD | TGT_PRIMARY);
  spi_start_data_();
  for (uint16_t row = 0; row < rows; row++) {
    size_t off = (size_t) row * ROW_BYTES;
    for (uint16_t x = 0; x < HALF_CEIL; x++)
      spi_write_byte_(frame[off + x]);
  }
  spi_end_data_();

  delay(1);

  // Secondary OLD RAM - right half (bytes HALF_FLOOR..HALF_FLOOR+HALF_CEIL-1)
  spi_command_(CMD_WRITE_RAM_OLD | TGT_SECONDARY);
  spi_start_data_();
  for (uint16_t row = 0; row < rows; row++) {
    size_t off = (size_t) row * ROW_BYTES;
    for (uint16_t x = 0; x < HALF_CEIL; x++)
      spi_write_byte_(frame[off + HALF_FLOOR + x]);
  }
  spi_end_data_();

  // Re-arm both cursors to their scan origins (the OLD-RAM writes advanced
  // the shared address counter of each chip).
  spi_command_(CMD_SET_X_CTR | TGT_PRIMARY);
  spi_data_(0x00);
  spi_command_(CMD_SET_Y_CTR | TGT_PRIMARY);
  spi_data_(0x00);
  spi_data_(0x00);
  spi_command_(CMD_SET_X_CTR | TGT_SECONDARY);
  spi_data_(0x31);
  spi_command_(CMD_SET_Y_CTR | TGT_SECONDARY);
  spi_data_(0x00);
  spi_data_(0x00);
}

void CrowPanelEPaper5P79In::send_data_() {
  uint16_t rows = is_full_update_ ? HEIGHT_5P79 : PARTIAL_ROWS;
  // Primary: left half (bytes 0..49 of each row)
  for (uint16_t row = 0; row < rows; row++) {
    size_t off = (size_t) row * ROW_BYTES;
    for (uint16_t x = 0; x < HALF_CEIL; x++)
      spi_write_byte_(buffer_[off + x]);
  }
  spi_end_data_();

  delay(1);

  // Secondary: right half (bytes 49..98 of each row)
  spi_command_(CMD_WRITE_RAM | TGT_SECONDARY);
  spi_start_data_();
  for (uint16_t row = 0; row < rows; row++) {
    size_t off = (size_t) row * ROW_BYTES;
    for (uint16_t x = 0; x < HALF_CEIL; x++)
      spi_write_byte_(buffer_[off + HALF_FLOOR + x]);
  }
  spi_end_data_();
}

}  // namespace crowpanel_epaper
}  // namespace esphome
