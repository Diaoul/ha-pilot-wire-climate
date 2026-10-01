"""Config flow for Pilot Wire thermostat."""

from collections.abc import Mapping
from typing import Any, override

from homeassistant.components.input_select import DOMAIN as INPUT_SELECT_DOMAIN
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN, SensorDeviceClass
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)
from homeassistant.helpers.typing import VolDictType
import voluptuous as vol

from .const import (
    CONF_ADDITIONAL_MODES,
    CONF_DEFAULT_PRESET,
    CONF_POWER,
    CONF_POWER_THRESHOLD,
    CONF_PRESET,
    CONF_TEMP,
    DEFAULT_DEFAULT_PRESET,
    DOMAIN,
    PRESET_TO_VALUE,
)
from .util import async_hide_select, config_entry_title

OPTIONS_SCHEMA: VolDictType = {
    vol.Required(CONF_PRESET): selector.EntitySelector(
        selector.EntitySelectorConfig(domain=[SELECT_DOMAIN, INPUT_SELECT_DOMAIN])
    ),
    vol.Optional(CONF_TEMP): selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.TEMPERATURE
        )
    ),
    vol.Optional(CONF_POWER): selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.POWER
        )
    ),
    vol.Optional(CONF_ADDITIONAL_MODES, default=True): selector.BooleanSelector(),
    vol.Optional(CONF_POWER_THRESHOLD, default=0): selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0, step=1, unit_of_measurement="W", mode=selector.NumberSelectorMode.BOX
        )
    ),
    vol.Optional(
        CONF_DEFAULT_PRESET, default=DEFAULT_DEFAULT_PRESET
    ): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=list(PRESET_TO_VALUE),
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key=CONF_DEFAULT_PRESET,
        )
    ),
}

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(vol.Schema(OPTIONS_SCHEMA)),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(vol.Schema(OPTIONS_SCHEMA)),
}


class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow."""

    VERSION = 1
    MINOR_VERSION = 5

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW
    options_flow_reloads = True

    @override
    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title and hide the select."""
        async_hide_select(self.hass, options[CONF_PRESET])
        return config_entry_title(self.hass, options[CONF_PRESET])
