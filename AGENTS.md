# Working in this repo

## What this is

A Home Assistant **custom integration**, installed through HACS: a helper that
builds a `climate` entity over a pilot wire module's `select` entity. It talks
to no device itself; every command is a `select.select_option` on the select it
wraps.

Consequences that are easy to miss:

- **The repo is not what runs.** HACS installs the zip attached to a GitHub
  release. Nothing on `main` reaches a Home Assistant until it is released and
  downloaded there, followed by a restart. When debugging, confirm which version
  the install actually has.
- **Config entry options are a public API.** They are stored in each user's
  config entry. Renaming a key or changing a value's format needs a config
  entry migration and a test feeding it an old entry.
- **The entity's identity is a public API.** Changing its unique ID or the
  device it sits on orphans the entity users have renamed and wired into
  automations.
- **This is a fork** of [faizpuru/ha-pilot-wire-climate](https://github.com/faizpuru/ha-pilot-wire-climate)
  that has diverged on purpose. Upstream changes are ported by hand, rewritten
  to this code's conventions, not merged.

## What it controls, and why that matters

Electric heaters. A wrong preset heats an empty room or leaves an occupied one
cold, and every `select_option` is a radio command to the module.

- **Send nothing that changes nothing.** A command that leaves the heater where
  it is, or passes it through a preset on the way to another, is noise on the
  radio and can race the automation that is setting the preset it wants.
- **The select is the source of truth.** Don't cache what the select or a
  sensor reports; read it on each state change. Keep only what the select
  cannot tell you.
- **Unavailable means unavailable.** When the select or a sensor is
  unavailable, show that, not its last value. A frozen `hvac_action: heating`
  would mislead load-shedding automations.
- **A failed command fails the caller.** The automation that asked for a preset
  must see the error, not a success logged over in the background.

## Track current Home Assistant

Write it the way core writes its helpers today, not the legacy way that still
happens to work. `generic_thermostat`, `derivative` and the other core helpers
are the reference.

The test harness pins one Home Assistant release, and Renovate bumps it,
sometimes to a beta. A red bump is the early warning that the next Home
Assistant breaks something: fix it before upgrading Home Assistant. When a fix
needs a newer Home Assistant, raise `homeassistant` in `hacs.json` so HACS
refuses older installs.

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

Run the mise tasks that CI runs (`mise tasks` lists them). Tests use real Home
Assistant fixtures, not mocks of it. Don't let coverage drop, and when fixing a
bug, check that the new test fails without the fix.

State clearly what was verified and what was not. A passing suite is not the
integration working on a real module: check a live install's states and logs
after a release.

## Debugging

Read the select's history before reasoning from the code: what it reported,
when, and what the thermostat showed then. Enable debug logging for
`custom_components.pilot_wire_climate`.

## Docs must match the code

When behaviour changes, update both READMEs (English and French) and both
translations in the same commit.

## Versioning and releases

Semantic versioning. Anything that needs users to change their setup or
automations is a major bump, whatever its size.

Releases are cut from the commit messages by release-please. Never bump the
version by hand. The release notes are built from the `feat` and `fix`
summaries and from each `BREAKING CHANGE:` footer, verbatim, so write that
footer as the remedy users will read.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/). A change that
needs users to act gets a `!` and a `BREAKING CHANGE:` footer saying what to do.

Write the summary in the imperative, lower case. The body explains the
reasoning, not the diff: what was wrong, why this fix, and what tradeoff it
accepts. One concern per commit. Commits are gpg-signed; if signing times out,
retry rather than disabling it.
