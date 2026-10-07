# 🔥 Pilot Wire Climate

[![fr](https://img.shields.io/badge/lang-fr-blue.svg)](README-fr.md)

A Home Assistant helper that turns a pilot wire heater module into a proper `climate` entity, with presets, on/off, heating detection and optional temperature and humidity readings.

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Diaoul&repository=hass-pilot-wire-climate&category=integration)

## ✨ Features

- 🎛️ **Presets from the Select** - Comfort, Comfort -1 °C, Comfort -2 °C, Eco and Frost protection map to climate presets
- 🔛 **On/Off** - Off is the HVAC mode; turning back on restores the last preset, even across restarts
- 🔥 **Heating Detection** - A power sensor and a threshold tell heating from idle
- 🌡️ **Temperature and Humidity** - Optional sensors shown on the thermostat
- 🧩 **Only What the Module Supports** - Presets the select has no option for are not offered
- 🏷️ **Linked to the Module** - The thermostat joins the select's device, is named after it, and hides the now redundant select
- 🔄 **Follows Renames** - Renaming the select or a sensor updates the thermostat instead of breaking it
- 🔌 **Availability Handling** - The thermostat is unavailable while its select is, and a sensor reading clears while its sensor is unavailable or reports no number
- ⚙️ **Editable** - Every setting, the select included, can be changed afterwards from the helper's options

## 📦 Installation

Click the button above to add this repository to HACS, then download **Pilot Wire Climate** and restart Home Assistant.

**Requires Home Assistant 2026.10 or newer** (enforced by HACS).

> **Coming from [faizpuru/ha-pilot-wire-climate](https://github.com/faizpuru/ha-pilot-wire-climate):**
> this fork has no YAML configuration and no `none` preset. Recreate YAML
> thermostats as helpers, and switch automations that set or test the `none`
> preset to the `off` HVAC mode. Thermostats created from the UI migrate
> automatically.

## 🚀 Quick Start

1. Go to **Settings** → **Devices & services** → [**Helpers**](https://my.home-assistant.io/redirect/helpers/)
2. **Create helper** → **Pilot Wire Thermostat**
3. **Select the module's pilot wire select** (required) - a `select` or an `input_select` with pilot wire options, not used by another thermostat
4. **(Optional)** Pick a temperature sensor, a humidity sensor and a power sensor
5. **(Optional)** Set the power threshold, the default preset, and whether to offer the Comfort -1 °C and -2 °C presets

The thermostat appears on the module's device, named after it.

## 🔧 Options

| Option | Default | Description |
| :----- | :------ | :---------- |
| Select entity | required | The module's pilot wire `select` or `input_select` |
| Temperature sensor | none | Shown as the current temperature, in the sensor's unit, or in °C for a sensor in kelvin |
| Humidity sensor | none | Shown as the current humidity |
| Power sensor | none | Tells heating from idle |
| Additional modes | on | Offer Comfort -1 °C and Comfort -2 °C when the select has them |
| Power threshold | 0 W | Power above which the heater counts as heating, in watts whatever the sensor's unit |
| Default preset | Comfort | Preset used to turn on a thermostat that has no previous preset; must be one the select has and the thermostat offers |

## 🧠 How It Works

The thermostat is a view over the select: the only thing it keeps of its own is the last preset.

| Select option | Thermostat |
| :------------ | :--------- |
| `comfort`, `Comfort` | Heat, Comfort |
| `comfort_-1`, `ComfortMinus1` | Heat, Comfort -1 °C |
| `comfort_-2`, `ComfortMinus2` | Heat, Comfort -2 °C |
| `eco`, `Eco` | Heat, Eco |
| `frost_protection`, `FrostProtection` | Heat, Frost protection (`away`) |
| `off`, `Off` | Off |

- **Setting a preset** selects the matching option, which also turns an off thermostat on; setting the current preset sends nothing
- **Turning on** restores the last preset, or the default preset when there is none; turning on a thermostat that is already heating sends nothing
- **Heating status** is `heating` above the power threshold and `idle` below it, and `off` whenever the thermostat is off, with or without a power sensor
- **An unknown option**, or one for a preset that is not offered, shows heat with no preset; an unknown one is also logged as a warning

## 🔌 Compatibility

Any module exposing its pilot wire mode as a select with the options above, including:

- **Equation**: SIN-4-FP-21_EQU
- **Legrand**: 064882
- **NodOn**: SIN-4-FP-20, SIN-4-FP-21

## ⚙️ Technical Details

- **No Polling:** The thermostat only reacts to state changes of its select and sensors
- **Startup:** Sources are read once Home Assistant has started
- **Restart Recovery:** The last preset is stored, so turning on after a restart goes back to it
- **Removal:** Deleting the helper unhides the select, unless you hid it yourself

## 🤝 Support

If you encounter issues:
- Enable debug logging for `custom_components.pilot_wire_climate` and check the logs
- Check the select's options in **Developer Tools** → **States**
- Open an issue on [GitHub](https://github.com/Diaoul/hass-pilot-wire-climate/issues)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Forked from [faizpuru/ha-pilot-wire-climate](https://github.com/faizpuru/ha-pilot-wire-climate), made with ❤️ for the Home Assistant community
