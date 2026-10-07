"""Config flow for Pilot Wire thermostat."""

from collections.abc import Mapping
from typing import Any, override

from homeassistant.components.input_select import DOMAIN as INPUT_SELECT_DOMAIN
from homeassistant.components.select import ATTR_OPTIONS, DOMAIN as SELECT_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN, SensorDeviceClass
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
)
from homeassistant.helpers.typing import VolDictType
import probatio

from .const import (
    CONF_ADDITIONAL_MODES,
    CONF_DEFAULT_PRESET,
    CONF_HUMIDITY_SENSOR,
    CONF_POWER_SENSOR,
    CONF_POWER_THRESHOLD,
    CONF_SELECT,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_DEFAULT_PRESET,
    DOMAIN,
    PRESET_COMFORT_1,
    PRESET_COMFORT_2,
    PRESET_TO_VALUE,
)
from .util import async_hide_select, config_entry_title, get_value_key

OPTIONS_SCHEMA: VolDictType = {
    probatio.Required(CONF_SELECT): selector.EntitySelector(
        selector.EntitySelectorConfig(domain=[SELECT_DOMAIN, INPUT_SELECT_DOMAIN])
    ),
    probatio.Optional(CONF_TEMPERATURE_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.TEMPERATURE
        )
    ),
    probatio.Optional(CONF_HUMIDITY_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.HUMIDITY
        )
    ),
    probatio.Optional(CONF_POWER_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.POWER
        )
    ),
    probatio.Optional(CONF_ADDITIONAL_MODES, default=True): selector.BooleanSelector(),
    probatio.Optional(CONF_POWER_THRESHOLD, default=0): selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0, step=1, unit_of_measurement="W", mode=selector.NumberSelectorMode.BOX
        )
    ),
    probatio.Optional(
        CONF_DEFAULT_PRESET, default=DEFAULT_DEFAULT_PRESET
    ): selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=list(PRESET_TO_VALUE),
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key=CONF_DEFAULT_PRESET,
        )
    ),
}


async def validate_options(
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Reject options the thermostat could not act on."""
    default_preset = user_input[CONF_DEFAULT_PRESET]
    if not user_input[CONF_ADDITIONAL_MODES] and default_preset in (
        PRESET_COMFORT_1,
        PRESET_COMFORT_2,
    ):
        raise SchemaFlowError("default_preset_not_offered")

    state = handler.parent_handler.hass.states.get(user_input[CONF_SELECT])
    options = state.attributes.get(ATTR_OPTIONS, []) if state else []
    if PRESET_TO_VALUE[default_preset] not in {get_value_key(o) for o in options}:
        raise SchemaFlowError("default_preset_missing")
    return user_input


CONFIG_FLOW = {
    "user": SchemaFlowFormStep(
        probatio.Schema(OPTIONS_SCHEMA), validate_user_input=validate_options
    ),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(
        probatio.Schema(OPTIONS_SCHEMA), validate_user_input=validate_options
    ),
}


class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow."""

    VERSION = 1
    MINOR_VERSION = 6

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW
    options_flow_reloads = True

    @override
    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title and hide the select."""
        async_hide_select(self.hass, options[CONF_SELECT])
        return config_entry_title(self.hass, options[CONF_SELECT])
