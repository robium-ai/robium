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
