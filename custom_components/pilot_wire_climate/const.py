"""Constants for the pilot wire climate integration."""

from homeassistant.components.climate import PRESET_AWAY, PRESET_COMFORT, PRESET_ECO

DOMAIN = "pilot_wire_climate"
CONF_SELECT = "select"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_POWER_SENSOR = "power_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_ADDITIONAL_MODES = "additional_modes"
CONF_POWER_THRESHOLD = "power_threshold"
PRESET_COMFORT_1 = "comfort_1"
PRESET_COMFORT_2 = "comfort_2"
ADDITIONAL_PRESETS = (PRESET_COMFORT_1, PRESET_COMFORT_2)
CONF_DEFAULT_PRESET = "default_preset"
DEFAULT_DEFAULT_PRESET = PRESET_COMFORT

# The select options standing for each preset, as different modules name them
PRESET_OPTIONS = {
    PRESET_COMFORT: ("comfort", "Comfort"),
    PRESET_COMFORT_1: ("comfort_-1", "ComfortMinus1"),
    PRESET_COMFORT_2: ("comfort_-2", "ComfortMinus2"),
    PRESET_ECO: ("eco", "Eco"),
    PRESET_AWAY: ("frost_protection", "FrostProtection"),
}
OFF_OPTIONS = ("off", "Off")
