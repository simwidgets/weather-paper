import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import CONF_ID

from esphome.components.esp32 import include_builtin_idf_component, require_fatfs

DEPENDENCIES = []

sd_wifi_reader_ns = cg.esphome_ns.namespace('sd_wifi_reader')
SDWiFiReader = sd_wifi_reader_ns.class_('SDWiFiReader', cg.Component)

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(SDWiFiReader),
}).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    # FATFS + SDMMC/SDSPI are excluded from the ESP-IDF build by default; re-enable them.
    include_builtin_idf_component("fatfs")
    require_fatfs()

    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
