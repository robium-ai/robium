- [environments] figured-out-from-scratch <!-- id: lrn-0824-01 -->
  symptom: RunPod's current S3 documentation listed `US-MD-1`, and authenticated inventory reported Secure Cloud A100 SXM 80 GB stock there, but `POST /v1/networkvolumes` for a 20 GB volume returned HTTP 500 with no volume ID.
  root-cause: Published S3 endpoint presence and GPU inventory still do not prove that the live network-volume provisioning API will accept a create request in that datacenter.
  fix: Treat successful volume creation plus a subsequent authoritative list response as the provisioning gate; after any ambiguous 5xx, list volumes and Pods before deciding whether cleanup or retry is safe — check: the post-failure lists contained only the existing `US-KS-2` volume and zero Pods, so the paid-compute gate stopped without an orphaned resource.
  dead-ends: Inferring volume provisioning from the published S3 table; inferring it from per-datacenter GPU stock; automatically retrying an ambiguous create response without an idempotency key.
  anchors: environments#runpod-verify-before-terminating
  source: RunPod official S3 documentation, authenticated CLI inventory, and REST network-volume/Pod responses during issue #69 on 2026-08-24.

- brainstorming — fired: yes; accurate: yes, it classified the datacenter/volume move as a bounded amendment and enforced design approval before infrastructure mutation; complete: yes; lean: yes.
- architect — fired: yes; accurate: yes, it kept the living architecture brief synchronized with the approved US-MD-1 change and its open risk; complete: yes; lean: yes.
- environments — fired: yes; accurate: yes, it required live provider ground truth and stopped before compute when colocated storage failed; complete: no, S3 endpoint publication versus actual volume provisioning required live discovery captured above; lean: yes.

- environments — fired: yes; accurate: yes, its storage-locality and fail-closed guidance narrowed recovery to waiting for A100 beside the proven volume, a provider-side volume fix, or an explicitly approved hardware amendment; complete: yes for recovery planning; lean: yes.

- [environments] figured-out-from-scratch (seen 2x) <!-- id: lrn-0824-02 -->
  symptom: Authenticated RunPod inventory showed H100 NVL 94 GB stock `Low` in `US-KS-2` during alternative selection, but the final paid preflight later reported `stockStatus: none`; no Pod request could safely be made.
  root-cause: RunPod catalog availability is both advisory and highly transient: `Low` can disappear entirely between design approval and the create gate, just as an earlier `Low` A100 indication failed at allocation.
  fix: Re-query the exact GPU/datacenter immediately before every one-shot paid request and stop before create when stock is `none` — check: the final preflight reported zero Pods, zero current-day Pod billing records, and no GPU allocation.
  dead-ends: Treating the earlier `Low` reading as reserved capacity; sending a create request after the exact inventory changed to `none`; silently selecting another GPU.
  anchors: environments#runpod-verify-before-terminating
  source: authenticated RunPod CLI and REST preflight during issue #69 on 2026-08-24; recurrence of lrn-0823-17.

- brainstorming — fired: yes; accurate: yes, it treated H100 as a bounded, explicitly approved hardware amendment before implementation; complete: yes; lean: yes.
- architect — fired: yes; accurate: yes, it synchronized the active brief, design, plan, and historical evidence before the hardware gate; complete: yes; lean: yes.
- environments — fired: yes; accurate: yes, it required an immediate exact-stock recheck and stopped before compute when H100 changed to unavailable; complete: no, the speed of `Low`-to-`none` inventory drift required repeated live evidence captured above; lean: yes.
- lerobot — fired: yes; accurate: yes, it preserved the exact checkpoint, processor files, CUDA-only runtime, and same-Pod offline-load path while only the GPU changed; complete: yes for preflight; lean: yes.
- testing — fired: yes; accurate: yes, the H100 evidence constant was changed red-green and the full 17-test plus fake-smoke gate passed before paid preflight; complete: yes; lean: yes.

