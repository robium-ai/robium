# Generic RunPod skill design

**Date:** 2026-08-24  
**Status:** Approved and implemented

## Goal

Add a first-class `runpod` tool skill to the Robium plugin. The skill will help
an agent safely select, provision, diagnose, validate, and clean up RunPod
compute for generic container workloads. It will also preserve the
battle-tested operational knowledge from Robium issue #69 without narrowing
the skill to robotics or VLA applications.

The outcome is a provider-specific operating guide that delegates changing API
facts to official RunPod documentation while embedding the decision rules,
safety gates, and failure-recovery patterns that agents need during real paid
work.

## Scope

The `runpod` skill owns:

- read-only account, balance, spend, Pod, volume, datacenter, and GPU inventory;
- GPU selection by workload requirements, exact provider ID, region, price,
  architecture, VRAM, cloud type, and storage locality;
- immutable container-image and private-registry deployment;
- Pod provisioning through current official interfaces, including deciding
  between CLI, REST, GraphQL, and SDK paths based on the required fields;
- network-volume creation, locality, mount contracts, and post-create
  verification;
- explicit paid-compute approval, budget, lifetime, and production-enable
  gates;
- startup monitoring through provider state, logs, attached storage, durable
  application markers, and health endpoints;
- bounded interactive debugging on a disposable Pod followed by a new
  immutable build and exact-image revalidation;
- HTTP proxy exposure, capability isolation, cancellation, and externally
  visible health checks;
- artifact collection, cost accounting, Pod deletion, temporary-object
  cleanup, and authoritative zero-Pod verification.

The skill is workload-agnostic. Robotics skills can route to it, but examples
must use generic container, model-serving, or GPU-job terminology unless a
Robium incident is explicitly labeled as evidence.

## Non-goals and boundaries

- Environment choice, lockfiles, Docker fundamentals, CUDA base-image parity,
  and local-versus-remote reproducibility stay in `environments`.
- Application Dockerfiles and multi-container communication stay in
  `integration`.
- Model/framework mechanics stay in their tool skills, such as `lerobot`,
  `isaac-sim`, and `isaac-lab`.
- Cloud Run deployment stays in `cloud-run`.
- The skill will not duplicate the full RunPod API, hard-code unstable stock,
  recommend a single permanent GPU SKU, expose credentials, or provide an
  automatic production-enable command.
- No Robium application code, provider resources, or production settings are
  changed while authoring the skill.

## Skill structure

Create `skills/runpod/` as a deep tool skill:

```text
skills/runpod/
├── SKILL.md
├── evals.yaml
└── references/
    ├── provisioning.md
    └── diagnostics-and-lifecycle.md
```

`SKILL.md` stays below 500 lines and follows the required tool-skill section
order. It provides routing, hard safety directives, a short operational quick
start, common usage patterns, platform gotchas, customization guidance,
references, and a changelog. Detailed commands, query shapes, and incident
evidence live in the two single-topic references.

No reusable script or example file will be added initially. Provider API
interfaces are small enough to document as reviewed snippets, and an untested
automation wrapper would create more risk than value.

## Operating workflow

The quick-start contract is an ordered lifecycle:

1. Confirm credentials without printing them; enumerate only safe fields.
2. Perform read-only inventory and establish the workload's minimum GPU,
   storage, region, network, image, budget, and lifetime requirements.
3. Stop at the paid-compute gate unless the operator has approved the exact
   bounded allocation and required funding/licensing/infrastructure exists.
4. Create one Pod using the interface that can express the complete contract.
5. Immediately re-read and compare exact image, GPU, cloud type, datacenter,
   network volume, mount path, ports, environment-mode flags, and termination
   time. Delete a mismatched Pod rather than debugging the wrong resource.
6. Monitor multiple independent signals. Do not classify `runtime: null`,
   missing ports, or repeated image-start events alone as a root cause.
7. For application defects, use one explicitly approved, time-bounded
   interactive Pod to test reviewed source overlays. Treat overlays only as
   diagnostic evidence.
8. Build a new immutable image and repeat the real acceptance gates against
   that exact digest without diagnostic bypasses.
9. Download and validate evidence, record observed cost, delete temporary
   objects and Pods, and verify zero running Pods.
10. Keep production disabled until a separate explicit production-enable
    approval, even when feasibility passes.

## Issue #69 evidence to embed

The following findings are generalized into directives or gotchas and retain
their provenance in the reference files:

- GPU selection must compare live regional stock with network-volume locality;
  trying A40, A100, H100, or 4090-class alternatives by name alone is not a
  capacity plan.
- Live inventory identifiers can differ from REST schema enums. Exact provider
  IDs must be discovered, not recalled.
- `runpodctl` v2.8 accepted network-volume flags during issue #69 yet created
  Pods whose safe-field reads reported `networkVolume: null`.
- Repeating the CLI with explicit mount flags did not correct the missing
  attachment. Direct REST also rejected the exact Server Edition GPU ID.
