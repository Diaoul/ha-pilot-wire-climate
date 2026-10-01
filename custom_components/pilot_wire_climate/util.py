"""Helpers for the pilot wire climate integration."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device import async_entity_id_to_device
from homeassistant.helpers.schema_config_entry_flow import (
    wrapped_entity_config_entry_title,
)

from .const import VALUES_MAPPING


def get_value_key(input_value: str) -> str | None:
    """Return the pilot wire value a select option stands for."""
    for key, alternatives in VALUES_MAPPING.items():
        if input_value in alternatives:
            return key
    return None


def config_entry_title(hass: HomeAssistant, preset_entity_id: str) -> str:
    """Name the thermostat after the select's device, else after the select.

    A device's select is usually named relative to it ("Pilot wire mode"),
    which would give every thermostat the same title.
    """
    device = async_entity_id_to_device(hass, preset_entity_id)
    if device and (name := device.name_by_user or device.name):
        return name
    return wrapped_entity_config_entry_title(hass, preset_entity_id)
