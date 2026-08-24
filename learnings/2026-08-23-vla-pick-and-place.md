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

- [environments] figured-out-from-scratch <!-- id: lrn-0823-11 -->
  symptom: `https://rest.runpod.io/openapi.json` returned the documentation site's HTML with HTTP 200, causing JSON decode failure; the machine-readable schema is at `/v1/openapi.json`.
  root-cause: The REST documentation root and versioned API serve different representations while both answer successfully.
  fix: Fetch `https://rest.runpod.io/v1/openapi.json` and verify `Content-Type: application/json` before parsing — check: the schema exposed Pod GET/POST/DELETE, billing, templates, and network-volume paths used by the paid preflight.
  dead-ends: Falling back only on HTTP failure, because the HTML endpoint returns 200.
  anchors: environments#runpod-verify-before-terminating
  source: RunPod REST endpoints inspected during issue #69 paid preflight.

- [environments] figured-out-from-scratch <!-- id: lrn-0823-12 -->
  symptom: RunPod GraphQL schema introspection returned HTTP 403 while documented concrete `gpuTypes` queries with the same credential succeeded; `myself.clientBalance` also returned 403.
  root-cause: API authorization is field/query-specific, so successful GPU discovery does not imply balance or introspection access.
  fix: Use documented concrete availability queries and fail the paid gate closed when the balance query is forbidden — check: A40 48 GB returned `High`, RTX A6000 48 GB returned `Low`, and no Pod was created because positive balance remained unverifiable.
  dead-ends: Treating general GraphQL authentication as proof that all fields are authorized; inferring remaining credit from historical billing records.
  anchors: environments#runpod-verify-before-terminating
  source: RunPod GraphQL and REST preflight on 2026-08-23.

- huggingface — fired: yes; accurate: yes, it required live revision/license access checks and correctly delegated Hub mechanics; complete: no, its required upstream `hf-cli` skill plugin was unavailable in this session, so the installed official `hf` CLI was used as the documented fallback; lean: yes.
- data — fired: yes; accurate: yes, immutable public evidence versioning matched the approved publication plan; complete: yes for preflight, while upload remained correctly blocked behind paid evaluation; lean: yes.

- [environments] figured-out-from-scratch <!-- id: lrn-0823-13 -->
  symptom: The pinned GPU image failed during `uv sync --extra gpu` while building `egl-probe==1.0.2` with `FileNotFoundError: [Errno 2] No such file or directory: 'cmake'` followed by `RuntimeError: CMake must be installed.`
  root-cause: `hf-libero==0.1.4` pulls `robomimic==0.2.0`, which pulls the source-built `egl-probe`; the lock's Python `cmake` package is not available inside uv's isolated build environment when `egl-probe` runs.
  fix: Install the system `cmake` package in the CUDA builder before the frozen uv sync — check: the Linux/amd64 GPU image completed all 25 BuildKit steps and exported manifest `sha256:96fb679a510e1f2791b640b96a516e10cb497a6116d29ff2435f3cf4315821bc`.
  dead-ends: Assuming the resolved Python `cmake` wheel would be on PATH for an isolated transitive-package build; relying on Cloud Build's default log bucket, which the deployer can submit to but cannot read.
  anchors: environments#local-remote-parity-acceptance-test
  source: issue #69 Cloud Build `30944977-14e9-4dfe-875f-9ac4ab0875ca` and local Linux/amd64 BuildKit reproduction on 2026-08-23.

