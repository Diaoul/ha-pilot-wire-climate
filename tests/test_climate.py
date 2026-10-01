import pytest
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import async_mock_service

from .conftest import (FOUR_OPTIONS, POWER, TEMPERATURE, SELECT, SIX_OPTIONS, climate_entity_id,
                       helper_entry, setup_helper)


async def call(hass: HomeAssistant, service: str, entity_id: str, **data) -> None:
    await hass.services.async_call(
        "climate", service, {"entity_id": entity_id, **data}, blocking=True)


@pytest.mark.parametrize("additional_modes", [True, False])
async def test_select_without_comfort_minus_options(hass: HomeAssistant, select_entity, additional_modes):
    hass.states.async_set(SELECT, "comfort", {"options": FOUR_OPTIONS})
    entry = helper_entry(additional_modes=additional_modes)
    await setup_helper(hass, entry)

    state = hass.states.get(climate_entity_id(hass, entry))
    assert state.state == "heat"
    assert state.attributes["preset_mode"] == "comfort"


async def test_preset_follows_select(hass: HomeAssistant, select_entity):
    entry = helper_entry()
    await setup_helper(hass, entry)
    entity_id = climate_entity_id(hass, entry)

    for option, preset in [("off", "none"), ("frost_protection", "away"), ("eco", "eco"),
                           ("comfort_-1", "comfort_1"), ("comfort_-2", "comfort_2")]:
        hass.states.async_set(SELECT, option, {"options": SIX_OPTIONS})
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).attributes["preset_mode"] == preset


async def test_comfort_minus_is_comfort_without_additional_modes(hass: HomeAssistant, select_entity):
    hass.states.async_set(SELECT, "comfort_-1", {"options": SIX_OPTIONS})
    entry = helper_entry(additional_modes=False)
    await setup_helper(hass, entry)

    assert hass.states.get(climate_entity_id(hass, entry)
                           ).attributes["preset_mode"] == "comfort"


async def test_set_preset_selects_matching_option(hass: HomeAssistant, select_entity):
    options = ["Off", "FrostProtection", "Eco",
               "Comfort", "ComfortMinus1", "ComfortMinus2"]
    hass.states.async_set(SELECT, "Comfort", {"options": options})
    entry = helper_entry()
    await setup_helper(hass, entry)
    calls = async_mock_service(hass, "select", "select_option")
    entity_id = climate_entity_id(hass, entry)

    await call(hass, "set_preset_mode", entity_id, preset_mode="comfort_2")
    await call(hass, "set_hvac_mode", entity_id, hvac_mode="off")
    hass.states.async_set(SELECT, "Off", {"options": options})
    await call(hass, "set_hvac_mode", entity_id, hvac_mode="heat")

    assert [c.data["option"] for c in calls] == ["ComfortMinus2", "Off", "Eco"]


async def test_options_are_read_when_used(hass: HomeAssistant, select_entity):
    hass.states.async_set(SELECT, "comfort", {"options": FOUR_OPTIONS})
    entry = helper_entry()
    await setup_helper(hass, entry)
    calls = async_mock_service(hass, "select", "select_option")
    entity_id = climate_entity_id(hass, entry)

    with pytest.raises(HomeAssistantError):
        await call(hass, "set_preset_mode", entity_id, preset_mode="comfort_1")

    hass.states.async_set(SELECT, "comfort", {"options": SIX_OPTIONS})
    await call(hass, "set_preset_mode", entity_id, preset_mode="comfort_1")
    assert calls[-1].data["option"] == "comfort_-1"


async def test_select_missing(hass: HomeAssistant, select_entity):
    hass.states.async_remove(SELECT)
    entry = helper_entry()
    await setup_helper(hass, entry)
    entity_id = climate_entity_id(hass, entry)
    calls = async_mock_service(hass, "select", "select_option")

    assert hass.states.get(entity_id).state == "unavailable"
    await call(hass, "set_hvac_mode", entity_id, hvac_mode="off")
    assert calls == []


async def test_follows_select_availability(hass: HomeAssistant, select_entity):
    entry = helper_entry()
    await setup_helper(hass, entry)
    entity_id = climate_entity_id(hass, entry)

    hass.states.async_set(SELECT, "unavailable", {"options": SIX_OPTIONS})
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "unavailable"

    hass.states.async_set(SELECT, "unknown", {"options": SIX_OPTIONS})
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == "unknown"
    assert state.attributes["preset_mode"] is None

    hass.states.async_set(SELECT, "eco", {"options": SIX_OPTIONS})
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "heat"


async def test_input_select_source(hass: HomeAssistant):
    hass.states.async_set("input_select.heater_mode",
                          "comfort", {"options": SIX_OPTIONS})
    entry = helper_entry(presets="input_select.heater_mode")
    await setup_helper(hass, entry)
    calls = async_mock_service(hass, "input_select", "select_option")

    await call(hass, "set_preset_mode", climate_entity_id(hass, entry), preset_mode="eco")

    assert [(c.data["entity_id"], c.data["option"]) for c in calls] == [
        ("input_select.heater_mode", "eco")]


