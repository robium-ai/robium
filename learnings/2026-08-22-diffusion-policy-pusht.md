- [none] verified <!-- id: lrn-0822-13 -->
  symptom: The PushT tutorial and demo pages needed real animated and static media without adding heavy page assets or keeping legacy imitation-manipulation thumbnails.
  root-cause: The article still referenced one generic thumbnail, while the useful evidence was split across a long browser recording, a clean policy replay, and two full-resolution screenshots.
  fix: Crop browser chrome, encode seconds 15–24 as an 8 FPS 1100×556 workspace loop and a 10 FPS 512×512 policy loop, use static solved evidence for social metadata, and ingest nested asset directories through the existing article pipeline — check: the 9-second workspace and policy GIFs are 267 KB and 480 KB, `make smoke` rebuilt 27 pages and passed the new hero, social-image, supporting-media, and demo-hero assertions.
  dead-ends: Using the 64-second 120 FPS source recording directly; using an animated GIF as the social image; retaining the legacy imitation-manipulation thumbnail URL on the current demo pages.
  source: supplied screen recording, official replay, and screenshots; local website build, 2026-08-22
