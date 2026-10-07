"""Platform for Pilot Wire."""

import logging
import math
from typing import override

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.select import (
    ATTR_OPTION,
    ATTR_OPTIONS,
    SERVICE_SELECT_OPTION,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import (
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
from homeassistant.util.unit_conversion import PowerConverter, TemperatureConverter

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
    OFF_OPTIONS,
    PRESET_COMFORT_1,
    PRESET_COMFORT_2,
    PRESET_OPTIONS,
)
from .util import option_preset

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: PilotWireConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Initialize config entry."""
    async_add_entities([PilotWireClimate(hass, config_entry)])


def _read_float(state: State | None, sensor: str) -> float | None:
    """Return the sensor's reading, or None while it has none."""
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        return None
    try:
        value = float(state.state)
    except ValueError:
        value = math.nan
    if not math.isfinite(value):
        _LOGGER.error("Unable to update from %s sensor: %s", sensor, state.state)
        return None
    return value


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

    def __init__(self, hass: HomeAssistant, config_entry: PilotWireConfigEntry) -> None:
        """Initialize the climate device."""
        options = config_entry.options
        self._select: str = options[CONF_SELECT]
        self._temperature_sensor: str | None = options.get(CONF_TEMPERATURE_SENSOR)
        self._humidity_sensor: str | None = options.get(CONF_HUMIDITY_SENSOR)
        self._power_sensor: str | None = options.get(CONF_POWER_SENSOR)
        self._additional_modes: bool = options.get(CONF_ADDITIONAL_MODES, True)
        self._power_threshold: float = options.get(CONF_POWER_THRESHOLD, 0)
        self._default_preset: str = options.get(
            CONF_DEFAULT_PRESET, DEFAULT_DEFAULT_PRESET
        )
        self._mode: str | None = None
        self._power: float | None = None
        self._last_preset: str | None = None

        self._attr_unique_id = config_entry.entry_id
        self.device_entry = async_entity_id_to_device(hass, self._select)
        # On a device, the thermostat is the device's main feature.
        self._attr_name = None if self.device_entry else config_entry.title

    @override
    async def async_added_to_hass(self) -> None:
        """Restore the last preset and follow the select and sensors."""
        await super().async_added_to_hass()

        if (data := await self.async_get_last_extra_data()) is not None:
            last_preset = data.as_dict().get("last_preset")
            if last_preset in PRESET_OPTIONS:
                self._last_preset = last_preset

        sources = [
            entity_id
            for entity_id in (
                self._select,
                self._temperature_sensor,
                self._humidity_sensor,
                self._power_sensor,
            )
            if entity_id is not None
        ]
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, sources, self._async_source_changed
            )
        )
        # A source that is not loaded yet is read from its first state change.
        for entity_id in sources:
            self._async_read(entity_id, self.hass.states.get(entity_id))

    @callback
    def _async_source_changed(self, event: Event[EventStateChangedData]) -> None:
        self._async_read(event.data["entity_id"], event.data["new_state"])
        self.async_write_ha_state()

    @callback
    def _async_read(self, entity_id: str, state: State | None) -> None:
        if entity_id == self._select:
            self._async_read_mode(state)
        if entity_id == self._temperature_sensor:
            self._async_read_temperature(state)
        if entity_id == self._humidity_sensor:
            self._attr_current_humidity = _read_float(state, "humidity")
        if entity_id == self._power_sensor:
            self._async_read_power(state)

    @callback
    def _async_read_mode(self, state: State | None) -> None:
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._mode = None
            return
        self._mode = state.state
        if self._mode in OFF_OPTIONS:
            return
        if (preset := option_preset(self._mode)) is None:
            _LOGGER.warning(
                "%s reports unknown pilot wire mode %s, shown with no preset",
                self._select,
                self._mode,
            )
        else:
            self._last_preset = preset

    @callback
    def _async_read_temperature(self, state: State | None) -> None:
        self._attr_current_temperature = _read_float(state, "temperature")
        if state is None or self._attr_current_temperature is None:
            return
        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if unit == UnitOfTemperature.KELVIN:
            # A climate entity's temperature unit can only be °C or °F.
            self._attr_current_temperature = TemperatureConverter.convert(
                self._attr_current_temperature,
                UnitOfTemperature.KELVIN,
                UnitOfTemperature.CELSIUS,
            )
            unit = UnitOfTemperature.CELSIUS
        if unit in (UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT):
            self._attr_temperature_unit = unit

    @callback
    def _async_read_power(self, state: State | None) -> None:
        self._power = _read_float(state, "power")
        if state is None or self._power is None:
            return
        # The threshold is set in watts.
        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if unit in PowerConverter.VALID_UNITS:
            self._power = PowerConverter.convert(self._power, unit, UnitOfPower.WATT)

    def _options(self) -> list[str]:
        state = self.hass.states.get(self._select)
        return state.attributes.get(ATTR_OPTIONS, []) if state else []

    def _get_option(self, names: tuple[str, ...]) -> str:
        """Return the select option going by one of these names."""
        for option in self._options():
            if option in names:
                return option
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="missing_option",
            translation_placeholders={"entity_id": self._select, "value": names[0]},
        )

    @override
    @property
    def available(self) -> bool:
        """Return whether the select driving the heater is available."""
        state = self.hass.states.get(self._select)
        return state is not None and state.state != STATE_UNAVAILABLE

    @override
    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation."""
        if self._power is not None and self._power > self._power_threshold:
            return HVACAction.HEATING
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        if self._power is not None:
            return HVACAction.IDLE
        return None

    @override
    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, off mode."""
        if self._mode is None:
            return None
        if self._mode in OFF_OPTIONS:
            return HVACMode.OFF
        return HVACMode.HEAT

    @override
    @property
    def preset_modes(self) -> list[str]:
        """List the presets that the select has an option for."""
        options = self._options()
        return [
            preset
            for preset, names in PRESET_OPTIONS.items()
            if (
                self._additional_modes
                or preset not in (PRESET_COMFORT_1, PRESET_COMFORT_2)
            )
            and any(option in names for option in options)
        ]

    @override
    @property
    def preset_mode(self) -> str | None:
        """Preset current mode."""
        if self._mode is None:
            return None
        preset = option_preset(self._mode)
        return preset if preset in self.preset_modes else None

    @override
    @property
    def extra_restore_state_data(self) -> ExtraStoredData:
        """Keep the preset to turn back on with across restarts."""
        return RestoredExtraData({"last_preset": self._last_preset})

    @override
    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        if preset_mode == self.preset_mode:
            # Every select_option is a radio command to the module.
            return
        await self._async_select_option(self._get_option(PRESET_OPTIONS[preset_mode]))

    @override
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == self.hvac_mode:
            # Otherwise turning on a heating thermostat would reset its preset.
            return
        if hvac_mode == HVACMode.OFF:
            names = OFF_OPTIONS
        elif self._last_preset in self.preset_modes:
            names = PRESET_OPTIONS[self._last_preset]
        else:
            names = PRESET_OPTIONS[self._default_preset]
        await self._async_select_option(self._get_option(names))

    async def _async_select_option(self, option: str) -> None:
        await self.hass.services.async_call(
            split_entity_id(self._select)[0],
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: self._select, ATTR_OPTION: option},
            blocking=True,
            context=self._context,
        )