- [lerobot] better-method <!-- id: lrn-0824-03 -->
  symptom: The feasibility design kept targeting 80–94 GB A100/H100 hardware and repeatedly stalled on scarce RunPod capacity, even though the application performs Pi0.5 inference at batch size 1 rather than optimizer-backed training.
  root-cause: The 24–40 GB guidance consulted during planning describes batch-8 AdamW training and was conservatively treated as an inference floor; storage locality then reinforced the oversized GPU choice before the exact checkpoint memory was derived.
  fix: Size inference from the pinned artifact and workload first: the Hub metadata reports 3,497,036,912 BF16 plus 119,720,608 F32 parameters (7,473,096,344 weight bytes), the app uses batch 1, and upstream OpenPI documents inference above 8 GB. Use a one-episode 24–32 GB feasibility run to measure peak allocation before selecting production capacity — check: authenticated RunPod inventory found a 32 GB RTX PRO 4500 at Medium stock and 24 GB RTX 4090 at Low stock; the actual CUDA peak remains unverified until the paid smoke is approved and run.
  dead-ends: Applying fine-tuning VRAM guidance to inference; treating more VRAM as intrinsically safer when it makes allocation unlikely; requiring durable regional checkpoint storage before measuring whether the model loads and completes one inference rollout.
  anchors: lerobot#gpu-mps-cpu-training-speed, environments#runpod-verify-before-terminating
  source: pinned Hugging Face checkpoint API, pinned app configuration/source, upstream Physical Intelligence OpenPI requirements, and authenticated RunPod inventory during issue #69 on 2026-08-24.

- brainstorming — fired: yes; accurate: yes, it kept the resource search read-only and separated the inference-memory question from the durable-storage design; complete: yes; lean: yes.
- environments — fired: yes; accurate: yes, it required authenticated current stock plus exact runtime compatibility before recommending a cheaper GPU; complete: yes; lean: yes.
- lerobot — fired: yes; accurate: yes for exact checkpoint/runtime inspection; complete: no, its compute-sizing table is training-oriented and did not explicitly distinguish batch-1 Pi0.5 inference, captured above; lean: yes.

- environments — fired: yes; accurate: yes, its authenticated provider-ground-truth rule produced a current US-only comparison and identified the one candidate colocated with the existing checkpoint volume; complete: yes; lean: yes.

- [environments] figured-out-from-scratch <!-- id: lrn-0824-04 -->
  symptom: The approved RunPod Pod allocated and extracted the immutable image, but the application restarted before its first CUDA check with `KeyError: 'getpwuid(): uid not found: 65532'` from PyTorch Inductor via `getpass.getuser()`.
  root-cause: Both runtime stages declared numeric `USER 65532:65532` without creating a matching passwd/group entry or setting a writable home.
  fix: Create a non-login `robium` user/group at UID/GID 65532 in both runtime stages and set `HOME=/tmp`, `USER=robium`, and `LOGNAME=robium` — check: the old image's `getent passwd 65532` exited 2; the rebuilt image resolved the user and Python identity, all 17 tests and fake smoke passed, the protected container lifecycle passed, and the same creation command succeeded on the pinned CUDA runtime base.
  dead-ends: Assuming a numeric Docker `USER` is sufficient for Python/ML libraries; investigating GPU compatibility before resolving the pre-CUDA traceback.
  anchors: environments#local-remote-parity-acceptance-test
  source: RunPod Pod `1m8xyqandczzdb` logs and local container regression during issue #69 on 2026-08-24.

- [environments] figured-out-from-scratch <!-- id: lrn-0824-05 -->
  symptom: An authenticated RunPod Pod-detail diagnostic returned injected environment values, including the Hub credential, in command output while diagnosing the startup failure.
  root-cause: Full provider resource objects are unsafe diagnostic output when deployment secrets are materialized as Pod environment variables.
  fix: Query and record only an explicit safe-field allowlist for Pod diagnostics, remove transient response/capability files immediately, and rotate any credential exposed to logs before reuse — check: the Pod was deleted, the sensitive temporary files were absent after cleanup, and credential rotation remains a required gate before another attempt.
  dead-ends: Treating an authenticated infrastructure `get` response as metadata-only; printing the complete Pod object during troubleshooting.
  anchors: environments#runpod-verify-before-terminating
  source: authenticated RunPod Pod-detail response and cleanup checks during issue #69 on 2026-08-24.

