from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pilot_wire_climate.const import DOMAIN

from .conftest import SELECT, helper_entry, setup_helper


async def test_links_to_source_device(hass: HomeAssistant, select_entity, source_device, caplog):
    entry = helper_entry()
    await setup_helper(hass, entry)

    assert dr.async_entries_for_config_entry(
        dr.async_get(hass), entry.entry_id) == []
    [entity] = er.async_entries_for_config_entry(
        er.async_get(hass), entry.entry_id)
    assert entity.device_id == source_device.id
    assert "deprecated" not in caplog.text


async def test_migration_removes_duplicate_device(hass: HomeAssistant, select_entity, source_device):
    entry = helper_entry(minor_version=2)
    entry.add_to_hass(hass)
    device_registry = dr.async_get(hass)
    duplicate = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers=source_device.identifiers)
    assert duplicate.id != source_device.id
    er.async_get(hass).async_get_or_create(
        "climate", DOMAIN, entry.entry_id,
        config_entry=entry, device_id=duplicate.id)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.minor_version == 3
    assert device_registry.async_get(duplicate.id) is None
    [entity] = er.async_entries_for_config_entry(
        er.async_get(hass), entry.entry_id)
    assert entity.device_id == source_device.id


async def test_migration_maps_old_default_preset(hass: HomeAssistant, select_entity):
    entry = MockConfigEntry(domain=DOMAIN, version=1, minor_version=1, options={
        "presets": SELECT, "additional_modes": True, "default_preset": "away"})
    await setup_helper(hass, entry)

    assert entry.options["default_preset"] == "frost_protection"
    assert entry.minor_version == 3
