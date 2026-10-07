from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pilot_wire_climate.const import DOMAIN

from .conftest import SELECT, helper_entry, setup_helper


async def test_links_to_source_device(
    hass: HomeAssistant, select_entity, source_device, caplog
):
    entry = helper_entry()
    await setup_helper(hass, entry)

    assert dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id) == []
    [entity] = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert entity.device_id == source_device.id
    assert "deprecated" not in caplog.text


async def test_migration_removes_duplicate_device(
    hass: HomeAssistant, select_entity, source_device
):
    entry = helper_entry(minor_version=2)
    entry.add_to_hass(hass)
    device_registry = dr.async_get(hass)
    duplicate = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers=source_device.identifiers
    )
    assert duplicate.id != source_device.id
    er.async_get(hass).async_get_or_create(
        "climate", DOMAIN, entry.entry_id, config_entry=entry, device_id=duplicate.id
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.minor_version == 6
    assert device_registry.async_get(duplicate.id) is None
    [entity] = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert entity.device_id == source_device.id


async def test_migration_maps_old_default_preset(hass: HomeAssistant, select_entity):
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=1,
        options={"presets": SELECT, "additional_modes": True, "default_preset": "away"},
    )
    await setup_helper(hass, entry)

    assert entry.options["default_preset"] == "away"
    assert entry.minor_version == 6


@pytest.mark.parametrize(
    ("stored", "migrated"),
    [("comfort-1", "comfort_1"), ("frost_protection", "away"), ("eco", "eco")],
)
async def test_migration_stores_default_preset_as_preset(
    hass: HomeAssistant, select_entity, stored, migrated
):
    entry = helper_entry(minor_version=4, default_preset=stored)
    await setup_helper(hass, entry)

    assert entry.options["default_preset"] == migrated


async def test_follows_select_rename(hass: HomeAssistant, select_entity):
    entry = helper_entry()
    await setup_helper(hass, entry)

    er.async_get(hass).async_update_entity(SELECT, new_entity_id="select.renamed")
    hass.states.async_set(
        "select.renamed", "eco", {"options": ["off", "eco", "comfort"]}
    )
    await hass.async_block_till_done()

    assert entry.options["select"] == "select.renamed"
    assert er.async_get(hass).async_get("select.renamed").hidden_by is None
    [entity] = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert hass.states.get(entity.entity_id).attributes["preset_mode"] == "eco"


async def test_follows_sensor_rename(hass: HomeAssistant, select_entity, source_entry):
    registry = er.async_get(hass)
    sensors = ("temperature", "humidity", "power")
    for sensor in sensors:
        registry.async_get_or_create(
            "sensor",
            "test",
            sensor,
            config_entry=source_entry,
            suggested_object_id=f"heater_{sensor}",
        )
    entry = helper_entry(
        **{f"{sensor}_sensor": f"sensor.heater_{sensor}" for sensor in sensors}
    )
    await setup_helper(hass, entry)

    for sensor in sensors:
        registry.async_update_entity(
            f"sensor.heater_{sensor}", new_entity_id=f"sensor.new_{sensor}"
        )
        await hass.async_block_till_done()

    for sensor in sensors:
        assert entry.options[f"{sensor}_sensor"] == f"sensor.new_{sensor}"


async def test_migration_titles_entry_after_device(hass: HomeAssistant, select_entity):
    entry = helper_entry(minor_version=3)
    await setup_helper(hass, entry)

    assert entry.title == "Heater"


async def test_migration_keeps_custom_title(hass: HomeAssistant, select_entity):
    entry = helper_entry(minor_version=3)
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(entry, title="Bathroom")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.title == "Bathroom"


async def test_migration_renames_option_keys(hass: HomeAssistant, select_entity):
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=5,
        options={
            "presets": SELECT,
            "temperature": "sensor.heater_temperature",
            "power": "sensor.heater_power",
            "additional_modes": True,
            "power_threshold": 0,
            "default_preset": "eco",
        },
    )
    await setup_helper(hass, entry)

    assert entry.minor_version == 6
    assert entry.options == {
        "select": SELECT,
        "temperature_sensor": "sensor.heater_temperature",
        "power_sensor": "sensor.heater_power",
        "additional_modes": True,
        "power_threshold": 0,
        "default_preset": "eco",
    }


async def test_repair_for_default_preset_not_offered(
    hass: HomeAssistant, select_entity
):
    issues = ir.async_get(hass)
    entry = helper_entry(additional_modes=False, default_preset="comfort_1")
    await setup_helper(hass, entry)
    issue_id = f"default_preset_not_offered_{entry.entry_id}"
    assert issues.async_get_issue(DOMAIN, issue_id) is not None

    hass.config_entries.async_update_entry(
        entry, options={**entry.options, "default_preset": "eco"}
    )
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert issues.async_get_issue(DOMAIN, issue_id) is None


async def test_repair_removed_with_entry(hass: HomeAssistant, select_entity):
    issues = ir.async_get(hass)
    entry = helper_entry(additional_modes=False, default_preset="comfort_2")
    await setup_helper(hass, entry)
    issue_id = f"default_preset_not_offered_{entry.entry_id}"
    assert issues.async_get_issue(DOMAIN, issue_id) is not None

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    assert issues.async_get_issue(DOMAIN, issue_id) is None