- [environments] figured-out-from-scratch <!-- id: lrn-0824-06 -->
  symptom: The create request supplied a compatibility-first command override, but the returned Pod details did not show the override and the image's gateway entrypoint ran directly.
  root-cause: The chosen RunPod template/create path did not apply the request-time Docker arguments as expected.
  fix: Bake compatibility-first startup behavior into the reviewed immutable image/template rather than depending on a per-request override — check: pending a corrected GPU image build and separately approved one-shot retry.
  dead-ends: Assuming create-time Docker arguments override a template/image entrypoint without verifying the resulting Pod specification.
  anchors: environments#runpod-verify-before-terminating
  source: RunPod create response, Pod details, and application logs during issue #69 on 2026-08-24.

- brainstorming — fired: yes; accurate: yes, it constrained the RTX PRO 4500 change to the approved one-shot feasibility scope; complete: yes; lean: yes.
- architect — fired: yes; accurate: yes, it preserved the issue-authorized production hardware and disabled state while documenting the feasibility amendment; complete: yes; lean: yes.
- environments — fired: yes; accurate: yes, it enforced exact-stock, funding, locality, immutable-image, lifetime, deletion, and zero-Pod checks; complete: no, numeric-user and provider-secret-output hazards required live discovery captured above; lean: yes.
- lerobot — fired: yes; accurate: yes, it preserved the exact checkpoint revision, processor set, offline-load requirement, and batch-one workload; complete: yes for the work reached before CUDA; lean: yes.
- testing — fired: yes; accurate: yes, it required a reproducible red check and full free regression after the runtime-user fix; complete: yes; lean: yes.

- [environments] figured-out-from-scratch <!-- id: lrn-0824-07 -->
  symptom: RunPod's authenticated GPU inventory and datacenter output identified `NVIDIA RTX PRO 4500 Blackwell Server Edition`, while the current REST Pod-create OpenAPI enum exposed only `NVIDIA RTX PRO 4500 Blackwell`; direct REST submissions returned HTTP 400 and no Pod ID.
  root-cause: RunPod's inventory ID and Pod-create schema use different aliases for the same RTX PRO 4500 Server Edition hardware.
  fix: Confirm zero Pods after each rejected request and use the current official `runpodctl pod create`, which maps the inventory ID into the provider's accepted request — check: the CLI created one Pod whose allocated device reported `NVIDIA RTX PRO 4500 Blackwell Server Edition`; no fallback GPU or duplicate running Pod existed.
  dead-ends: Sending the inventory ID directly through REST; substituting the shorter OpenAPI enum directly without provider-side alias handling.
  anchors: environments#runpod-verify-before-terminating
  source: RunPod v2.8.0 CLI inventory/create, current REST OpenAPI, HTTP 400 responses, and successful Pod `bzu8hoikhpaxzz` during issue #69 on 2026-08-24.

- [environments] figured-out-from-scratch <!-- id: lrn-0824-08 -->
  symptom: For the entire bounded attempt, RunPod's Pod surfaces reported `runtime: null`, uptime zero, no public IP, and no port mapping, yet the attached volume showed a successful CUDA preflight, a complete 7,473,096,344-byte model, and the exact revision marker written after hash validation.
  root-cause: RunPod control-plane runtime/readiness fields can lag or disagree with actual container execution and durable network-volume side effects.
  fix: Treat control-plane status as one signal, and independently poll expected durable evidence markers or application health before classifying a Pod as pre-runtime — check: S3 timestamps proved model write at `16:18:00Z`, revision marker at `16:18:32Z`, and CUDA evidence rewritten at `16:33:21Z` while the API still reported no runtime.
  dead-ends: Inferring that the image was still pulling solely from `runtime: null`; waiting only for port mapping before checking durable evidence.
  anchors: environments#runpod-verify-before-terminating, environments#local-remote-parity-acceptance-test
  source: RunPod REST/CLI safe-field responses and authenticated network-volume S3 objects from Pod `bzu8hoikhpaxzz` during issue #69 on 2026-08-24.