async def test_set_hvac_mode_keeps_current_preset(hass: HomeAssistant, select_entity):
    entry = helper_entry()
    await setup_helper(hass, entry)
    entity_id = climate_entity_id(hass, entry)
    calls = async_mock_service(hass, "select", "select_option")

    await call(hass, "set_hvac_mode", entity_id, hvac_mode="heat")
    await hass.services.async_call("climate", "turn_on", {"entity_id": entity_id}, blocking=True)
    assert calls == []

    hass.states.async_set(SELECT, "off", {"options": SIX_OPTIONS})
    await call(hass, "set_hvac_mode", entity_id, hvac_mode="off")
    assert calls == []
    await call(hass, "set_hvac_mode", entity_id, hvac_mode="heat")
    assert [c.data["option"] for c in calls] == ["eco"]


async def setup_with_sensors(hass: HomeAssistant, power: str = "0", temperature: str = "20.5"):
    hass.states.async_set(TEMPERATURE, temperature)
    hass.states.async_set(POWER, power)
    entry = helper_entry(temperature=TEMPERATURE,
                         power=POWER, power_threshold=5)
    await setup_helper(hass, entry)
    return climate_entity_id(hass, entry)


@pytest.mark.parametrize(("option", "power", "action"), [
    ("comfort", "1000", "heating"),
    ("comfort", "5", "idle"),
    ("off", "0", "off"),
    ("off", "1000", "heating"),
])
async def test_hvac_action(hass: HomeAssistant, select_entity, option, power, action):
    hass.states.async_set(SELECT, option, {"options": SIX_OPTIONS})
    entity_id = await setup_with_sensors(hass, power=power)

    assert hass.states.get(entity_id).attributes["hvac_action"] == action


async def test_no_hvac_action_without_power_sensor(hass: HomeAssistant, select_entity):
    entry = helper_entry()
    await setup_helper(hass, entry)

    assert "hvac_action" not in hass.states.get(
        climate_entity_id(hass, entry)).attributes


async def test_sensor_updates(hass: HomeAssistant, select_entity):
    entity_id = await setup_with_sensors(hass)
    assert hass.states.get(entity_id).attributes["current_temperature"] == 20.5

    hass.states.async_set(TEMPERATURE, "21.5")
    hass.states.async_set(POWER, "800")
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes["current_temperature"] == 21.5
    assert state.attributes["hvac_action"] == "heating"

    hass.states.async_set(TEMPERATURE, "unavailable")
    hass.states.async_set(POWER, "unknown")
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes["current_temperature"] is None
    assert "hvac_action" not in state.attributes


@pytest.mark.parametrize("value", ["abc", "inf"])
async def test_invalid_sensor_value_keeps_last_reading(hass: HomeAssistant, select_entity, caplog, value):
    entity_id = await setup_with_sensors(hass)

    hass.states.async_set(TEMPERATURE, value)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).attributes["current_temperature"] == 20.5
    assert "Unable to update from temperature sensor" in caplog.text


async def test_reads_sources_once_home_assistant_started(hass: HomeAssistant, select_entity):
    hass.set_state(CoreState.not_running)
    entity_id = await setup_with_sensors(hass, power="1000")
    state = hass.states.get(entity_id)
    assert state.state == "unknown"
    assert state.attributes["current_temperature"] is None

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "heat"
    assert state.attributes["preset_mode"] == "comfort"
    assert state.attributes["current_temperature"] == 20.5
    assert state.attributes["hvac_action"] == "heating"


async def test_named_after_device(hass: HomeAssistant, select_entity):
    entry = helper_entry()
    await setup_helper(hass, entry)

    assert hass.states.get(climate_entity_id(hass, entry)
                           ).attributes["friendly_name"] == "Heater"


async def test_default_name_without_device(hass: HomeAssistant):
    hass.states.async_set("input_select.heater_mode",
                          "comfort", {"options": SIX_OPTIONS})
    entry = helper_entry(presets="input_select.heater_mode")
    await setup_helper(hass, entry)

    assert hass.states.get(climate_entity_id(hass, entry)
                           ).attributes["friendly_name"] == "Thermostat"


async def test_temperature_unit_from_sensor(hass: HomeAssistant, select_entity):
    hass.states.async_set(TEMPERATURE, "68", {"unit_of_measurement": "°F"})
    entry = helper_entry(temperature=TEMPERATURE)
    await setup_helper(hass, entry)

    assert hass.states.get(climate_entity_id(hass, entry)
                           ).attributes["current_temperature"] == 20


async def test_unknown_mode_is_logged(hass: HomeAssistant, select_entity, caplog):
    entry = helper_entry()
    await setup_helper(hass, entry)

    hass.states.async_set(SELECT, "turbo", {"options": [*SIX_OPTIONS, "turbo"]})
    await hass.async_block_till_done()

    assert hass.states.get(climate_entity_id(hass, entry)
                           ).attributes["preset_mode"] == "comfort"
    assert "unknown pilot wire mode turbo" in caplog.text
