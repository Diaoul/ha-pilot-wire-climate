from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from custom_components.pilot_wire_climate.const import DOMAIN

from .conftest import SELECT


async def test_select_hidden_while_helper_exists(hass: HomeAssistant, select_entity):
    registry = er.async_get(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"presets": SELECT}
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
        result["flow_id"], {"presets": SELECT}
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
        result["flow_id"], {"presets": SELECT}
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
        result["flow_id"], {"presets": "input_select.heater_mode"}
    )

    assert result["title"] == "Heater mode"