- [environments] figured-out-from-scratch <!-- id: lrn-0824-09 -->
  symptom: The documented v2 Pod-log endpoint returned HTTP 403 to the same account credential that could create, inspect, bill, and delete the Pod, leaving the post-bootstrap restart cause unavailable.
  root-cause: Pod-log authorization is not guaranteed by general Pod API authorization for this account/path, despite the provider source guidance describing the same key.
  fix: Make persisted phase/error markers part of the application evidence contract and verify log access during preflight; fail the diagnosis as unknown when neither provider logs nor an application error marker exists — check: CUDA and checkpoint phase markers survived, but no measured episode/error marker existed, so OOM versus application/library failure was not claimed.
  dead-ends: Assuming control-plane access implies v2 log access; classifying the restart as OOM from absence of `feasibility.json`.
  anchors: environments#runpod-verify-before-terminating
  source: authenticated HTTP 403 from `v2-rest.runpod.io/v2/pods/bzu8hoikhpaxzz/logs` and persisted S3 evidence during issue #69 on 2026-08-24.

- [lerobot] verified <!-- id: lrn-0824-10 -->
  symptom: Blackwell/CUDA and exact Pi0.5 checkpoint bootstrap needed real paid verification before model inference could be claimed.
  fix: Run compatibility before download and persist exact device/runtime/tensor evidence, then write the checkpoint revision only after required files, byte size, and SHA-256 pass — check: RTX PRO 4500 SE reported driver `580.178.04`, PyTorch `2.10.0+cu128`, CUDA `12.8`, compute capability `12.0`, `sm_120`, tensor result `6.0`; the 7,473,096,344-byte model and exact revision marker persisted. The measured model episode remains unverified.
  dead-ends: Applying the first container's pre-CUDA UID failure to GPU compatibility; claiming end-to-end model success from checkpoint bootstrap alone.
  anchors: lerobot#gpu-mps-cpu-training-speed
  source: persisted CUDA/checkpoint objects from RunPod Pod `bzu8hoikhpaxzz` during issue #69 on 2026-08-24.

- [environments] user-correction <!-- id: lrn-0824-11 -->
  symptom: The agent made Hub-token rotation a prerequisite after a diagnostic exposed an injected environment value; the operator explicitly said to continue without rotation for this bounded attempt.
  root-cause: The security recommendation was valid, but it was elevated into a mandatory infrastructure blocker beyond the operator's accepted risk decision.
  fix: Record the accepted exception, avoid printing full secret-bearing Pod objects, keep credentials in process memory, and continue only the already bounded feasibility scope — check: subsequent diagnostics emitted safe-field allowlists, transient secret/capability files were not used, and production remained disabled.
  dead-ends: Repeating token rotation as a hard blocker after the operator explicitly accepted the risk; weakening unrelated lifetime, funding, or production gates.
  anchors: environments#runpod-verify-before-terminating
  source: operator correction and the corrected RunPod retry workflow during issue #69 on 2026-08-24.

- brainstorming — fired: yes; accurate: yes, it kept each startup correction inside the approved single-Pod design and preserved production disablement; complete: yes; lean: yes.
- architect — fired: yes; accurate: yes, the living brief now reflects compatibility-first bootstrap and same-Pod measured-to-gateway sequencing; complete: yes; lean: yes.
- environments — fired: yes; accurate: yes for immutable image, funding, volume locality, exact inventory, lifetime, and deletion gates; complete: no, provider alias drift, misleading runtime fields, and log authorization required live discovery captured above; lean: yes.
- lerobot — fired: yes; accurate: yes for exact revision, token-free offline child, and CUDA-only load boundary; complete: no, the post-bootstrap model-load failure remains undiagnosed without logs; lean: yes.
- testing — fired: yes; accurate: yes, startup ordering and same-Pod transition were developed red-green and the full 20-test/fake-smoke suite passed; complete: yes for free gates; lean: yes.

