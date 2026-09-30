"""Platform for Pilot Wire."""

import logging
import math

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import \
    PLATFORM_SCHEMA as CLIMATE_PLATFORM_SCHEMA
from homeassistant.components.climate import (PRESET_AWAY, PRESET_COMFORT,
                                              PRESET_ECO, PRESET_NONE,
                                              ClimateEntity,
                                              ClimateEntityFeature, HVACAction,
                                              HVACMode)
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.select import ATTR_OPTIONS, SERVICE_SELECT_OPTION
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (ATTR_ENTITY_ID, CONF_NAME, CONF_UNIQUE_ID,
                                 EVENT_HOMEASSISTANT_START, STATE_UNAVAILABLE,
                                 STATE_UNKNOWN, UnitOfTemperature)
from homeassistant.core import (CoreState, Event, EventStateChangedData,
                                HomeAssistant, State, callback)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device import async_entity_id_to_device
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN, PLATFORMS
from .util import get_value_key
from .const import (CONF_ADDITIONAL_MODES,
                    CONF_POWER,
                    CONF_POWER_THRESHOLD,
                    CONF_PRESET,
                    CONF_TEMP,
                    DEFAULT_NAME,
                    PRESET_COMFORT_1,
                    PRESET_COMFORT_2,
                    CONF_DEFAULT_PRESET,
                    DEFAULT_DEFAULT_PRESET, VALUE_COMFORT, VALUE_COMFORT_1, VALUE_COMFORT_2, VALUE_ECO, VALUE_FROST, VALUE_OFF, VALUES_MAPPING)

_LOGGER = logging.getLogger(__name__)

VALUE_TO_PRESET = {
    VALUE_OFF: PRESET_NONE,
    VALUE_FROST: PRESET_AWAY,
    VALUE_ECO: PRESET_ECO,
    VALUE_COMFORT: PRESET_COMFORT,
    VALUE_COMFORT_1: PRESET_COMFORT_1,
    VALUE_COMFORT_2: PRESET_COMFORT_2,
}
PRESET_TO_VALUE = {preset: value for value, preset in VALUE_TO_PRESET.items()}


PLATFORM_SCHEMA_COMMON = vol.Schema(
    {
        vol.Required(CONF_PRESET): cv.entity_id,
        vol.Optional(CONF_TEMP): cv.entity_id,
        vol.Optional(CONF_POWER): cv.entity_id,
        vol.Optional(CONF_ADDITIONAL_MODES, default=True): cv.boolean,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_POWER_THRESHOLD): cv.positive_float,
        vol.Optional(CONF_DEFAULT_PRESET, default=DEFAULT_DEFAULT_PRESET): vol.In([VALUE_COMFORT, VALUE_COMFORT_1, VALUE_COMFORT_2, VALUE_ECO, VALUE_FROST]),
    }
)

PLATFORM_SCHEMA = CLIMATE_PLATFORM_SCHEMA.extend(PLATFORM_SCHEMA_COMMON.schema)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize config entry."""
    await _async_setup_config(
        hass,
        PLATFORM_SCHEMA_COMMON(dict(config_entry.options)),
        config_entry.entry_id,
        async_add_entities,
    )


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the generic thermostat platform."""

    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)
    await _async_setup_config(
        hass, config, config.get(CONF_UNIQUE_ID), async_add_entities
    )


