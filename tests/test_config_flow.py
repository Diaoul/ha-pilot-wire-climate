from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest

from custom_components.pilot_wire_climate.const import DOMAIN

from .conftest import (
    FOUR_OPTIONS,
    POWER,
    SELECT,
    SIX_OPTIONS,
    climate_entity_id,
    helper_entry,
    setup_helper,
)

OTHER = "select.other_pilot_wire_mode"


async def test_select_hidden_while_helper_exists(hass: HomeAssistant, select_entity):
    registry = er.async_get(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"select": SELECT}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert registry.async_get(SELECT).hidden_by is er.RegistryEntryHider.INTEGRATION

    await hass.config_entries.async_remove(result["result"].entry_id)
    await hass.async_block_till_done()
    assert registry.async_get(SELECT).hidden_by is None


async def test_user_hidden_select_stays_hidden(hass: HomeAssistant, select_entity):
    registry = er.async_get(hass)
    registry.async_update_entity(SELECT, hidden_by=er.RegistryEntryHider.USER)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"select": SELECT}
    )
    await hass.async_block_till_done()

    await hass.config_entries.async_remove(result["result"].entry_id)
    await hass.async_block_till_done()
    assert registry.async_get(SELECT).hidden_by is er.RegistryEntryHider.USER


async def test_title_from_device(hass: HomeAssistant, select_entity):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"select": SELECT}
    )

    assert result["title"] == "Heater"


async def test_title_without_device(hass: HomeAssistant):
    hass.states.async_set(
        "input_select.heater_mode",
        "comfort",
        {"options": ["off", "comfort"], "friendly_name": "Heater mode"},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"select": "input_select.heater_mode"}
    )

    assert result["title"] == "Heater mode"


async def change_options(hass: HomeAssistant, entry_id: str, **changes: object) -> None:
    entry = hass.config_entries.async_get_entry(entry_id)
    result = await hass.config_entries.options.async_init(entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**entry.options, **changes}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_change_select(hass: HomeAssistant, select_entity, source_entry):
    registry = er.async_get(hass)
    other_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=source_entry.entry_id,
        identifiers={("test", "other")},
        name="Other heater",
    )
    registry.async_get_or_create(
        "select",
        "test",
        "other_mode",
        config_entry=source_entry,
        device_id=other_device.id,
        suggested_object_id="other_pilot_wire_mode",
        has_entity_name=True,
        original_name="Pilot wire mode",
    )
    hass.states.async_set(OTHER, "eco", {"options": SIX_OPTIONS})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"select": SELECT}
    )
    await hass.async_block_till_done()
    entry = result["result"]

    await change_options(hass, entry.entry_id, select=OTHER)

    assert entry.options["select"] == OTHER
    assert entry.title == "Other heater"
    assert registry.async_get(SELECT).hidden_by is None
    assert registry.async_get(OTHER).hidden_by is er.RegistryEntryHider.INTEGRATION
    [climate] = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert climate.device_id == other_device.id
    assert hass.states.get(climate.entity_id).attributes["preset_mode"] == "eco"


async def test_change_option_reloads(hass: HomeAssistant, select_entity):
    hass.states.async_set(POWER, "100")
    entry = helper_entry(power_sensor=POWER, power_threshold=5)
    await setup_helper(hass, entry)
    entity_id = climate_entity_id(hass, entry)
    assert hass.states.get(entity_id).attributes["hvac_action"] == "heating"

    await change_options(hass, entry.entry_id, power_threshold=500)

    assert hass.states.get(entity_id).attributes["hvac_action"] == "idle"
    assert er.async_get(hass).async_get(SELECT).hidden_by is None


async def configure(hass: HomeAssistant, **options: object):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    return await hass.config_entries.flow.async_configure(result["flow_id"], options)


@pytest.mark.parametrize("default_preset", ["comfort_1", "comfort_2"])
async def test_default_preset_must_be_offered(
    hass: HomeAssistant, select_entity, default_preset
):
    result = await configure(
        hass, select=SELECT, additional_modes=False, default_preset=default_preset
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "default_preset_not_offered"}


async def test_default_preset_needs_an_option(hass: HomeAssistant, select_entity):
    hass.states.async_set(SELECT, "comfort", {"options": FOUR_OPTIONS})

    result = await configure(hass, select=SELECT, default_preset="comfort_1")

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "default_preset_missing"}


async def test_options_flow_validates(hass: HomeAssistant, select_entity):
    entry = helper_entry()
    await setup_helper(hass, entry)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {**entry.options, "additional_modes": False, "default_preset": "comfort_1"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "default_preset_not_offered"}
    assert entry.options["additional_modes"] is True
