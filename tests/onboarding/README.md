# Onboarding routing probes

These opt-in probes exercise native skill discovery and instruction loading in
fresh temporary directories outside the Robium checkout. They use your existing
host login and default model, consuming account usage. They do not install a
plugin globally, start simulations, train models, or authorize paid robot APIs.

```sh
node tests/onboarding/run.mjs claude
node tests/onboarding/run.mjs codex
# Or a bounded subset:
node tests/onboarding/run.mjs claude navigation navigation-first maintenance
```

Claude loads the local plugin with `--plugin-dir`, read-only tools, no hooks,
and no MCP servers. Restricted file access permits the temporary workspace,
plugin source, and sibling apps checkout, not obsolete skills in user caches.
The sibling `robium-apps` checkout must be present for these probes.
Codex loads the source skills through a temporary native
`.agents/skills` link with a read-only sandbox and user configuration excluded.
The latter validates the skills, not Codex's installed plugin cache or global
installation. Neither substitutes for a fresh Ubuntu installation/bring-up.

`cases.json` preserves the three homepage prompts plus a domain-first entry,
maintenance, incompatible prerequisites, and an explicit from-scratch request.
It also probes try-only, whole-app adaptation, selective component reuse, and
a minimal fresh app. Review whether the starting path is surfaced before deep
research, and whether the first visible result stays proportional to the ask.
When homepage wording changes, update these cases and architect's trigger cases.

The runner prints the temporary transcript directory. Review each transcript
against its case's `review` rubric. A zero exit means the host completed, **not**
that behavior passed. Check actual Skill/Read calls, not just a promise to load
architect later. A domain skill may legitimately load first if it reaches the
reference-selection instructions before proposing new infrastructure. Check
the chosen app, reuse plan, constraints, and absence of unnecessary onboarding
in maintenance. Repeat passing cases before judging reliability; a single
pass is not a routing guarantee.

The read-only boundary lets the model inspect skills but deliberately prevents
full setup. Record denied tools or missing workspace state as probe limitations,
not simulator failures or evidence that a baseline ran successfully.
