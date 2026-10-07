"""Helpers for the pilot wire climate integration."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device import async_entity_id_to_device
from homeassistant.helpers.schema_config_entry_flow import (
    wrapped_entity_config_entry_title,
)

from .const import OFF_OPTIONS, PRESET_OPTIONS


def option_preset(option: str) -> str | None:
    """Return the preset a select option stands for."""
    for preset, names in PRESET_OPTIONS.items():
        if option in names:
            return preset
    return None


def is_pilot_wire_option(option: str) -> bool:
    """Return whether a select option is a pilot wire mode."""
    return option in OFF_OPTIONS or option_preset(option) is not None


def config_entry_title(hass: HomeAssistant, preset_entity_id: str) -> str:
    """Name the thermostat after the select's device, else after the select.

    A device's select is usually named relative to it ("Pilot wire mode"),
    which would give every thermostat the same title.
    """
    device = async_entity_id_to_device(hass, preset_entity_id)
    if device and (name := device.name_by_user or device.name):
        return name
    return wrapped_entity_config_entry_title(hass, preset_entity_id)


def async_hide_select(hass: HomeAssistant, entity_id: str) -> None:
    """Hide the select, which the thermostat replaces in the UI."""
    registry = er.async_get(hass)
    entity_entry = registry.async_get(entity_id)
    if entity_entry is not None and not entity_entry.hidden:
        registry.async_update_entity(
            entity_id, hidden_by=er.RegistryEntryHider.INTEGRATION
        )


def async_unhide_select(hass: HomeAssistant, entity_id: str) -> bool:
    """Unhide the select unless the user hid it, and say whether it was hidden."""
    registry = er.async_get(hass)
    entity_entry = registry.async_get(entity_id)
    if (
        entity_entry is not None
        and entity_entry.hidden_by == er.RegistryEntryHider.INTEGRATION
    ):
        registry.async_update_entity(entity_id, hidden_by=None)
        return True
    return False