- [environments] figured-out-from-scratch <!-- id: lrn-0823-14 -->
  symptom: RunPod had funded A40/A6000 capacity and supports direct S3-compatible network-volume preload, but no datacenter simultaneously had stocked A40/A6000 capacity and the S3 volume API; the funded account also had only the general RunPod API key, not the separate S3 key pair.
  root-cause: RunPod's GPU inventory and S3-compatible network-volume endpoint have independent datacenter matrices, and Pod-free volume access uses credentials created separately from `RUNPOD_API_KEY`.
  fix: Before creating billed storage, intersect live per-datacenter GPU stock with the documented S3 datacenter list and verify `RUNPOD_S3_ACCESS_KEY` plus `RUNPOD_S3_SECRET_KEY`; fail closed if the intersection is empty — check: official `runpodctl gpu list` showed the stocked A40/A6000 locations outside the S3 list and `stockStatus: none` for those GPUs in S3-enabled candidate locations, so no volume or Pod was created.
  dead-ends: Choosing `EU-SE-1` from GPU stock alone (no S3 endpoint); choosing `US-MO-1`, `EU-RO-1`, or `US-KS-2` from S3 support alone (allowed GPU stock `none`); preloading through a temporary Pod (violates issue #69's read-only preflight and exactly-one-feasibility-Pod sequence).
  anchors: environments#runpod-verify-before-terminating
  source: RunPod official S3 API datacenter table and authenticated `runpodctl gpu list` on 2026-08-23 during issue #69 Task 4.

- environments — fired: yes; accurate: yes, it required provider-side balance, capacity, and lifecycle verification before allocation; complete: no, the live intersection between S3-enabled volume locations and GPU stock plus the separate S3 credential requirement needed fresh research captured above; lean: yes.
- integration — fired: yes; accurate: yes, immutable image and private-registry boundaries stayed explicit; complete: yes for the resumed image/preflight block; lean: yes.
- lerobot — fired: yes; accurate: yes, the exact checkpoint and processor snapshot remained pinned and offline-loadable by design; complete: yes for the resumed preflight; lean: yes.
- testing — fired: yes; accurate: yes, it kept the paid gate fail-closed on independently verified prerequisites; complete: yes for the resumed preflight; lean: yes.

- [environments] wrong-stale-guidance <!-- id: lrn-0823-15 -->
  symptom: RunPod's published S3 API table listed `US-MO-1`, and live inventory showed L40S 48 GB stock there, but `POST /v1/networkvolumes` failed with `Data center "US-MO-1" not found or does not support network volumes` and returned the currently accepted volume-datacenter list.
  root-cause: S3 endpoint availability, GPU inventory, and the live network-volume provisioning allowlist are three independently changing provider surfaces; intersecting only the first two can select a location that cannot provision storage.
  fix: Before selecting a GPU/volume location, perform a zero-Pod live volume-create capability check or consume the provisioning API's current allowlist, then intersect that result with S3 endpoint support and GPU stock — check: `US-KS-2` accepted volume `68s0bxbv7p` and had A100 SXM 80 GB Secure Cloud stock `Low` at $1.59/hour.
  dead-ends: Selecting `US-MO-1` from the official S3 table plus live L40S stock; assuming the general datacenter inventory implied network-volume provisioning support.
  anchors: environments#runpod-verify-before-terminating
  source: RunPod official S3 documentation, authenticated `runpodctl gpu list`, and live `/v1/networkvolumes` responses on 2026-08-23.

- [environments] figured-out-from-scratch <!-- id: lrn-0823-16 -->
  symptom: Direct upload of the 7,473,096,344-byte Pi0.5 weight to RunPod's S3-compatible volume failed with HTTP 524 using AWS CLI and the official large-file helper at 50 MB/10 MB parts; 5 MB parts completed but measured about 0.24 MB/s, projecting many hours.
  root-cause: The local-to-RunPod S3 path's bandwidth and proxy timeout made large multipart transfer operationally unsuitable even though authentication and small-object uploads worked.
  fix: Measure several parts before committing to the whole transfer, abort every failed multipart session, verify no open uploads remain, and require an explicit design amendment before switching to same-Pod volume bootstrap — check: all three upload IDs were aborted, `list-multipart-uploads` returned `null`, six small files plus `REVISION` remained intact, and no Pod was created.
  dead-ends: AWS CLI retry mode with ten attempts; official helper defaults at 50 MB; 10 MB parts; 5 MB parts as a technically successful but multi-hour path.
  anchors: environments#runpod-verify-before-terminating
  source: RunPod S3 endpoint `US-KS-2`, official `runpod/runpod-s3-examples` helper, and issue #69 preload attempts on 2026-08-23.

- environments — fired: yes; accurate: yes, it kept provider capacity, storage locality, and no-Pod ground truth explicit; complete: no, the three-way datacenter intersection and large-file S3 throughput gate required live discovery captured above; lean: yes.
- lerobot — fired: yes; accurate: yes, the exact checkpoint, required processor files, CUDA floor, and offline-load requirement remained intact while hardware changed; complete: yes for resource selection and snapshot validation; lean: yes.

- [environments] figured-out-from-scratch <!-- id: lrn-0823-17 -->
  symptom: RunPod's live availability surface reported Secure Cloud A100 SXM 80 GB stock `Low` in `US-KS-2`, but the single immediate `POST /v1/pods` request failed with HTTP 500: `create pod: There are no instances currently available`.
  root-cause: A nonzero/`Low` catalog stock indication is advisory and does not reserve capacity or guarantee that an exact Secure Cloud/datacenter/volume allocation will succeed moments later.
  fix: Treat the Pod-create response as the allocation ground truth, persist an attempt record without secrets, re-list Pods after any ambiguous or failed response, and stop the paid gate without a fallback when no Pod ID exists — check: Pods were empty before and after the rejected request, so zero GPU compute was allocated and no deletion was required.
  dead-ends: Retrying immediately (violates the approved one-attempt/no-fallback feasibility gate); interpreting catalog `Low` as reserved capacity; attempting another GPU or datacenter that cannot attach the accepted volume.
  anchors: environments#runpod-verify-before-terminating
  source: authenticated RunPod REST create/list responses during issue #69 Task 5 on 2026-08-23.

- brainstorming — fired: yes; accurate: yes, it preserved the explicitly approved A100-only design and no-fallback boundary; complete: yes for the resumed paid gate; lean: yes.
- environments — fired: yes; accurate: yes, its fail-closed capacity and post-request lifecycle verification prevented duplicate or orphaned Pods; complete: no, catalog stock versus allocation-ground-truth behavior required live discovery captured above; lean: yes.
- integration — fired: yes; accurate: yes, immutable image, private template, volume, and secret boundaries remained intact in the create request; complete: yes for the allocation attempt; lean: yes.
- lerobot — fired: yes; accurate: yes, exact checkpoint bootstrap stayed behind successful allocation and therefore did not run under a false capacity assumption; complete: yes for this blocked gate; lean: yes.
- testing — fired: yes; accurate: yes, the paid feasibility gate failed on provider allocation before runtime checks and later gates remained closed; complete: yes for the observable failure path; lean: yes.

- environments — fired: yes; accurate: yes, its per-datacenter inventory and volume-locality guidance separated same-volume H100 NVL from alternatives requiring a new volume; complete: yes for the read-only RunPod alternative-instance review; lean: yes.
