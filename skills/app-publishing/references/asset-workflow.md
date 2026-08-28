# Article asset workflow

## Standard set

Each published app should carry:

1. A real-result hero, either a still or a short motion capture.
2. Alt text that describes the visible frame.
3. A caption that states why it matters and whether it is simulated, recorded,
   or live.
4. A 1200 by 630 social card composed from real project imagery.
5. One system diagram showing the main data or control path.
6. Optional short motion when movement communicates more than a still.

Use app-relative paths and keep media with the application. Suggested folders
are `assets/gifs/`, `assets/stills/`, `assets/diagrams/`, and `assets/social/`.
Canonical run archives may remain under `evidence/`; the article can reference
their curated previews without copying the underlying result records.

## Real-run capture

- Capture the smallest sequence that shows the claimed behavior.
- Remove idle frames when that does not hide startup or latency being discussed.
- Preserve readable controls, axes, units, and timestamps when relevant.
- Keep the original run record or sidecar metadata when the application already
  produces one.
- Never repaint a failure into a success or use generated frames to fill gaps.

## System diagrams

Use code-native SVG for architecture and data flow. Apply the publication
tokens, Inter labels, mono identifiers, square boxes, cobalt arrows, and flat
borders. Keep the diagram to the components needed to understand the article.
Do not turn a complete dependency graph into a hero image.

## Social cards

Use a 1200 by 630 canvas. Place a real application frame on roughly three
fifths of the card and a paper panel on the remaining area. The panel contains
“robium / applications,” a short project headline, and one compact descriptor.
Use cobalt for one rule or label. Do not add performance claims to the card.

## Optional conceptual illustration

Use generated art only when a real capture or system diagram cannot explain the
idea. Save it under a new filename such as `concept-v1.png`; never overwrite a
capture.

Prompt recipe:

```text
Use case: stylized-concept
Asset type: Robium application article illustration
Primary request: <the single concept to explain>
Scene/backdrop: clean editorial field with generous negative space
Subject: <conceptual subject, not a literal robot run>
Style/medium: restrained technical editorial illustration, flat and tactile
Composition/framing: wide article composition with one clear focal idea
Color palette: paper #EDEFEE, ink #101719, cobalt #2563EB, small muted accents
Constraints: no UI screenshot, no performance numbers, no logos, no watermark,
  no claim that this depicts a real run
Avoid: glossy 3D marketing art, neon gradients, fake dashboards, tiny text
```

Caption it as a conceptual illustration. If the result looks like application
output, discard it and use a diagram or real capture.