- [testing] better-method <!-- id: lrn-0824-12 -->
  symptom: A restart-safe diagnostics test failed because an existing `failure.json` caused the outer feasibility launcher to preserve stale evidence instead of recording the current subprocess failure (`assert "current failure" in failure` saw only `{"message": "stale failure"}`).
  root-cause: Testing only for file existence cannot distinguish a child-process failure written during the current attempt from a marker left by a previous container restart.
  fix: Snapshot the failure-marker bytes before startup and preserve the child marker only when its contents change; otherwise atomically replace it with the current outer failure — check: the regression failed before the change, then all 26 tests, doctor, fake smoke, and the rebuilt protected Linux/amd64 container lifecycle passed.
  dead-ends: Never overwriting any existing failure marker; unconditionally overwriting the child's more precise `model_loading` failure with the generic outer subprocess exception; deleting prior evidence at startup.
  anchors: testing#test-at-right-layer-not-everything-in-sim, testing#gate-paid-remote-run-behind-free-dry-run
  source: issue #69 persistent startup diagnostics red-green tests on 2026-08-24.

- brainstorming — fired: yes; accurate: yes, it classified the diagnostics change as bounded and the previously approved phase/failure design was sufficient to proceed without expanding the architecture; complete: yes; lean: yes.
- testing — fired: yes; accurate: yes, it put atomicity, redaction, exact failure stage, stale-marker replacement, full fake rollout, and container lifecycle at the free test layers before any paid image build; complete: yes; lean: yes.

- [environments] figured-out-from-scratch <!-- id: lrn-0824-13 -->
  symptom: The diagnostics-enabled RunPod retry passed CUDA and reached `model_loading`, then persisted `EOFError: EOF when reading a line` before producing an episode.
  root-cause: At the pinned revision, LIBERO's first import creates a config file when none exists and calls `input()` to ask whether the dataset path should be customized; the headless container has closed stdin.
  fix: Bake a deterministic config into the GPU image, set `LIBERO_CONFIG_PATH=/app/libero-config`, and point every LIBERO resource at the exact `/opt/libero` checkout — check: the container-contract test failed before the copy/env contract was added; afterward all 27 tests and fake smoke passed, the full Linux/amd64 GPU image built locally, and LIBERO imported with closed stdin while verifying its pinned asset paths.
  dead-ends: Classifying the missing episode as OOM despite a precise persisted exception; relying on a writable home directory to initialize configuration; unit-testing only the application wrapper without importing LIBERO inside the actual GPU image.
  anchors: environments#local-remote-parity-acceptance-test, testing#gate-paid-remote-run-behind-free-dry-run
  source: RunPod Pod `opc5yz6isvxmfr` durable phase/failure/CUDA evidence, pinned LIBERO revision `8f1084e3132a39270c3a13ebe37270a43ece2a01`, and local GPU-image import on 2026-08-24.

- brainstorming — fired: yes; accurate: yes, it kept the remediation limited to the diagnosed headless-config defect and preserved a separate paid revalidation gate; complete: yes; lean: yes.
- environments — fired: yes; accurate: yes, its local/remote parity guidance led to an import inside the exact Linux/amd64 GPU image rather than a host-only test; complete: no, LIBERO's interactive first-import behavior required live diagnosis and is captured above; lean: yes.
- testing — fired: yes; accurate: yes, the image contract was developed red-green and followed by the full 27-test/fake-smoke suite plus the right-layer container import; complete: yes for the free remediation; lean: yes.

- [environments] figured-out-from-scratch <!-- id: lrn-0824-14 -->
  symptom: Cloud Build rejected an `E2_HIGHCPU_32` submission with `FAILED_PRECONDITION: due to quota restrictions, Cloud Build cannot run builds of this machine type in this region`, even though the same machine type had built successfully earlier that day.
  root-cause: The failed command explicitly selected the `us-central1` regional pool, while the earlier successful builds used the global pool; the machine-type quota applies to the selected worker pool, not the Artifact Registry image region.
  fix: Verify the prior build's location and submit through the same global pool while retaining the `us-central1` registry destination — check: no regional build ID was created, zero global builds were active, and global build `647c9b11-4a51-4476-a7fd-804f4f780e6b` succeeded with the expected immutable digest.
  dead-ends: Inferring that an `us-central1` Artifact Registry destination requires a regional Cloud Build; reducing the builder size before comparing the prior successful build location; treating the rejected precondition as a billable build attempt.
  anchors: environments#local-remote-parity-acceptance-test
  source: GCP Cloud Build precondition response and global build metadata during issue #69 on 2026-08-24.

