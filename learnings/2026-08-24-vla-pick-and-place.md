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
