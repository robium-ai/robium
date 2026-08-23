## fall back to direct image rendering when an embedded Rerun viewer stays black <!-- id: obs-rerun-001 -->
status: ready
proof: 1
signal: verified
sources: [lrn-0817-12]
target: rerun#gradio-rerun-embed (update) — add a measured fallback boundary: keep Rerun for valid offline recordings, but render critical live camera frames directly when the embedded component receives valid data and still shows a black canvas
evidence: both initial-path and streamed-byte Gradio integrations produced a black canvas while valid RRF2 data and successful chunk fetches were observed ✓ · direct gr.Image camera rendering plus offline Rerun recordings passed browser and demo-smoke checks ✓ · retrying the Path and byte-stream embedding shapes was ruled out after transport, viewer initialization, and recording validity were verified ✓
