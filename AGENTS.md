# Working in this repo

## What this is

One Home Assistant **custom integration**, `custom_components/pilot_wire_climate`,
installed through HACS. It is a helper: a `climate` entity built over a pilot
wire module's `select` entity, with optional temperature, humidity and power
sensors. It talks to no device itself; every command is a `select.select_option`
on the select it wraps.

Consequences that are easy to miss:

- **The repo is not what runs.** HACS installs the zip attached to a GitHub
  release. Nothing on `main` reaches a Home Assistant until it is released and
  downloaded there, followed by a restart. When debugging, confirm which version
  the install actually has.
- **Config entry options are a public API.** The option keys and their values
  are stored in each user's config entry. Renaming a key or changing a value's
  format needs a migration in `async_migrate_entry`, guarded by
  `MINOR_VERSION`, and a test feeding it an old entry.
- **The entity's unique ID is the config entry ID**, and the entity sits on the
  select's device. Changing either orphans the entity users have renamed and
  wired into automations.
- **This is a fork** of [faizpuru/ha-pilot-wire-climate](https://github.com/faizpuru/ha-pilot-wire-climate)
  that has diverged on purpose (no YAML, renamed option keys). Upstream changes
  are ported by hand, rewritten to this code's conventions, not merged.

## What it controls, and why that matters

Electric heaters. A wrong preset heats an empty room or leaves an occupied one
cold, and every `select_option` is a radio command to the module.

- **Send nothing that changes nothing.** Turning on a thermostat that is
  already heating sends nothing, and turning on from off goes back to the last
  preset. Both used to send the default preset, which flipped heaters through
  it right before an automation set the preset it wanted.
- **The select is the source of truth.** The thermostat stores only the last
  preset, to turn back on with. Everything else is read from the select and
  sensors on each state change.
- **Unavailable means unavailable.** The thermostat follows its select's
  availability, and a sensor reading clears while its sensor is unavailable.
  A frozen `hvac_action: heating` would mislead load-shedding automations.

## Track current Home Assistant

Write it the way core writes its helpers today, not the legacy way that still
happens to work: `entry.runtime_data`, `AddConfigEntryEntitiesCallback`,
`probatio` for schemas, the `helper_integration` functions for linking to the
source device and following its renames, `_attr_*` class attributes for fixed
values. `generic_thermostat`, `derivative` and the other core helpers are the
reference.

The test harness `pytest-homeassistant-custom-component` pins one Home
Assistant release. Renovate bumps it, sometimes to a beta; a red bump is the
early warning that the next Home Assistant breaks something. Fix it before
upgrading Home Assistant. When a fix needs a newer Home Assistant, raise
`homeassistant` in `hacs.json` so HACS refuses older installs.

## Don't invent fallbacks

If the select has no option for the requested preset, raise rather than send
something close. Likewise, don't add handling for a failure you have only
imagined; fix what is observed.

## Comments

Comments explain **why**. If a comment restates the line below it, delete it.

```python
# bad
# Return early when the mode is unchanged
if hvac_mode == self.hvac_mode:
    return

# good
if hvac_mode == self.hvac_mode:
    # Otherwise turning on a heating thermostat would reset its preset.
    return
```

## Verify before committing

```bash
pip install -r requirements_test.txt
pytest
ruff check
ruff format --check
mypy
```

CI runs the same, plus hassfest and the HACS validation. Tests use real Home
Assistant fixtures, not mocks of it; keep coverage near its current level, and
when fixing a bug, check the new test fails without the fix.

State clearly what was verified and what was not. A passing suite is not the
integration working on a real module: check a live install's states and logs
after a release.

## Debugging

Read the select's history before reasoning from the code: what it reported,
when, and what the thermostat showed then. Enable debug logging for
`custom_components.pilot_wire_climate`.

## Docs must match the code

When behaviour changes, update in the same commit:

1. `README.md` and `README-fr.md`
2. the strings in `translations/en.json` and `translations/fr.json`

## Versioning and releases

Semantic versioning. Anything that needs users to change their setup or
automations is a major bump, whatever its size.

The release is the `version` in `manifest.json`. Bump it in its own commit
(`Release X.Y.Z`) and push: once the tests pass on `main`, the release workflow
creates the GitHub release with the zip attached. Then edit the generated notes,
which are empty for direct commits; put breaking changes under a `### Breaking`
heading first, with the remedy.

## Commits

Commit messages explain the reasoning, not the diff: what was wrong, why the
chosen fix, and what tradeoff it accepts. One concern per commit. Commits are
gpg-signed; if signing times out, retry rather than disabling it.
