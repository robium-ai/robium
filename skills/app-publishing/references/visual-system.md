# Robium publication visual system

## Canonical tokens

### Editorial light

| Role | Value |
| --- | --- |
| Paper | `#EDEFEE` |
| Paper deep | `#E5E9E8` |
| Tint | `#E8ECEB` |
| Panel | `#E0E6E5` |
| Border | `#D1D8D7` |
| Border strong | `#ADBAB9` |
| Ink | `#101719` |
| Ink secondary | `#3B494C` |
| Muted | `#718083` |
| Cobalt | `#2563EB` |
| Cobalt ink | `#1D4ED8` |
| Cobalt soft | `#DFE9FF` |

### Working dark

| Role | Value |
| --- | --- |
| Canvas | `#090C12` |
| Surface | `#11131A` |
| Panel | `#161922` |
| Text | `#F7F8FA` |
| Text secondary | `#AAB1BF` |
| Bright cobalt | `#4C8DFF` |

Status colors are restrained: stable `#047857` on light and `#4ADE80` on
dark; experimental `#A65308` on light and `#FB923C` on dark. Error treatment
uses dark red only for an active failure, not as decoration.

## Type and shape

- Inter: headings, body, buttons, and explanatory interface copy.
- System mono: metadata, controls, compact labels, commands, and code.
- Geist Mono: skill names, versions, and knowledge identifiers.
- Aldrich: the lowercase Robium wordmark only.
- Corners: square or 2px. A circle is reserved for status dots and avatars.
- Surfaces: flat border, no drop shadow, no decorative gradient.

## Page modes

Overview and guide use the editorial light tokens. Live workspaces use the
working dark tokens. Both modes retain cobalt actions, the same type roles,
compact mono metadata, project navigation, and status vocabulary.

The guide owns the page H1. Its project context is a compact header with the
app name, status, source link, and Overview / Live / Guide navigation. The
overview may use the full project title as its H1.

## Reusable component language

- Project identity: owner, app name, one-sentence outcome, status, source.
- Project tabs: Overview, Live, Guide in that order.
- Real-run hero: edge-to-edge media inside a flat border, followed by a short
  caption.
- Choice cards: Try live and Run locally, with concrete availability.
- Article callouts: “What happened,” “Why we chose this,” and “Limits.”
- Live states: Ready, Starting, Reconnecting, Busy, Unavailable, Failed.

Keep embedded viewer styling isolated. The project shell can frame Gradio,
Foxglove, Lichtblick, or another viewer, but it should not restyle the tool's
internal interface.
