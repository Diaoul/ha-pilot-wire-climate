"""Platform for Pilot Wire."""

import logging
import math
from typing import Any, override

from homeassistant.components.climate import (
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.select import ATTR_OPTIONS, SERVICE_SELECT_OPTION
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_UNIT_OF_MEASUREMENT,
    EVENT_HOMEASSISTANT_START,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import (
    CoreState,
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
    split_entity_id,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device import async_entity_id_to_device
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import (
    ExtraStoredData,
    RestoredExtraData,
    RestoreEntity,
)
from homeassistant.util.unit_conversion import PowerConverter

from . import PilotWireConfigEntry
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
    VALUE_OFF,
    VALUE_TO_PRESET,
)
from .util import get_value_key

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: PilotWireConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Initialize config entry."""
    options = config_entry.options
    async_add_entities(
        [
            PilotWireClimate(
                hass,
                config_entry.title,
                options[CONF_SELECT],
                options.get(CONF_TEMPERATURE_SENSOR),
                options.get(CONF_HUMIDITY_SENSOR),
                options.get(CONF_POWER_SENSOR),
                options.get(CONF_ADDITIONAL_MODES, True),
                options.get(CONF_POWER_THRESHOLD, 0),
                options.get(CONF_DEFAULT_PRESET, DEFAULT_DEFAULT_PRESET),
                config_entry.entry_id,
            )
        ]
    )


def _finite_float(value: str) -> float | None:
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _value(state: State) -> str | None:
    """Return the state, or None while the entity is unavailable or unknown."""
    if state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        return None
    return state.state


class PilotWireClimate(ClimateEntity, RestoreEntity):
    """Representation of a Pilot Wire device."""

    _attr_has_entity_name = True
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_should_poll = False
    _attr_supported_features = (
        ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_translation_key: str = "pilot_wire"

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        preset_entity_id: str,
        temp_entity_id: str | None,
        humidity_entity_id: str | None,
        power_entity_id: str | None,
        additional_modes: bool,
        power_threshold: float,
        default_preset: str,
        unique_id: str,
    ) -> None:
        """Initialize the climate device."""

        self.device_entry = async_entity_id_to_device(hass, preset_entity_id)
        # On a device, the thermostat is the device's main feature.
        self._attr_name = None if self.device_entry else name

        self.preset_entity_id = preset_entity_id
        self.temp_entity_id = temp_entity_id
        self.humidity_entity_id = humidity_entity_id
        self.power_entity_id = power_entity_id
        self.additional_modes = additional_modes
        self._power_threshold = power_threshold
        self._cur_temperature: float | None = None
        self._cur_humidity: float | None = None
        self._cur_power: float | None = None
        self._cur_mode: str | None = None
        self._default_preset = default_preset
        self._last_preset: str | None = None

        self._attr_unique_id = unique_id

    @override
    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        if (data := await self.async_get_last_extra_data()) is not None:
            last_preset = data.as_dict().get("last_preset")
            if last_preset in PRESET_TO_VALUE:
                self._last_preset = last_preset

        # Add listener
        if self.temp_entity_id is not None:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self.temp_entity_id], self._async_temp_changed
                )
            )

        if self.humidity_entity_id is not None:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self.humidity_entity_id], self._async_humidity_changed
                )
            )

        if self.power_entity_id is not None:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self.power_entity_id], self._async_power_changed
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
            self._async_update_mode(self.hass.states.get(self.preset_entity_id))
            if self.temp_entity_id is not None:
                self._async_update_temp(self.hass.states.get(self.temp_entity_id))
            if self.humidity_entity_id is not None:
                self._async_update_humidity(
                    self.hass.states.get(self.humidity_entity_id)
                )
            if self.power_entity_id is not None:
                self._async_update_power(self.hass.states.get(self.power_entity_id))
            self.async_write_ha_state()

        if self.hass.state is CoreState.running:
            _async_startup()
        else:
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _async_startup)

    def _options(self) -> list[str]:
        state = self.hass.states.get(self.preset_entity_id)
        return state.attributes.get(ATTR_OPTIONS, []) if state else []

    def _get_option(self, value: str) -> str:
        """Return the select option standing for a pilot wire value."""
        for option in self._options():
            if get_value_key(option) == value:
                return option
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="missing_option",
            translation_placeholders={
                "entity_id": self.preset_entity_id,
                "value": value,
            },
        )

    @override
    @property
    def available(self) -> bool:
        """Return whether the select driving the heater is available."""
        state = self.hass.states.get(self.preset_entity_id)
        return state is not None and state.state != STATE_UNAVAILABLE

    @override
    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation."""
        if self._cur_power is not None and self._cur_power > self.power_threshold:
            return HVACAction.HEATING
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        if self._cur_power is not None:
            return HVACAction.IDLE
        return None

    @property
    def power_threshold(self) -> float:
        """Return the power above which the heater counts as heating."""
        return self._power_threshold

    @override
    @property
    def current_temperature(self) -> float | None:
        """Return the sensor temperature."""
        return self._cur_temperature

    @override
    @property
    def current_humidity(self) -> float | None:
        """Return the sensor humidity."""
        return self._cur_humidity

    # Presets

    @override
    @property
    def preset_modes(self) -> list[str]:
        """List the presets that the select has an option for."""
        presets = [PRESET_COMFORT, PRESET_ECO, PRESET_AWAY]
        if self.additional_modes:
            presets[1:1] = [PRESET_COMFORT_1, PRESET_COMFORT_2]
        values = {get_value_key(option) for option in self._options()}
        return [preset for preset in presets if PRESET_TO_VALUE[preset] in values]

    @override
    @property
    def preset_mode(self) -> str | None:
        """Preset current mode."""
        if self._cur_mode is None:
            return None
        value = get_value_key(self._cur_mode)
        if value is None or value == VALUE_OFF:
            return None
        preset = VALUE_TO_PRESET[value]
        return preset if preset in self.preset_modes else None

    @override
    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        if preset_mode == self.preset_mode:
            # Every select_option is a radio command to the module.
            return
        await self._async_set_mode_value(self._get_option(PRESET_TO_VALUE[preset_mode]))

    # Modes

    @override
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == self.hvac_mode:
            # Otherwise turning on a heating thermostat would reset its preset.
            return
        if hvac_mode == HVACMode.OFF:
            value = VALUE_OFF
        elif self._last_preset in self.preset_modes:
            value = PRESET_TO_VALUE[self._last_preset]
        else:
            value = PRESET_TO_VALUE[self._default_preset]
        await self._async_set_mode_value(self._get_option(value))

    @override
    @property
    def extra_restore_state_data(self) -> ExtraStoredData:
        """Keep the preset to turn back on with across restarts."""
        return RestoredExtraData({"last_preset": self._last_preset})

    @override
    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, off mode."""
        if self._cur_mode is None:
            return None
        if get_value_key(self._cur_mode) == VALUE_OFF:
            return HVACMode.OFF
        return HVACMode.HEAT

    @callback
    def _async_temp_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle temperature changes."""
        self._async_update_temp(event.data["new_state"])
        self.async_write_ha_state()

    @callback
    def _async_humidity_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle humidity changes."""
        self._async_update_humidity(event.data["new_state"])
        self.async_write_ha_state()

    @callback
    def _async_power_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle power changes."""
        self._async_update_power(event.data["new_state"])
        self.async_write_ha_state()

    @callback
    def _async_mode_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle preset switch state changes."""
        self._async_update_mode(event.data["new_state"])
        self.async_write_ha_state()

    @callback
    def _async_update_mode(self, state: State | None) -> None:
        self._cur_mode = None if state is None else _value(state)
        if self._cur_mode is None:
            return
        if (value := get_value_key(self._cur_mode)) is None:
            _LOGGER.warning(
                "%s reports unknown pilot wire mode %s, shown with no preset",
                self.preset_entity_id,
                self._cur_mode,
            )
        elif value != VALUE_OFF:
            self._last_preset = VALUE_TO_PRESET[value]

    @callback
    def _async_update_temp(self, state: State | None) -> None:
        if state is None or (raw := _value(state)) is None:
            self._cur_temperature = None
            return
        if (value := _finite_float(raw)) is None:
            _LOGGER.error("Unable to update from temperature sensor: %s", raw)
            self._cur_temperature = None
            return
        self._cur_temperature = value
        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if unit in (UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT):
            self._attr_temperature_unit = unit

    @callback
    def _async_update_humidity(self, state: State | None) -> None:
        if state is None or (raw := _value(state)) is None:
            self._cur_humidity = None
            return
        if (value := _finite_float(raw)) is None:
            _LOGGER.error("Unable to update from humidity sensor: %s", raw)
            self._cur_humidity = None
            return
        self._cur_humidity = value

    @callback
    def _async_update_power(self, state: State | None) -> None:
        if state is None or (raw := _value(state)) is None:
            self._cur_power = None
            return
        if (value := _finite_float(raw)) is None:
            _LOGGER.error("Unable to update from power sensor: %s", raw)
            self._cur_power = None
            return
        # The threshold is set in watts.
        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if unit in PowerConverter.VALID_UNITS:
            value = PowerConverter.convert(value, unit, UnitOfPower.WATT)
        self._cur_power = value

    async def _async_set_mode_value(self, value: str) -> None:
        data: dict[str, Any] = {
            ATTR_ENTITY_ID: self.preset_entity_id,
            "option": value,
        }
        await self.hass.services.async_call(
            split_entity_id(self.preset_entity_id)[0],
            SERVICE_SELECT_OPTION,
            data,
            blocking=True,
            context=self._context,
        )