async def _async_setup_config(
    hass: HomeAssistant,
    config: ConfigType,
    unique_id: str | None,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the pilot wire climate platform."""
    name: str | None = config.get(CONF_NAME)
    preset_entity_id: str = config.get(CONF_PRESET)
    temp_entity_id: str | None = config.get(CONF_TEMP)
    power_entity_id: str | None = config.get(CONF_POWER)
    additional_modes: bool = config.get(CONF_ADDITIONAL_MODES)
    power_threshold: float = config.get(CONF_POWER_THRESHOLD)
    default_preset: str | None = config.get(CONF_DEFAULT_PRESET)

    async_add_entities(
        [
            PilotWireClimate(
                hass,
                name,
                preset_entity_id,
                temp_entity_id,
                power_entity_id,
                additional_modes,
                power_threshold,
                default_preset,
                unique_id,
            )
        ]
    )


class PilotWireClimate(ClimateEntity, RestoreEntity):
    """Representation of a Pilot Wire device."""

    _attr_should_poll = False
    _attr_translation_key: str = "pilot_wire"
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        hass: HomeAssistant,
        name: str | None,
        preset_entity_id: str,
        temp_entity_id: str | None,
        power_entity_id: str | None,
        additional_modes: bool,
        power_threshold: float,
        default_preset: str,
        unique_id: str | None,
    ) -> None:
        """Initialize the climate device."""

        registry = er.async_get(hass)
        preset_entity = registry.async_get(preset_entity_id)
        has_entity_name = preset_entity.has_entity_name if preset_entity else False

        self.device_entry = async_entity_id_to_device(hass, preset_entity_id)

        if name:
            self._attr_name = name
        else:
            self._attr_name = DEFAULT_NAME

        self.preset_entity_id = preset_entity_id
        self.temp_entity_id = temp_entity_id
        self.power_entity_id = power_entity_id
        self.additional_modes = additional_modes
        self._power_threshold = power_threshold
        self._cur_temperature = None
        self._cur_power = None
        self._cur_mode = None
        self._default_preset = default_preset

        self._attr_has_entity_name = has_entity_name
        self._attr_unique_id = (
            unique_id if unique_id else "pilot_wire_" + preset_entity_id
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Add listener
        if self.temp_entity_id is not None:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [
                        self.temp_entity_id], self._async_temp_changed
                )
            )

        if self.power_entity_id is not None:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [
                        self.power_entity_id], self._async_power_changed
                )
            )

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.preset_entity_id], self._async_mode_changed
            )
        )

        @callback
        def _async_startup(_: Event | None = None) -> None:
            """Init on startup."""
            mode_state = self.hass.states.get(self.preset_entity_id)
            if mode_state and mode_state.state not in (
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
            ):
                self._async_update_mode(mode_state)
                self.async_write_ha_state()

            if self.temp_entity_id is not None:
                temp_state = self.hass.states.get(self.temp_entity_id)
                if temp_state and temp_state.state not in (
                    STATE_UNAVAILABLE,
                    STATE_UNKNOWN,
                ):
                    self._async_update_temp(temp_state)
                    self.async_write_ha_state()

            if self.power_entity_id is not None:
                power_state = self.hass.states.get(self.power_entity_id)
                if power_state and power_state.state not in (
                    STATE_UNAVAILABLE,
                    STATE_UNKNOWN,
                ):
                    self._async_update_power(power_state)
                    self.async_write_ha_state()

        if self.hass.state is CoreState.running:
            _async_startup()
        else:
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_START, _async_startup)

    def _get_option(self, value: str) -> str:
        """Return the select option standing for a pilot wire value."""
        state = self.hass.states.get(self.preset_entity_id)
        options = state.attributes.get(ATTR_OPTIONS) if state else None
        for option in options or ():
            if get_value_key(option) == value:
                return option
        raise HomeAssistantError(
            f"{self.preset_entity_id} has no option for {value}")

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return (
            ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )

    def update(self) -> None:
        """Update unit attributes."""

    @property
    def hvac_action(self) -> str:
        """Return the unit of measurement."""
        value = None
        if self._cur_power is not None:
            if self._cur_power > self.power_threshold:
                value = HVACAction.HEATING
            elif self.preset_mode == PRESET_NONE:
                value = HVACAction.OFF
            else:
                value = HVACAction.IDLE
        return value

    @property
    def power_threshold(self) -> str:
        """Return the unit of measurement."""
        return 0 if self._power_threshold is None else self._power_threshold

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float | None:
        """Return the sensor temperature."""
        return self._cur_temperature

    # Presets

    @property
    def preset_modes(self) -> list[str] | None:
        """List of available preset modes."""
        if self.additional_modes:
            return [
                PRESET_COMFORT,
                PRESET_COMFORT_1,
                PRESET_COMFORT_2,
                PRESET_ECO,
                PRESET_AWAY,
                PRESET_NONE,
            ]
        return [PRESET_COMFORT, PRESET_ECO, PRESET_AWAY, PRESET_NONE]

    @property
    def preset_mode(self) -> str | None:
        """Preset current mode."""
        if self._cur_mode is None:
            return None
        preset = VALUE_TO_PRESET.get(get_value_key(self._cur_mode))
        if preset is None or preset not in self.preset_modes:
            return PRESET_COMFORT
        return preset

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        await self._async_set_mode_value(
            self._get_option(PRESET_TO_VALUE[preset_mode]))
    # Modes

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """List of available operation modes."""
        return [HVACMode.HEAT, HVACMode.OFF]

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        value = self._default_preset if hvac_mode == HVACMode.HEAT else VALUE_OFF
        await self._async_set_mode_value(self._get_option(value))

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, off mode."""
        if self.preset_mode is not None:
            return HVACMode.OFF if self.preset_mode == PRESET_NONE else HVACMode.HEAT
        return None

    async def _async_temp_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle temperature changes."""
        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        self._async_update_temp(new_state)
        self.async_write_ha_state()

    async def _async_power_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle temperature changes."""
        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        self._async_update_power(new_state)
        self.async_write_ha_state()

    @callback
    def _async_mode_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle preset switch state changes."""

        new_state = event.data["new_state"]
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        self._async_update_mode(new_state)
        self.async_write_ha_state()

    @callback
    def _async_update_mode(self, state: State):
        try:
            cur_mode = str(state.state)
            self._cur_mode = cur_mode
        except ValueError as ex:
            _LOGGER.error("Unable to update from mode sensor: %s", ex)

    @callback
    def _async_update_temp(self, state: State):
        try:
            cur_temp = float(state.state)
            if not math.isfinite(cur_temp):
                raise ValueError(f"Sensor has illegal state {state.state}")
            self._cur_temperature = cur_temp
        except ValueError as ex:
            _LOGGER.error("Unable to update from temperature sensor: %s", ex)

    @callback
    def _async_update_power(self, state: State):
        try:
            cur_power = float(state.state)
            if not math.isfinite(cur_power):
                raise ValueError(f"Sensor has illegal state {state.state}")
            self._cur_power = cur_power
        except ValueError as ex:
            _LOGGER.error("Unable to update from temperature sensor: %s", ex)

    async def _async_set_mode_value(self, value):
        data = {
            ATTR_ENTITY_ID: self.preset_entity_id,
            "option": value,
        }
        await self.hass.services.async_call(SELECT_DOMAIN, SERVICE_SELECT_OPTION, data)