- [environments] figured-out-from-scratch <!-- id: lrn-0824-15 -->
  symptom: The paid revalidation passed CUDA and the previous noninteractive LIBERO boundary, then failed at `model_loading` because `/app/.venv/lib/python3.10/site-packages/libero/libero/assets/scenes/libero_tabletop_base_style.xml` did not exist.
  root-cause: The GPU image copied the exact LIBERO checkout to `/opt/libero` but Python still imported dependency-installed `hf-libero` from `site-packages`; LIBERO's `BDDLBaseDomain` derives its scene-asset directory from the imported module's `__file__`, so the deterministic config could not redirect it.
  fix: Make `/opt/libero` the authoritative import source and add an image-level contract that the imported LIBERO module plus required scene XML resolve under that pinned checkout — check: source inspection confirmed the checkout contains the exact XML, while the current local image reports the imported module under `site-packages`; implementation and paid revalidation remain pending.
  dead-ends: Adding more paths to LIBERO's config file; assuming copying a source checkout makes Python import it; testing only `get_libero_path("assets")`, which passed while runtime code independently used its module-relative directory.
  anchors: environments#local-remote-parity-acceptance-test, testing#test-at-right-layer-not-everything-in-sim, testing#gate-paid-remote-run-behind-free-dry-run
  source: RunPod Pod `8r15u991q4duzm` durable CUDA/phase/failure evidence, pinned LIBERO source, and local GPU-image module inspection on 2026-08-24.

- brainstorming — fired: yes; accurate: yes, it kept the paid operation to one immutable build and one bounded Pod and stopped when the runtime exposed a distinct packaging defect; complete: yes; lean: yes.
- environments — fired: yes; accurate: yes for exact digest, pool-location diagnosis, GPU/volume/template parity, durable evidence, and immediate deletion; complete: no, copied-versus-imported LIBERO source identity required real runtime discovery captured above; lean: yes.
- testing — fired: yes; accurate: yes, all free gates preceded the paid run and the failure was classified only from a precise persisted marker; complete: no, the prior image import test checked config/resource values but not the imported module origin used by scene construction; lean: yes.

- [environments] better-method <!-- id: lrn-0824-16 -->
  symptom: Making `/opt/libero` first on `PYTHONPATH` still imported `hf-libero` from `site-packages`; using the checkout's inner project directory instead made `libero.libero` unavailable, and a source overlay then failed on undeclared legacy `gym`.
  root-cause: The pinned checkout uses a namespace-package outer layout, while the installed wheel is a regular package and therefore wins Python import resolution; the checkout and locked wheel also target different Gym APIs.
  fix: Keep the locked Gymnasium-compatible `hf-libero==0.1.4` code and hydrate its incomplete asset directory from the pinned checkout during the privileged image build — check: a disposable hydrated-wheel overlay imported the modern module, found `libero_tabletop_base_style.xml`, preserved CUDA, and reset exact LIBERO-Goal task 8 to a 256×256 observation; the final local Linux/amd64 GPU image repeated the module/asset/reset checks with closed stdin.
  dead-ends: `PYTHONPATH=/opt/libero`; `PYTHONPATH=/opt/libero/libero`; replacing the wheel with the older checkout; relying on config paths for a module-relative asset lookup.
  anchors: environments#local-remote-parity-acceptance-test, testing#test-at-right-layer-not-everything-in-sim
  source: interactive RunPod Pod `kvt2gz619xym9s` during issue #69 on 2026-08-24; corrects the pending fix in `lrn-0824-15`.

- [lerobot] figured-out-from-scratch <!-- id: lrn-0824-17 -->
  symptom: Pi0.5 printed `Loaded state dict from model.safetensors` from the RunPod network volume but remained in key remapping for several minutes with no CUDA completion or error; the same load progressed immediately after a sequential copy to container-local `/tmp`.
  root-cause: Safetensors memory mapping plus LeRobot's tensor-by-tensor remapping produced non-sequential reads against the 7,473,096,344-byte network-volume object.
  fix: Validate the persistent snapshot, copy it sequentially to transient container disk, validate the staged snapshot, and point offline child processes at the staged path — check: the local-path run advanced past state-dict remapping to processor construction; episode validation remains gated.
  dead-ends: Repeating the network-volume mmap load; inferring OOM without an exception; baking the private checkpoint into the public application image.
  anchors: lerobot#pre-06-checkpoints-unloadable, environments#local-remote-parity-acceptance-test
  source: interactive RunPod Pod `kvt2gz619xym9s` and exact 7.47 GB S3 object metadata during issue #69 on 2026-08-24.

