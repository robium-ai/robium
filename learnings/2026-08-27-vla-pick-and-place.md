- [live-demo] user-correction <!-- id: lrn-0827-01 -->
  symptom: The VLA demo page, article, reference-app README, and live workspace used a different visual theme and a denser operational writing style than the ACT ALOHA, Diffusion Policy, and Robot Navigation references.
  root-cause: The VLA surfaces were published as evidence and lifecycle status accumulated during production hardening, without a final cross-demo editorial and theme pass.
  fix: Reorganized the public story as try → run locally → understand → inspect evidence, aligned the live workspace with the shared dark policy-demo treatment, and preserved all measured claims — check: website build, 48 app tests, 50 orchestrator tests, and desktop/mobile browser bounds passed.
  dead-ends: A CSS-only recolor would have left the three-way landing hierarchy, short result-note article, and deployment-first README inconsistent.
  anchors: live-demo#demo-link-from-proof-card, live-demo#honest-cold-boot-copy-on-page

## End-of-block retro — cross-demo theme and editorial alignment

- live-demo — fired: yes; accurate: yes for treating the demo as a complete product surface, keeping measured proof beside the live path, and preserving honest lifecycle states; complete: partial because the skill covers page anatomy but not cross-demo visual/editorial consistency; lean: yes.

- [live-demo] user-correction <!-- id: lrn-0827-02 -->
  symptom: Public VLA copy led with “Measured policy evidence,” suite averages, acceptance targets, states/seeds, rollouts, and checksums; the user said it felt too benchmark-heavy for a Hackaday or Hacker News reader.
  root-cause: Reproducibility details escaped their supporting role and became the headline story across the demo, live sidebar, and article.
  fix: Reframed the story around one instruction, the robot's visible behavior, the slow first start, and how to try it; moved the exact run archive to a short final section — check: website smoke locks the approachable copy and rejects the old benchmark phrases on the demo page.
  dead-ends: Merely replacing “evidence” with a friendlier synonym would have preserved the same expert-first information hierarchy.
  anchors: live-demo#demo-link-from-proof-card, live-demo#honest-cold-boot-copy-on-page

## End-of-block retro — approachable VLA story

- live-demo — fired: yes; accurate: yes for honest startup, keeping saved attempts available, and making the live path the primary invitation; complete: partial because it does not guide audience-level editorial voice or jargon budgets; lean: yes.

- [live-demo] user-correction <!-- id: lrn-0827-03 -->
  symptom: Removing benchmark jargon overcorrected into a beginner-first maker story; the user wanted technical depth comparable to the other articles, focused on models, architecture, and engineering challenges rather than scores.
  root-cause: Audience simplification removed both unnecessary scorekeeping and useful system-level detail instead of separating them.
  fix: Added VLA-versus-ACT/Diffusion guidance, the Pi0.5/LIBERO adapter, pinned runtime, CUDA/EGL and model staging, compiled-versus-eager inference, session isolation, cancellation, and diagnostics; removed first-person voice — check: site smoke asserts model comparison, engineering depth, and live architecture.
  dead-ends: A general-interest narrative alone did not match the established technical tutorial series.
  anchors: live-demo#demo-link-from-proof-card, live-demo#one-visitor-one-instance-gateway-enforced, live-demo#honest-cold-boot-copy-on-page

## End-of-block retro — technical voice without benchmark emphasis

- live-demo — fired: yes; accurate: yes for the per-visitor lifecycle, direct application handoff, cancellation boundaries, and honest cold start; complete: partial because model-selection and article voice required comparison against the sibling technical tutorials; lean: yes.
