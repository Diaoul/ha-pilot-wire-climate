# README - Pilot Wire Integration for Home Assistant

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/Diaoul/ha-pilot-wire-climate/blob/master/README.md)
[![fr](https://img.shields.io/badge/lang-fr-blue.svg)](https://github.com/Diaoul/ha-pilot-wire-climate/blob/master/README-fr.md)

## Overview
This Home Assistant integration simplifies the setup of pilot wire modules for heating systems, providing seamless conversion of multiple entities (`select` and `power`) into a unified `climate` entity. An optional temperature `sensor` entity can also be added. This integration is ideal for controlling pilot wire heating modules, enabling streamlined control and monitoring of heating states.

### Key Features
- Converts `select` and `power` entities into a single `climate` entity.
- Utilizes the `select` entity to adjust the pilot wire preset modes.
- Uses the `power` entity to detect whether the heating is on or off.
- Configurable power threshold to determine heating state.
- Configurable default power on preset.
- Optional support for temperature `sensor` entities.

### Compatibility
The integration is compatible with the following devices or any climate manageable with a select entity :
- **Equation**: SIN-4-FP-21_EQU
- **Legrand**: 064882
- **NodOn**: SIN-4-FP-20, SIN-4-FP-21

## Installation

### Option 1: Using HACS (Home Assistant Community Store)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Diaoul&repository=ha-pilot-wire-climate&category=integration)

1. Use the button above or search for "Wire Pilot Climate" in HACS
2. Download the integration and restart Home Assistant

### Option 2: Manual Installation
1. Copy the integration files to your Home Assistant custom components directory.
2. Restart Home Assistant.
3. Add the integration through the Home Assistant UI.

## Configuration
This integration is set up from the Home Assistant UI only.

> [!IMPORTANT]  
> This integration is implemented as a **Helper** in Home Assistant and is not a full-fledged custom integration. 
> 
> To initialize this helper, follow this path in your Home Assistant interface:
> 1. Settings
> 2. Devices and Services
> 3. Helpers
> 4. Create Helper
> 5. Pilot Wire Thermostat
>
> Once configured, the climate entity will appear in the Helpers tab. It will be automatically linked to the device of the select entity you chose during setup.


## 🤝 Contributing

Contributions are welcome! Feel free to:
- 🐛 Report bugs
- 💡 Suggest improvements
- 🔀 Submit pull requests

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
If you find this integration helpful, please consider giving it a ⭐️ on GitHub!
