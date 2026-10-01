"""Pilot wire component."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device import async_entity_id_to_device_id
from homeassistant.helpers.event import async_track_entity_registry_updated_event
from homeassistant.helpers.helper_integration import (
    async_handle_source_entity_changes,
    async_remove_helper_devices,
)
from homeassistant.helpers.schema_config_entry_flow import (
    wrapped_entity_config_entry_title,
)

from .const import (
    CONF_DEFAULT_PRESET,
    CONF_POWER_SENSOR,
    CONF_SELECT,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_DEFAULT_PRESET,
    OLD_OPTION_KEYS,
    VALUE_TO_PRESET,
)
from .util import async_hide_select, async_unhide_select, config_entry_title

PLATFORMS = [Platform.CLIMATE]
_LOGGER = logging.getLogger(__name__)

# runtime_data is the select the entry was set up with
type PilotWireConfigEntry = ConfigEntry[str]


async def async_setup_entry(hass: HomeAssistant, entry: PilotWireConfigEntry) -> bool:
    """Set up from a config entry."""
    entry.runtime_data = entry.options[CONF_SELECT]

    def set_option(key: str, entity_id: str) -> None:
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, key: entity_id}
        )
        hass.config_entries.async_schedule_reload(entry.entry_id)

    entry.async_on_unload(
        async_handle_source_entity_changes(
            hass,
            helper_config_entry_id=entry.entry_id,
            set_source_entity_id_or_uuid=lambda entity_id: set_option(
                CONF_SELECT, entity_id
            ),
            source_device_id=async_entity_id_to_device_id(
                hass, entry.options[CONF_SELECT]
            ),
            source_entity_id_or_uuid=entry.options[CONF_SELECT],
        )
    )

    for key in (CONF_TEMPERATURE_SENSOR, CONF_POWER_SENSOR):
        if not (sensor_entity_id := entry.options.get(key)):
            continue

        async def async_sensor_updated(
            event: Event[er.EventEntityRegistryUpdatedData], key: str = key
        ) -> None:
            if (
                event.data["action"] == "update"
                and "entity_id" in event.data["changes"]
            ):
                set_option(key, event.data["entity_id"])

        entry.async_on_unload(
            async_track_entity_registry_updated_event(
                hass, sensor_entity_id, async_sensor_updated
            )
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PilotWireConfigEntry) -> bool:
    """Unload a config entry."""
    previous, current = entry.runtime_data, entry.options[CONF_SELECT]
    # The options flow saves a new select and then reloads: this is the only
    # point that sees both the old select and the new one.
    if previous != current:
        if async_unhide_select(hass, previous):
            async_hide_select(hass, current)
        if entry.title == config_entry_title(hass, previous):
            hass.config_entries.async_update_entry(
                entry, title=config_entry_title(hass, current)
            )
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Unhide the select entity that the config flow hid."""
    async_unhide_select(hass, entry.options[CONF_SELECT])


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    if config_entry.version > 1:
        return False

    options = {**config_entry.options}
    if config_entry.minor_version < 6:
        for old, new in OLD_OPTION_KEYS.items():
            if old in options:
                options[new] = options.pop(old)
    if config_entry.minor_version < 5:
        # Stored as a preset before minor version 2, then as a select value.
        default_preset = options.get(CONF_DEFAULT_PRESET, DEFAULT_DEFAULT_PRESET)
        options[CONF_DEFAULT_PRESET] = VALUE_TO_PRESET.get(
            default_preset, default_preset
        )

    if config_entry.minor_version < 3:
        # Earlier versions put the source device's identifiers in the climate
        # entity's device_info, which leaves a duplicate of that device owned by
        # this config entry.
        async_remove_helper_devices(
            hass,
            helper_config_entry_id=config_entry.entry_id,
            source_device_id=async_entity_id_to_device_id(hass, options[CONF_SELECT]),
            remove_all_devices=True,
        )

    title = config_entry.title
    if config_entry.minor_version < 4 and title == wrapped_entity_config_entry_title(
        hass, options[CONF_SELECT]
    ):
        title = config_entry_title(hass, options[CONF_SELECT])

    hass.config_entries.async_update_entry(
        config_entry, title=title, options=options, minor_version=6
    )
    return True