- The official GraphQL create mutation successfully expressed the complete
  contract using the exact inventory GPU ID, `networkVolumeId`,
  `volumeInGb: 0`, and `volumeMountPath`.
- Post-create reads are mandatory. Accepted arguments do not prove the
  resulting Pod matches them.
- A large private-image pull can take many minutes. Conversely, repeated
  `start container ...: begin` events can mask a crash loop. System/application
  logs, storage identity, durable markers, and health checks distinguish them.
- RunPod control-plane runtime and port fields can lag real container and
  volume activity.
- Full authenticated Pod objects can contain injected secrets. Diagnostics
  use an explicit safe-field allowlist and redact credentials.
- A single bounded interactive allocation can diagnose several application
  seams faster than repeated immutable builds, but only the rebuilt digest's
  clean run proves deployment readiness.
- The final issue #69 image passed CUDA, default compilation, one real model
  episode, proxy isolation, cooperative cancellation, artifact hashing, and
  cleanup while `VLA_LIVE_ENABLED=false` remained unchanged.
- Cost reporting must identify the observed window and include failed
  allocations rather than attributing the entire delta to the final Pod.

These findings are sourced from
`learnings/2026-08-24-vla-pick-and-place.md`, especially entries
`lrn-0824-05` through `lrn-0824-29`, and the app evidence in the sibling
`robium-apps` repository. The skill must not copy local paths, capability
tokens, credentials, or transient resource IDs into reusable command examples.

## Official-source policy

Before implementation, verify unstable claims against current official RunPod
documentation. Primary sources include the Pod REST API, official GraphQL/SDK
guidance, the live GraphQL schema, networking/proxy documentation, storage
documentation, and CLI documentation.

The references distinguish:

- stable operating principles verified by issue #69;
- current interface shapes verified by direct official documentation fetch;
- provider behavior observed in a dated incident but not guaranteed as a
  permanent API contract.

No current API or CLI syntax is written from memory. If official sources
disagree, the skill states the disagreement and requires a post-create read
rather than presenting one interface as universally authoritative.

## Catalog ownership migration

`environments` currently owns RunPod and `references/gpu-cloud.md`. This
ownership moves to the new skill:

- Move generic RunPod content from the environments reference into the two new
  RunPod references, preserving useful provenance and removing duplication.
- Keep non-RunPod cloud-GPU environment selection and GCP quota context in
  `environments` where it supports local-versus-remote decisions.
- Replace environments' RunPod implementation details with a concise route to
  `runpod` after the environment and image strategy are selected.
- Add `runpod` to the `architect` routing table.
- Update `cloud-run` and any other stale ownership statements that route
  RunPod mechanics to `environments`.
- Preserve workload-specific RunPod references in `isaac-lab` and
  `isaac-sim`; change only their generic-mechanics handoff to the new skill.

Cross-references remain bidirectional: `runpod` routes environment/image
strategy back to `environments`, and workload-specific skills continue owning
their framework mechanics.

## Versioning and repository mechanics

Use `skill-creator` to scaffold and evaluate the new skill, wrapped by
Robium's `skill-author` workflow.

For every existing skill whose content changes:

- archive the complete prior version under `archive/<skill>/<old-version>/`;
- use a major bump when provider ownership or scope changes;
- use a minor or build bump only for routing/cross-reference additions that do
  not change ownership;
- re-confirm `evals.yaml` in the same change for every major bump;
- add dated per-skill changelog entries and one repository changelog entry.

The new `runpod` skill begins at `0.1.0`. Its evals cover positive triggers,
adjacent negative scope, paid-compute stopping, safe diagnostics, volume
verification, slow-start diagnosis, interactive-overlay limits, immutable
revalidation, cleanup, and the separate production-enable gate.

## Validation gates

Implementation is complete only when all of these pass:

1. `uv run skills/skill-author/scripts/validate_skills.py` reports the new
   catalog count and `PASS`.
2. The new trigger evals and every re-confirmed eval file pass the repository's
   supported evaluation mechanism.
3. Plugin manifest JSON sanity checks pass.
4. Repository-wide stale-reference searches find no statement that
   `environments` still owns generic RunPod mechanics.
5. Backticked non-local path and cross-skill-reference checks pass manually.
6. Every current version/API/CLI claim has an honest primary-source note.
7. `git diff --check` passes and only the approved skill/catalog/archive/docs
   files changed.
8. No provider allocation or other paid computation occurs during skill
   authoring and validation.

## Acceptance criteria

An agent presented with a generic request such as “find an available RunPod
GPU,” “attach my RunPod network volume,” “the Pod has no ports,” “debug this
Pod interactively,” or “clean up the RunPod allocation” should load `runpod`
and receive an ordered, safe workflow. An environment-choice question without
a chosen provider should still load `environments`, and framework-specific
questions should remain with their existing tool skills.

The skill is successful when it prevents the costly issue #69 failure pattern:
it must not assume accepted creation flags were applied, must not terminate a
slow Pod from one weak signal, must not print secret-bearing provider objects,
must not promote an interactive overlay as an immutable deployment, and must
not enable production as a side effect of a passing test.
