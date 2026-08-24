- [environments] figured-out-from-scratch <!-- id: lrn-0823-06 -->
  symptom: Issue #69 requires checking tagged RunPod billed usage plus active reserved cost, but the current RunPod `/billing/pods` API returns spend by Pod ID/GPU only and exposes no template, name, tag, or cost-center filter; deleted Pods also disappear from the active Pod list.
  root-cause: The `environments` GPU-cloud reference covers RunPod networking and lifecycle but not the current billing API's ownership-attribution gap for a public per-session budget.
  fix: Design an atomic durable ledger of owned Pod IDs/reservations, reconcile those IDs against `/billing/pods` and active owned Pods, keep the dedicated cost center as operator attribution, and fail closed on any unverifiable input — check: issue #69 design and active architecture brief commit `7283bb0` define the complete algorithm and API evidence was verified from RunPod's OpenAPI schema.
  dead-ends: Filtering the billing API by cost center or template (unsupported); inferring deleted ownership from the active Pod list (deleted Pods are absent); adding a waiting queue database (explicitly prohibited).
  anchors: environments#runpod-verify-before-terminating
  source: RunPod REST OpenAPI `/billing/pods`, `/pods`, and `/pods/{podId}` inspected 2026-08-23 during issue #69 architecture.

- brainstorming — fired: yes; accurate: yes, it correctly classified the cross-repository replacement/provider work as architectural and the issue supplied the prior approval; complete: yes, spec and plan stages were explicit; lean: yes.
- architect — fired: yes; accurate: yes, its brief template and environment-first routing matched the work; complete: yes, all eight required brief sections were filled; lean: yes.
- environments — fired: yes; accurate: yes, doctor and the GPU-cloud exception correctly ruled out local real inference; complete: no, RunPod budget attribution required fresh API research captured above; lean: yes.
- lerobot — fired: yes; accurate: yes for the Pi0.5/LIBERO manipulation path and headless EGL guidance after exact v0.4.4 source verification; complete: yes for architecture; lean: yes.
- integration — fired: yes; accurate: yes, rate/failure-domain guidance kept policy and simulator in process and the orchestrator lifecycle-only; complete: yes for the module/comms plan; lean: yes.

- [test-assets] figured-out-from-scratch <!-- id: lrn-0823-07 -->
  symptom: The public HuggingFaceVLA/libero dataset uses a global task index 10 for `put the bowl on the plate`, while the live benchmark selector is zero-based LIBERO-Goal task ID 8; selecting fixture rows by the live task ID would source the wrong task.
  root-cause: Dataset-global task indexing and per-suite LIBERO task indexing are distinct namespaces, and the fixture workflow required joining `meta/tasks.parquet` to `meta/episodes` before querying datasets-server rows.
  fix: Pin the dataset revision, resolve the prompt to global task index 10 from `meta/tasks.parquet`, select official episode offsets from `meta/episodes`, then fetch and hash rows 101469, 107174, and 107606 — check: all three returned task index 10, decoded as nonblank 256×256 JPEGs, and pass the fake rollout suite.
  dead-ends: Reusing live task ID 8 as the dataset-global task index; reading parquet with system Python, which lacked pyarrow (`ModuleNotFoundError: No module named 'pyarrow'`).
  anchors: test-assets#provenance-manifest
  source: HuggingFaceVLA/libero revision 86958911c0f959db2bbbdb107eb3e17c5f9c798e metadata and datasets-server rows.

- [environments] figured-out-from-scratch <!-- id: lrn-0823-08 -->
  symptom: The pinned CPU image failed at `uv sync --frozen --no-dev --no-extra --no-install-project` with `a value is required for '--no-extra <NO_EXTRA>'` under uv 0.11.29.
  root-cause: `--no-extra` excludes one named extra; base dependencies are already the default when no `--extra` flag is supplied.
  fix: Use `uv sync --frozen --no-dev --no-install-project` for the dependency layer and `uv sync --frozen --no-dev` after copying source — check: Linux/amd64 image `sha256:43c6d3ba714eb2b70930e41cfdcd52ca0796b3247b44c182a9ed36e6f93c9306` built and passed the protected container lifecycle.
  dead-ends: Treating `--no-extra` as a valueless boolean equivalent to “install no extras.”
  anchors: environments#uv-lock-sync
  source: uv 0.11.29 CLI error and the passing issue #69 CPU image build.

- [integration] figured-out-from-scratch <!-- id: lrn-0823-09 -->
  symptom: The exact LeRobot v0.4.4 GPU dependency could not resolve beside Gradio 6.20.0 because LeRobot requires `huggingface-hub<0.36` while Gradio 6.20 requires `huggingface-hub>=1.2`; Gradio 5.49.1 then conflicted with Pillow 12 because it requires Pillow <12.
  root-cause: The app's UI and real-policy extras share one lock, so their transitive Hugging Face Hub and Pillow bounds must intersect even though the GPU extra is not installed locally.
  fix: Pin Gradio 5.49.1 and Pillow 11.3.0, keeping LeRobot at commit 8fff0fde; the resolved lock pins 203 packages and base-only clean sync passes — check: `uv lock`, isolated `uv sync --frozen`, 14 tests, and the Linux/amd64 image all passed.
  dead-ends: Gradio 6.20.0 with LeRobot v0.4.4; Pillow 12.3.0 with Gradio 5.49.1.
  anchors: integration#dependency-boundaries
  source: uv solver output from issue #69 implementation.

- [none] figured-out-from-scratch <!-- id: lrn-0823-10 -->
  symptom: Gradio 5.49 treated `lambda: stream_rollout(...)` as a scalar callback and failed with `function didn't return enough output values (needed: 2, returned: 1)` because the one value was a generator object.
  root-cause: Gradio detects streaming from the callback function itself; a regular lambda returning a generator is not recognized as a generator function.
  fix: Register a named generator callback containing `yield from stream_rollout(...)` — check: `gradio_client` invoked `/run_rollout` through the Linux/amd64 container and received five nonblank frames plus simulator success, with regression coverage in `tests/test_ui.py`.
  dead-ends: Returning the generator object from a lambda.
  source: issue #69 CPU/fake container Gradio lifecycle.

- testing — fired: yes; accurate: yes, its test-first and boundary guidance produced the expected failing import gate before implementation and covered lock/cancellation/evidence/security; complete: yes, local, clean-environment, and real container UI paths were all exercised; lean: yes.
- test-assets — fired: yes; accurate: yes, its provenance-manifest and compact-fixture rules produced three immutable official frames; complete: no, it did not call out dataset-global versus suite-local task indexing, captured above; lean: yes.
- environments — fired: yes; accurate: yes, the uv-first local environment and pinned Docker path reproduced; complete: no, exact uv extra syntax needed runtime verification, captured above; lean: yes.
- lerobot — fired: yes; accurate: yes, official Pi0.5 preprocessing, fixed-state LIBERO mechanics, EGL, and action chunking matched pinned source; complete: yes at the free gate, with real CUDA load intentionally deferred; lean: yes.
- integration — fired: yes; accurate: yes, one-process rollout and capability-scoped gateway boundaries passed; complete: no, cross-version Gradio/LeRobot lock compatibility required solver-driven pinning, captured above; lean: yes.
