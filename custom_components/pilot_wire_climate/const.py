"""Constants for the pilot wire climate integration."""

from homeassistant.components.climate import PRESET_AWAY, PRESET_COMFORT, PRESET_ECO

DOMAIN = "pilot_wire_climate"
CONF_SELECT = "select"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_POWER_SENSOR = "power_sensor"
OLD_OPTION_KEYS = {
    "presets": CONF_SELECT,
    "temperature": CONF_TEMPERATURE_SENSOR,
    "power": CONF_POWER_SENSOR,
}
CONF_ADDITIONAL_MODES = "additional_modes"
CONF_POWER_THRESHOLD = "power_threshold"
PRESET_COMFORT_1 = "comfort_1"
PRESET_COMFORT_2 = "comfort_2"
CONF_DEFAULT_PRESET = "default_preset"

VALUE_OFF = "off"
VALUE_FROST = "frost_protection"
VALUE_ECO = "eco"
VALUE_COMFORT_2 = "comfort-2"
VALUE_COMFORT_1 = "comfort-1"
VALUE_COMFORT = "comfort"
DEFAULT_DEFAULT_PRESET = PRESET_COMFORT

VALUE_TO_PRESET = {
    VALUE_FROST: PRESET_AWAY,
    VALUE_ECO: PRESET_ECO,
    VALUE_COMFORT: PRESET_COMFORT,
    VALUE_COMFORT_1: PRESET_COMFORT_1,
    VALUE_COMFORT_2: PRESET_COMFORT_2,
}
PRESET_TO_VALUE = {preset: value for value, preset in VALUE_TO_PRESET.items()}

VALUES_MAPPING = {
    VALUE_OFF: ["off", "Off"],
    VALUE_FROST: ["frost_protection", "FrostProtection"],
    VALUE_ECO: ["eco", "Eco"],
    VALUE_COMFORT: ["comfort", "Comfort"],
    VALUE_COMFORT_2: ["comfort_-2", "ComfortMinus2"],
    VALUE_COMFORT_1: ["comfort_-1", "ComfortMinus1"],
}
