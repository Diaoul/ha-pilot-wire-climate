# Changelog

## [3.0.1](https://github.com/Diaoul/hass-pilot-wire-climate/compare/3.0.0...3.0.1) (2026-10-10)


### Bug Fixes

* write the English form labels in sentence case ([cc3a34d](https://github.com/Diaoul/hass-pilot-wire-climate/commit/cc3a34df006dc1b77d10a2bc3e9e1cab18d92cc0))

## [3.0.0](https://github.com/Diaoul/hass-pilot-wire-climate/compare/2.3.0...3.0.0) (2026-10-07)


### ⚠ BREAKING CHANGES

* **climate:** preset_mode is now empty, instead of comfort, while the select reports an unknown option, or Comfort -1 °C or -2 °C with additional modes off. Automations that relied on comfort in those cases should enable additional modes, or read the select's state instead.

### Features

* **config-flow:** refuse a select that is not pilot wire or already used ([804ddbe](https://github.com/Diaoul/hass-pilot-wire-climate/commit/804ddbecfa065aaaafdab637f4df08bf37a53ab6))


### Bug Fixes

* **climate:** clear a sensor reading that is not a number ([504f4d2](https://github.com/Diaoul/hass-pilot-wire-climate/commit/504f4d2dc9b096610be8d9b401c617e72a5b8283))
* **climate:** compare a kW power sensor with the threshold in watts ([8034b58](https://github.com/Diaoul/hass-pilot-wire-climate/commit/8034b58a84f4463292f2b79198856ae6d3de368e))
* **climate:** log an unusable select or sensor once, not on every change ([7473a20](https://github.com/Diaoul/hass-pilot-wire-climate/commit/7473a20a657d4e53ce592fdfcf9b13a568f46403))
* **climate:** name the mode in the missing option error, not a module's option ([ed3daca](https://github.com/Diaoul/hass-pilot-wire-climate/commit/ed3daca25e4ee1c38355cc9cd87135689348f984))
* **climate:** send nothing when setting the current preset ([bdd72f6](https://github.com/Diaoul/hass-pilot-wire-climate/commit/bdd72f637f310664181d900c423d65c8b64310f3))
* **climate:** show a kelvin temperature sensor in °C ([da74866](https://github.com/Diaoul/hass-pilot-wire-climate/commit/da74866318e198d4446f4c364f721a850e200e2c))
* **climate:** show no preset for a mode the thermostat cannot name ([db0e9a4](https://github.com/Diaoul/hass-pilot-wire-climate/commit/db0e9a43d75b5684d2b788c5a8cdab9e71aab7ec))
* **climate:** wait for the select and pass the caller's context ([338bcee](https://github.com/Diaoul/hass-pilot-wire-climate/commit/338bcee41880240574ee0a69e2fc4ecabe0a92e8))
* **config-flow:** reject a default preset the thermostat cannot use ([ff0e7ad](https://github.com/Diaoul/hass-pilot-wire-climate/commit/ff0e7ad9652cda2657d0557e37daa93e43ec1cf9))
* report a default preset the thermostat does not offer in Repairs ([8cf9f7e](https://github.com/Diaoul/hass-pilot-wire-climate/commit/8cf9f7eff872ce7362d5a6ed71df1e325e7531a0))
