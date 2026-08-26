# VLA pick-and-place — 2026-08-25

- [integration] figured-out-from-scratch (seen 1x) <!-- id: lrn-0825-01 -->
  symptom: Cloud Build `a22d390c-8e89-41c8-b47e-95d118a03ce9` failed at Dockerfile step 12 with `the --mount option requires BuildKit` after the GPU Dockerfile adopted `RUN --mount=type=cache`.
  root-cause: Local validation used `docker buildx`, which enables BuildKit, while `gcr.io/cloud-builders/docker` ran legacy `docker build` without `DOCKER_BUILDKIT=1`.
  fix: Set `DOCKER_BUILDKIT=1` on the Cloud Build Docker step whenever the Dockerfile uses cache mounts. (check: the corrected Linux/amd64 GPU target built locally, and all 46 app tests plus Ruff checks passed before resubmission.)
  dead-ends: Repeating the unchanged Cloud Build was ruled out because it would deterministically fail at the same parser gate.
  anchors: Docker build contracts; Cloud Build; BuildKit cache mounts
  source: app build `a22d390c-8e89-41c8-b47e-95d118a03ce9`

- [runpod] figured-out-from-scratch (seen 1x) <!-- id: lrn-0825-02 -->
  symptom: `boto3.client("s3").download_file(...)` failed with `403 Forbidden` on `HeadObject` while the same RunPod network-volume credential could list objects and read them with `GetObject`.
  root-cause: boto3's managed downloader performs a metadata HEAD request that the RunPod S3-compatible credential/path did not permit, even though direct object reads were allowed.
  fix: For bounded RunPod volume evidence downloads, list the exact prefix and stream each object body from `GetObject` to its validated local target; verify byte counts and hashes afterward. (check: all 43 durable evaluation objects downloaded through `GetObject`, all 20 video hashes matched their records, and all 20 MP4s passed `ffprobe`.)
  dead-ends: Retrying `download_file` was ruled out because its mandatory `HeadObject` step would deterministically hit the same permission boundary.
  anchors: S3-compatible network volumes; evidence download; boto3
  source: RunPod volume `68s0bxbv7p`, evaluation prefix `issue-69-evaluation-9aba9cb/`

- [huggingface] figured-out-from-scratch (seen 1x) <!-- id: lrn-0825-03 -->
  symptom: Public dataset creation for the application-pinned repo ID `robium-ai/pi05-libero-goal-task-8-evidence` failed with `403 Forbidden: You don't have the rights to create a dataset under the namespace "robium-ai"`.
  root-cause: The authenticated Hub identity belongs to the existing `robium` organization, while `huggingface.co/robium-ai` returns 404; the implementation had copied the GitHub organization name into a nonexistent Hugging Face namespace.
  fix: Resolve and authorize the actual Hugging Face namespace before hardcoding the publication repo ID or generating a final manifest. (check: authenticated `hf auth whoami` reported organization `robium`; revision `d9908eb717d3e8d62ca7ba0820a825daf36fa7c0` was published publicly under `robium`, downloaded anonymously at that exact revision, and passed all bundle checksums plus current app schema validation.)
  dead-ends: Retrying repo creation was ruled out because the namespace does not exist and the credential has no rights to it; silently publishing under a different namespace would change the approved public evidence contract.
  anchors: Hub namespace preflight; public evidence repository; immutable publication pointer
  source: Hugging Face create-repo response on 2026-08-25

- [huggingface] figured-out-from-scratch (seen 1x) <!-- id: lrn-0825-04 -->
  symptom: The official `hf upload` progress summary displayed `0` uploaded files even though the command returned an immutable commit URL for the 46-file evidence bundle.
  root-cause: The CLI's displayed transfer counter was not authoritative for the resulting repository commit; content-deduplication/progress reporting could not establish whether the commit tree was complete.
  fix: Treat the returned revision as a candidate only, then verify the public repository API inventory and perform an anonymous exact-revision download before recording the publication pointer. (check: public revision `d9908eb717d3e8d62ca7ba0820a825daf36fa7c0` exposed 46 bundle files plus `.gitattributes`; the anonymous download contained all 46 bundle files and `sha256sum -c SHA256SUMS` passed.)
  dead-ends: Trusting the CLI progress counter or commit URL alone was ruled out because neither proves public readability or complete immutable content.
  anchors: Hub upload verification; immutable dataset revision; anonymous publication check
  source: Hugging Face publication for issue #69 on 2026-08-25

- [lerobot] figured-out-from-scratch (seen 1x) <!-- id: lrn-0825-05 -->
  symptom: After the RunPod evaluation wrote `evaluation_complete`, provider log collection ended with `Exception ignored in: <function EGLGLContext.__del__ ...>` during Python teardown.
  root-cause: robosuite's EGL context destructor emitted a cleanup-time exception after the evaluator had already persisted and closed the complete result; it was not an episode failure.
  fix: Make the durable phase marker, per-episode records, complete expected artifact set, and hashes authoritative; report teardown stderr separately instead of reclassifying a completed no-retry evaluation as failed. (check: `evaluation_complete` was durable, all states 0–19 had exactly one successful record, all 20 video hashes matched, all MP4s passed `ffprobe`, and the public exact-revision checksum audit passed.)
  dead-ends: Rerunning any episode was ruled out because the protocol forbids retries and the persisted evidence was already complete and internally consistent.
  anchors: headless EGL teardown; durable evaluation state; no-retry evidence protocol
  source: RunPod Pod `j49jvedkgd9gmi` logs and durable volume `68s0bxbv7p`

## End-of-block retro — public evaluation and publication

- integration — fired: yes; accurate: yes for immutable images and explicit runtime contracts; complete: partial because Cloud Build's legacy Docker builder needed an explicit BuildKit environment flag, captured above; lean: yes.
- runpod — fired: yes; accurate: yes for inventory-grounded allocation, volume locality, exact GPU checks, durable diagnostics, and deletion verification; complete: partial because the S3-compatible credential's HEAD-versus-GET permission difference needed live discovery, captured above; lean: yes.
- lerobot — fired: yes; accurate: yes for the pinned Pi0.5/LIBERO evaluation and compiled-versus-eager separation; complete: partial because benign EGL destructor errors after durable completion needed evidence-based interpretation, captured above; lean: yes.
- testing — fired: yes; accurate: yes for the no-retry protocol, immutable verification, video/hash checks, and clean publication gate; complete: yes for the 20-episode evidence milestone; lean: yes.
- huggingface — fired: yes; accurate: yes for immutable revisions and public verification; complete: partial because the required upstream Hub-mechanics skill was unavailable and namespace authorization plus CLI progress behavior required direct official CLI/API checks, captured above; lean: yes.
