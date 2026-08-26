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
  fix: Resolve and authorize the actual Hugging Face namespace before hardcoding the publication repo ID or generating a final manifest. (check: authenticated `hf auth whoami` reported organization `robium`, the `robium` Hub page returned 200, and the `robium-ai` page returned 404; publication paused before upload.)
  dead-ends: Retrying repo creation was ruled out because the namespace does not exist and the credential has no rights to it; silently publishing under a different namespace would change the approved public evidence contract.
  anchors: Hub namespace preflight; public evidence repository; immutable publication pointer
  source: Hugging Face create-repo response on 2026-08-25