- [lerobot] figured-out-from-scratch <!-- id: lrn-0824-18 -->
  symptom: Offline processor construction failed because `policy_preprocessor.json` names `google/paligemma-3b-pt-224`, but the exact Pi0.5 checkpoint snapshot contains no tokenizer files; a direct authenticated tokenizer download returned HTTP 403.
  root-cause: Processor-era checkpoint completeness is transitive: the processor JSON can reference a separately hosted, manually gated tokenizer that is not included beside the weights. Metadata access does not prove gated file access.
  fix: Preflight a direct file download, pin tokenizer revision `35e4f46485b4d07967e7e9935bc3786aad50687c`, persist and validate its five files plus revision marker with the checkpoint, and override the processor to that local path — check: free bootstrap/validation/override tests pass, and after the operator accepted the PaliGemma terms the Doppler token downloaded all five exact-revision files successfully; real model load and episode remain gated.
  dead-ends: Treating checkpoint dry-run access as proof of all transitive model licensing; enabling general network access during production inference; relying on an unspecified Hub cache.
  anchors: lerobot#pre-06-checkpoints-unloadable, lerobot#no-cli-facts-from-memory
  source: pinned processor JSON, Hugging Face model metadata, initial direct HTTP 403, successful exact-revision `hf download` recheck, and interactive RunPod failure during issue #69 on 2026-08-24.

- [lerobot] figured-out-from-scratch <!-- id: lrn-0824-19 -->
  symptom: Pinned LeRobot revision `8fff0fde7c79f23a93d845d1a50e985de01f8b8a` raised a strict state-dict error for missing `model.paligemma_with_expert.paligemma.model.language_model.embed_tokens.weight` even though the safetensors header contains the corresponding `paligemma.lm_head.weight` tensor.
  root-cause: The pinned loader does not remap the tied language-head alias before `strict=True` loading.
  fix: Load with `strict=False` and immediately fail closed unless the runtime embedding and language-head parameters share storage — check: safetensors range-header inspection proved the head tensor exists and free unit tests cover accepted and rejected storage identity; real GPU verification remains gated.
  dead-ends: Accepting the loader's caught warning and continuing with an unverified model; duplicating a 1+ GB tensor in application code; editing the pinned LeRobot dependency.
  anchors: lerobot#no-cli-facts-from-memory
  source: interactive RunPod output, official pinned LeRobot source, and the exact checkpoint safetensors header during issue #69 on 2026-08-24.

- brainstorming — fired: yes; accurate: yes, it constrained interactive diagnosis to one approved Pod, one hour, and the existing GPU/volume/image; complete: yes; lean: yes.
- browser — fired: yes; accurate: yes, it confirmed the in-app RunPod console lacked an authenticated session without mutating provider state; complete: yes; lean: yes.
- environments — fired: yes; accurate: yes for immutable identity, one-Pod budget, durable-volume diagnostics, provider cleanup, and zero-Pod verification; complete: no, namespace-package precedence and network-volume mmap behavior required live discovery captured above; lean: yes.
- lerobot — fired: yes; accurate: yes for exact revision, processor-file scrutiny, offline loading, and CUDA-only evaluation boundaries; complete: no, transitive gated tokenizer completeness and the pinned loader's tied-key defect required source/runtime discovery captured above; lean: yes.
- testing — fired: yes; accurate: yes, each discovered defect became a free contract before implementation and no episode success was claimed without the real gate; complete: yes for the reached free gates; lean: yes.

- huggingface — fired: yes; accurate: yes, it correctly treated authenticated file download rather than metadata visibility as the licensing proof; complete: yes for the free access recheck, while its upstream mechanics skill was unavailable in this session; lean: yes.
