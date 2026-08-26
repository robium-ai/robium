# VLA pick-and-place — 2026-08-25

- [integration] figured-out-from-scratch (seen 1x) <!-- id: lrn-0825-01 -->
  symptom: Cloud Build `a22d390c-8e89-41c8-b47e-95d118a03ce9` failed at Dockerfile step 12 with `the --mount option requires BuildKit` after the GPU Dockerfile adopted `RUN --mount=type=cache`.
  root-cause: Local validation used `docker buildx`, which enables BuildKit, while `gcr.io/cloud-builders/docker` ran legacy `docker build` without `DOCKER_BUILDKIT=1`.
  fix: Set `DOCKER_BUILDKIT=1` on the Cloud Build Docker step whenever the Dockerfile uses cache mounts. (check: the corrected Linux/amd64 GPU target built locally, and all 46 app tests plus Ruff checks passed before resubmission.)
  dead-ends: Repeating the unchanged Cloud Build was ruled out because it would deterministically fail at the same parser gate.
  anchors: Docker build contracts; Cloud Build; BuildKit cache mounts
  source: app build `a22d390c-8e89-41c8-b47e-95d118a03ce9`
