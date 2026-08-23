- [lerobot] better-method <!-- id: lrn-0823-01 -->
  symptom: The official LeRobot ACT ALOHA checkpoints contain `config.json` and weights but no processor-pipeline files, while the current eval path requires those files.
  root-cause: The checkpoints predate LeRobot 0.6's processor-pipeline format.
  fix: Current LeRobot ships `src/lerobot/processor/migrate_policy_normalization.py`, and its loader detects legacy checkpoints and emits that migration command; design the app around a pinned, verified upstream migration rather than classifying every pre-0.6 checkpoint as permanently unloadable — check: LeRobot 0.6.1 was PyPI-verified and the current `factory.py`/`pipeline.py` paths were fetched directly on 2026-08-23; execution verification remains the first implementation gate.
  dead-ends: Retraining solely to obtain processor files; generating normalization from an unrelated current dataset; assuming a model-repository config migration also created processor pipelines.
  anchors: lerobot#pre-06-checkpoints-unloadable
  source: official LeRobot model repositories, PyPI API, and current LeRobot source, 2026-08-23

- [lerobot] figured-out-from-scratch <!-- id: lrn-0823-02 -->
  symptom: The official ALOHA Insertion model card reports 20.6% success, but its current `eval_info.json` returns the same 83% aggregate values and 500-episode structure as Transfer Cube.
  root-cause: The Insertion repository appears to contain a copied or stale evaluation artifact; the repository does not provide internally consistent benchmark evidence.
  fix: Exclude Insertion from the first ACT reference app and treat the model-card number as unverified until upstream reconciles the artifact — check: both raw model cards and both raw evaluation JSON files were compared directly on 2026-08-23.
  dead-ends: Presenting Insertion as a trustworthy side-by-side checkpoint comparison; using its JSON aggregate without checking the task-specific model card.
  source: `lerobot/act_aloha_sim_transfer_cube_human` and `lerobot/act_aloha_sim_insertion_human`, 2026-08-23

- [architect] verified <!-- id: lrn-0823-03 -->
  symptom: A new ACT reference app needed a stack and donor choice that remained viable on the maintainer's Mac and in the existing hosted-demo architecture.
  root-cause: ALOHA is a bimanual MuJoCo simulation with an older checkpoint format, so choosing it from reputation alone would leave environment and compatibility assumptions implicit.
  fix: Select official ACT ALOHA Transfer Cube, bootstrap the operator/demo/test shape from `diffusion-policy-pusht`, choose native uv plus a separate CPU image, and record migration, MPS, success-semantics, seed, and CPU-latency risks in the canonical architecture brief — check: `npx robium-ai doctor --json` passed Apple MPS, Docker, disk, and uv checks; the brief was self-reviewed and committed as `f37942e`.
  dead-ends: Reusing PushT for a second policy demo; choosing Isaac Sim without a task requirement or NVIDIA host; scaffolding before checking `REGISTRY.md`.
  anchors: architect#always-produce-brief, architect#env-first-route-environments, architect#bootstrap-first-scaffold, architect#state-open-risks-explicitly
  source: approved architecture design and local preflight, 2026-08-23

## End-of-block retro

- architect — fired: yes; accurate: yes, especially bootstrap-first and explicit-risk guidance; complete: yes for selection and the architecture brief; lean: yes.
- lerobot — fired: yes; accurate: partial, it correctly identified the legacy processor incompatibility but its blanket unloadable guidance has been overtaken by the current official migration tool; complete: partial until the pinned ACT migration and rollout execute; lean: yes.
- data — fired: yes; accurate: yes, offline-first and embodiment matching led directly to the official ALOHA model/dataset pair; complete: yes for a no-training MVP; lean: yes.
- environments — fired: yes; accurate: yes, the doctor preflight confirmed native uv/MPS plus a separate CPU container as the correct split; complete: yes for design, pending measured parity; lean: yes.
