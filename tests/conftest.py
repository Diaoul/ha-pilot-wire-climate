from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Imported before the hass fixture puts its own test config dir first on
# sys.path, whose custom_components package would otherwise shadow this one.
from custom_components.pilot_wire_climate.const import DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"

SELECT = "select.heater_pilot_wire_mode"
TEMPERATURE = "sensor.heater_temperature"
HUMIDITY = "sensor.heater_humidity"
POWER = "sensor.heater_power"
SIX_OPTIONS = ["off", "frost_protection", "eco", "comfort", "comfort_-1", "comfort_-2"]
FOUR_OPTIONS = ["off", "frost_protection", "eco", "comfort"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    return


@pytest.fixture
def source_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def source_device(hass: HomeAssistant, source_entry) -> dr.DeviceEntry:
    return dr.async_get(hass).async_get_or_create(
        config_entry_id=source_entry.entry_id,
        identifiers={("test", "heater")},
        name="Heater",
    )


@pytest.fixture
def select_entity(hass: HomeAssistant, source_entry, source_device) -> str:
    er.async_get(hass).async_get_or_create(
        "select",
        "test",
        "heater_mode",
        config_entry=source_entry,
        device_id=source_device.id,
        suggested_object_id="heater_pilot_wire_mode",
        has_entity_name=True,
        original_name="Pilot wire mode",
    )
    hass.states.async_set(SELECT, "comfort", {"options": SIX_OPTIONS})
    return SELECT


def helper_entry(minor_version: int = 6, **options) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=minor_version,
        title="Pilot wire mode",
        options={
            "select": SELECT,
            "additional_modes": True,
            "power_threshold": 0,
            "default_preset": "eco",
            **options,
        },
    )


async def setup_helper(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def climate_entity_id(hass: HomeAssistant, entry: MockConfigEntry) -> str:
    [entity] = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    return entity.entity_id
