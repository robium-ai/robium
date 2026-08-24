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
