# VLA pick-and-place — 2026-08-26

- [runpod] figured-out-from-scratch (seen 2x) <!-- id: lrn-0826-01 -->
  symptom: The production driver needed the exact `NVIDIA RTX PRO 4500 Blackwell Server Edition` inventory ID plus network volume `68s0bxbv7p`; REST create rejected that ID, while the first GraphQL request failed authentication and the next request required both singular `gpuTypeId` and the preferred-ID list.
  root-cause: RunPod's current REST create enum, live inventory IDs, and GraphQL Pod input are not behaviorally equivalent; the GraphQL endpoint used by the official tooling authenticates the API key in the query string rather than the REST Authorization header.
  fix: Build the GraphQL URL internally from a fixed endpoint and URL-encoded API key, send the exact singular GPU ID plus ordered IDs and network-volume contract, never log the URL, then safe-field re-read GPU, image, region, volume, disk, mount, and port before startup monitoring. (check: Pod `yqqvxujoq78b37` used exact image `sha256:4613c522…606a`, RTX PRO 4500 Server Edition, `US-KS-2`, and volume `68s0bxbv7p`; it passed rollout/cancellation and was deleted with authoritative Pod list `[]`.)
  dead-ends: Retrying REST with the Server Edition inventory ID; sending the API key only as a Bearer header to GraphQL; assuming the ordered GPU list alone satisfied the mutation's required singular field.
  anchors: runpod#exact-gpu-id-from-live-inventory; runpod#verify-created-pod-contract; runpod#safe-field-provider-diagnostics
  source: issue #69 canary controller builds `44aa36c1-c5c7-4519-9e66-78f9d570f662`, `28fc87f7-1e15-4f7b-89c3-ecfc9ebe5b78`, and final Pod `yqqvxujoq78b37`

- [live-demo] figured-out-from-scratch (seen 1x) <!-- id: lrn-0826-02 -->
  symptom: RunPod GraphQL creation returned the Pod identity but did not echo the request environment, so the first browser-facing allocation response omitted the freshly generated capability even though it had been sent to the Pod.
  root-cause: The orchestrator tried to reconstruct response state only from the provider's sparse create response instead of preserving controller-owned session inputs.
  fix: Merge the controller-generated capability and hard expiry into the immediate instance response, then recover later status from provider state without exposing provisioning credentials. (check: final canary creation immediately returned a 32-character capability; the same capability authorized claim/status/UI/rollout while missing and foreign capabilities returned 404.)
  dead-ends: Waiting for a later REST environment read before returning the session; using the shorter control-plane session ID as the browser capability.
  anchors: live-demo#instance-lifecycle-gateway-contract; live-demo#one-visitor-one-instance-gateway-enforced
  source: issue #69 orchestrator regression and final session `9ee841775796f315c556a7`

- [testing] verified (seen 2x) <!-- id: lrn-0826-03 -->
  symptom: The first production-like Pod reached READY and passed a rollout, but its capability status lacked the newly added `remaining_s` field because live metadata still pointed at an image built before the ready-window timer change.
  root-cause: Source and local tests were current while the immutable deployment digest was stale; a healthy rollout alone did not prove the intended lifecycle revision.
  fix: Rebuild from the exact current app commit, repin both template and orchestrator metadata, and assert a revision-specific status payload before accepting the paid smoke. (check: replacement digest `sha256:4613c522…606a` reported `remaining_s=562`, then passed genuine rollout, active cancellation, deletion, and zero-Pod cleanup.)
  dead-ends: Treating the earlier successful rollout as proof of the timer change; rewriting the immutable 20-episode evaluation manifest to point at a different, unevaluated live image.
  anchors: testing#gate-paid-remote-run-behind-free-dry-run; runpod#overlay-not-deployment-proof
  source: issue #69 stale Pod `9xa9cxdmadr12u` and final Pod `yqqvxujoq78b37`

- [cloud-run] figured-out-from-scratch (seen 1x) <!-- id: lrn-0826-04 -->
  symptom: `gcloud run deploy` reported a new controller/site revision as deployed and serving, but both services kept 100% traffic on an older revision carrying the existing `act-canary` tag; production initially omitted the new VLA route and the live page returned 404.
  root-cause: The services already used manual tagged traffic, so deploying a new revision did not replace the pinned traffic target even though the service template and latest-created revision changed.
  fix: After immutable deployment, inspect `latestCreatedRevisionName`, `latestReadyRevisionName`, and the full traffic map; explicitly run `gcloud run services update-traffic SERVICE --to-latest` when traffic remains pinned, then probe the public routes. (check: controller latest revision served the disabled VLA contract with HTTP 503 and zero Pods; site latest revision served all VLA demo/article routes with HTTP 200.)
  dead-ends: Trusting the deploy command's “serving 100 percent of traffic” summary; checking only the service template image rather than the ready revision and traffic map.
  anchors: cloud-run deployment verification; live-demo#gcloud-run-deploy-demo-flags
  source: Cloud Run revisions `demo-robot-navigation-control-00005-x8h` and `robium-site-00029-46g` on 2026-08-26

- [live-demo] figured-out-from-scratch (seen 1x) <!-- id: lrn-0826-05 -->
  symptom: A local production-driver launch failed before allocation with `GoogleAuthExceptionMessages.NO_ADC_FOUND`, even though RunPod and application inputs were otherwise available.
  root-cause: The atomic budget ledger intentionally authenticates to GCS with the controller workload identity; the local shell did not have Application Default Credentials for that production identity.
  fix: Keep the local failure closed and run the real budget/allocation smoke in a bounded Cloud Run canary using the production controller service account and secret binding. (check: the canary wrote and released generation-conditional reservations, completed the final RunPod lifecycle, and was deleted after the production-disabled deployment.)
  dead-ends: Bypassing the ledger for a local launch; weakening production authentication or copying a service-account credential into the repository.
  anchors: live-demo#lifecycle-needs-host-level-orchestrator; runpod#cleanup-and-production-separate-gates
  source: issue #69 local ADC error and deleted Cloud Run service `demo-vla-control-canary`

- [cloud-run] figured-out-from-scratch (seen 1x) <!-- id: lrn-0826-06 -->
  symptom: `gcloud run services update` rejected the staged controller with `traffic tag 'vla-live-candidate' and service name 'demo-robot-navigation-control' together are too long. Combined traffic tag and service name cannot exceed 46 characters.`
  root-cause: Cloud Run validates the combined service-name and traffic-tag length; the descriptive candidate tag exceeded that current platform limit.
  fix: Use a short, purpose-specific tag (`vla`) and retain the full revision ID in evidence and explicit traffic commands. (check: tagged revision `demo-robot-navigation-control-00008-cus` passed direct candidate probes, then served 100% production traffic.)
  dead-ends: Retrying the same descriptive tag; shortening or recreating the production service.
  anchors: cloud-run deployment verification
  source: queue flag signature `82fcb3babf8f`, issue #69 production enablement

- [live-demo] figured-out-from-scratch (seen 1x) <!-- id: lrn-0826-07 -->
  symptom: The enabled controller candidate reported the VLA demo available, but the staged website still rendered the disabled workspace because `PUBLIC_VLA_LIVE_ENABLED` existed only in the React source and was never passed through Docker or Cloud Build.
  root-cause: Production availability used two independent compile/runtime gates, but only the controller runtime gate had a deployment surface.
  fix: Add a default-false Docker build argument, thread it through Cloud Build and Make, and compile/test both `vla-recorded-build` and `vla-live-build` outputs before promotion. (check: production site revision `robium-site-00032-zes` exposed `data-build-mode=vla-live-build`; an actual browser showed `IDLE` with an enabled Start control.)
  dead-ends: Promoting the controller alone; treating the source-level `import.meta.env` check as proof the immutable site image contained the live build.
  anchors: live-demo#gate-with-demo-smoke-before-linking; cloud-run#build-push-artifact-registry
  source: website commit `591ae34`, Cloud Build `dbf0cc39-bc53-429c-a46c-8459f969e890`

- [runpod] better-method (seen 1x) <!-- id: lrn-0826-08 -->
  symptom: `runpodctl pod list --all --json` failed with `unknown flag: --json` during the final zero-Pod preflight.
  root-cause: The current CLI exposes output format through the global `-o/--output` flag rather than a command-specific JSON boolean.
  fix: Use `runpodctl pod list --all -o json`, then filter only safe fields with `jq`. (check: the corrected command returned zero active Pods before allocation and again after visitor deletion.)
  dead-ends: Treating the usage error as a provider/API failure or retrying `--json`.
  anchors: runpod#safe-field-provider-diagnostics; runpod#cleanup-and-production-separate-gates
  source: issue #69 production lifecycle smoke, 2026-08-26

- [testing] verified (seen 1x) <!-- id: lrn-0826-09 -->
  symptom: Production enablement required proof that the public site, public controller, direct RunPod proxy, real policy, cancellation path, and cleanup all described the same live revision.
  root-cause: Unit, private-canary, or source-level success alone cannot establish the public multi-service release contract.
  fix: Promote exact site/controller revisions, create through the public controller, verify proxy isolation and numeric ready lifetime, run canonical state 0, cancel active state 1, delete through the public controller, and require the authoritative active-Pod count to reach zero. (check: state 0 succeeded with 76 frames; state 1 cancelled; DELETE returned 204; active Pod count returned 0; browser showed live IDLE.)
  dead-ends: Accepting a healthy candidate tag without exercising public production traffic; checking only Cloud Run health endpoints; inferring deletion from the controller response without RunPod re-listing.
  anchors: testing#confirm-smoke-passes-before-done; live-demo#demo-smoke-extends-product-surface; runpod#cleanup-and-production-separate-gates
  source: production session `a99c53d8a3ad0526140fcb`, Pod `c74qvd52y74rm6`

## End-of-block retro — final RunPod and production-disabled deployment

- brainstorming — fired: yes; accurate: yes for keeping the approved issue design and treating the available-GPU amendment as a bounded change; complete: yes; lean: yes.
- runpod — fired: yes; accurate: yes for inventory-first selection, exact contract re-read, safe-field diagnostics, immutable rerun, and confirmed deletion; complete: partial because GraphQL authentication/input quirks and sparse create responses required live discovery, captured above; lean: yes.
- live-demo — fired: yes; accurate: yes for capability isolation, controller-owned lifecycle, evidence fallback, one-Pod budget, and disabled production switch; complete: partial because manual Cloud Run traffic pins and immediate capability preservation required live discovery, captured above; lean: yes.
- integration — fired: yes; accurate: yes for immutable image boundaries, direct browser-to-Pod data flow, and secret placement; complete: yes; lean: yes.
- testing — fired: yes; accurate: yes for free-before-paid gates, revision-specific contract checks, real rollout, cancellation, cleanup, and regression suites; complete: yes; lean: yes.
- learning-loop — fired: yes; accurate: yes for queue promotion, evidence completion, observation merge, and no skill edits; complete: yes; lean: yes.

## End-of-block retro — approved production enablement

- brainstorming — fired: yes; accurate: yes for isolating the missing website build switch before production traffic; complete: yes; lean: yes.
- runpod — fired: yes; accurate: yes for the bounded paid gate, independent proxy/lifecycle signals, safe output, honest billing lag, and zero-Pod cleanup; complete: partial because the current CLI output flag shape was absent and is captured above; lean: yes.
- live-demo — fired: yes; accurate: yes for the direct browser-to-Pod handoff, evidence fallback, one-session product state, and public lifecycle smoke; complete: partial because the separate compile-time website gate had not been surfaced, captured above; lean: yes.
- cloud-run — fired: yes; accurate: yes for staged no-traffic revisions, exact revision promotion, traffic inspection, and rollback readiness; complete: partial because the combined service/tag length limit required live discovery, captured above; lean: yes.
- testing — fired: yes; accurate: yes for testing both immutable site modes and the final rollout/cancel/delete production path; complete: yes; lean: yes.
- learning-loop — fired: yes; accurate: yes for promoting the pending queue flag and recording evidence without editing skills; complete: yes; lean: yes.

- [live-demo] figured-out-from-scratch (seen 1x) <!-- id: lrn-0826-10 -->
  symptom: Raising the generated demo `maxInstances` value to three did not allow a third VLA Pod; the provider driver still returned `The one VLA GPU slot is busy`, and simultaneous creates could pass provider-list checks before new Pods became visible.
  root-cause: Fleet capacity existed in both the generic manager and a hard-coded RunPod one-Pod guard, while provider list consistency was insufficient as an atomic admission lock.
  fix: Make the canonical app manifest the only capacity source, compare both manager/provider counts to that value, and count active generation-conditional GCS reservations inside the same budget transaction. (check: focused red tests failed on the old one-Pod behavior; the final 50-test suite admits three, atomically rejects a fourth with `BUSY`, and the production smoke created exactly three Pods while request four returned HTTP 429 without a Pod.)
  dead-ends: Editing only the generated website JSON, which `sync-demos` correctly reverted; relying only on RunPod's active Pod list for concurrent clicks.
  anchors: live-demo#fleet-budget; live-demo#instance-lifecycle-gateway-contract
  source: website commits `5f002d0` and `ab290ed`; queue signature `ba1f089bd016`

- [runpod] figured-out-from-scratch (seen 1x) <!-- id: lrn-0826-11 -->
  symptom: Three RTX PRO 4500 SE Pods could mount the same network volume, but two concurrent cold starts missed the eight-minute boot gate and one logged `FileNotFoundError: .../.phase.json.tmp -> .../phase.json` before restarting.
  root-cause: Read-only model sharing was supported, but concurrent image/checkpoint startup increased cold-load latency; all Pods also wrote startup diagnostics through one shared directory and fixed temp filename.
  fix: Keep model data shared and immutable, but append the server-generated session ID to `VLA_DIAGNOSTIC_OUTPUT` so each Pod owns its diagnostic files. Treat concurrent readiness as a separate capacity measurement from successful allocation. (check: the production smoke allocated three exact-image/GPU/volume Pods, one reached `READY`, the diagnostic-path contract test passes, and all Pods were deleted.)
  dead-ends: Assuming documented multi-Pod volume attachment implied three equal cold-boot times; treating the diagnostic traceback as a model or CUDA failure.
  anchors: runpod#persistent-volume-shared-readers; runpod#safe-field-provider-diagnostics
  source: Pods `1ft1yzgh620veq`, `k4lu8tnaa5ajlw`, and `gpncldceb6t8m9`; website commit `941ddc9`

- [live-demo] figured-out-from-scratch (seen 1x) <!-- id: lrn-0826-12 -->
  symptom: The controller automatically deleted two boot-timeout Pods, but their atomic ledger reservations retained null `deletedAt` values; the provider router then sent idempotent visitor deletes to Cloud Run because the RunPod resources no longer existed.
  root-cause: Reconciliation deleted provider resources without releasing logical slots, and ownership routing depended solely on a currently visible provider resource instead of allowing a vanished RunPod session to release historical ledger state.
  fix: Mark reservations deleted in the same reconciliation path; make RunPod delete release a matching reservation even without a Pod; when neither provider can find an ID, let both idempotent delete paths run. (check: red reconcile/router tests reproduced both gaps; final 50 tests pass; all three production reservations have deletion timestamps, active reservations are zero, and RunPod lists zero Pods.)
  dead-ends: Retrying DELETE against the RunPod driver implementation before fixing the provider router; relying on hard-expiry filtering to restore capacity while leaving stale audit state.
  anchors: live-demo#cleanup-reaper; runpod#cleanup-and-production-separate-gates
  source: website commits `f08ce91` and `ab290ed`; queue signatures `6b2716e1bd72` and `f66dba2a4fc3`

- [cloud-run] figured-out-from-scratch (seen 1x) <!-- id: lrn-0826-13 -->
  symptom: Interrupting a silent `gcloud builds submit` waiter printed `Cancelling...` and cancelled remote build `e57da544-5cb5-4f59-bbf3-a40662659fd0`, rather than detaching only the local wait.
  root-cause: The submit command owns the newly created Cloud Build operation and propagates Ctrl-C cancellation to it.
  fix: Once a build ID is printed, keep polling the same command or inspect that build read-only; do not send Ctrl-C unless remote cancellation is intended. (check: one clean replacement build `64ee16f9-7959-47b6-aeed-6a9f6f208ef2` completed successfully, and the later final build `48755e15-af49-48f3-ba4e-76335380c902` produced the deployed digest.)
  dead-ends: Interpreting a quiet waiter as a local-only hang despite the already printed remote build ID.
  anchors: cloud-run#build-push-artifact-registry
  source: issue #69 capacity follow-up, 2026-08-26

## End-of-block retro — three-slot production capacity

- brainstorming — fired: yes; accurate: yes for scoping the approved change to three slots, an atomic admission contract, and one bounded paid smoke; complete: yes; lean: yes.
- runpod — fired: yes; accurate: yes for inventory/balance/zero-Pod preflight, immutable contract checks, log inspection, and authoritative cleanup; complete: partial because shared-volume attachment guidance did not distinguish concurrent cold-start performance or diagnostic-writer isolation, captured above; lean: yes.
- live-demo — fired: yes; accurate: yes for per-visitor isolation, budget gating, staged promotion, and public product-state verification; complete: partial because the hard-coded provider cap and vanished-resource ledger routing required live discovery, captured above; lean: yes.
- cloud-run — fired: yes; accurate: yes for immutable builds, no-traffic candidate checks, exact revision promotion, and traffic-map verification; complete: partial because Ctrl-C cancellation propagation was not surfaced, captured above; lean: yes.
- testing — fired: yes; accurate: yes for red/green capacity, atomic reservation, BUSY phase, diagnostic isolation, reconciliation, router, free gates, and a bounded real-provider smoke; complete: yes; lean: yes.

- [live-demo] figured-out-from-scratch (seen 1x) <!-- id: lrn-0826-14 -->
  symptom: Immediately after a successful VLA allocation, the page replaced `BOOTING` with “Live capacity is unavailable” even though the controller returned POST 202, every status poll returned 200, and RunPod was still extracting the immutable image.
  root-cause: The frontend attempted the capability claim as soon as RunPod exposed a proxy hostname, before the gateway was listening; that claim exception shared the controller-poll catch and was mislabeled as lifecycle/capacity failure. The same state also exposed Retry while the existing Pod remained active.
  fix: Attempt the capability claim only after controller phase `READY`; keep claim connection retries in `BOOTING` with an explicit workspace-connection message; reserve `UNAVAILABLE` for controller polling failures; hide Retry whenever an instance exists and tell the visitor that polling continues. (check: live-enabled Astro build passed; staged and public bundles contain the new lifecycle copy; production revision `robium-site-00038-xas` serves 100% traffic; the original session expired cleanly with zero Pods.)
  dead-ends: Treating a RunPod proxy hostname as gateway readiness; mapping gateway connection errors and controller failures to one UI state; asking the visitor to Retry while their first Pod was still billable.
  anchors: live-demo#honest-cold-boot-copy-on-page; live-demo#instance-lifecycle-gateway-contract
  source: production session `1fba2c8f36423785a7e4d0`, Pod `6z7aopyr9248cy`, website commit `07d2cea`

## End-of-block retro — VLA boot feedback

- brainstorming — fired: yes; accurate: yes for treating the request as a bounded existing-flow change and getting explicit approval for the state semantics; complete: yes; lean: yes.
- live-demo — fired: yes; accurate: yes that cold boot must be honest and the page must distinguish lifecycle ownership from the direct gateway handoff; complete: partial because proxy-host availability versus gateway readiness needed live discovery, captured above; lean: yes.
- cloud-run — fired: yes; accurate: yes for immutable build, no-traffic staging, direct candidate verification, and exact revision promotion; complete: yes; lean: yes.

- [live-demo] better-method (seen 1x) <!-- id: lrn-0826-15 -->
  symptom: After the model reached `READY`, the RunPod gateway logged repeated claim HTTP 200 responses while Chrome kept the page in “Connecting your private workspace.” The response had no `Access-Control-Allow-Origin`, so the browser treated each successful cross-origin fetch as a failure.
  root-cause: The website depended on reading a cross-origin `/claim` response even though the capability-scoped Gradio iframe did not require CORS and the gateway's `claimed` flag was informational rather than an access gate.
  fix: Remove the browser-side claim request and render the capability-scoped iframe directly when the lifecycle controller reports `READY`. (check: staged and production live bundles contain the private iframe and no `/claim` request; site revision `robium-site-00040-sar` serves 100% traffic; zero Pods remained before the next visitor test.)
  dead-ends: Rebuilding the large GPU image solely to add CORS for an informational endpoint; proxying claim through the lifecycle controller and putting it back into the application data path; `no-cors` fetch, which would hide genuine failures.
  anchors: live-demo#instance-lifecycle-gateway-contract; live-demo#lifecycle-needs-host-level-orchestrator
  source: production session `5ae47f8663583986141867`, Pod `twen64io4zix9x`, website commit `5424b7e`

## End-of-block retro — direct ready-workspace handoff

- brainstorming — fired: yes; accurate: yes for comparing gateway rebuild, opaque fetch, controller relay, and direct iframe approaches before selecting the smallest safe change; complete: yes; lean: yes.
- live-demo — fired: yes; accurate: yes for keeping the lifecycle controller out of the data path and preserving the capability-scoped direct handoff; complete: yes; lean: yes.
- cloud-run — fired: yes; accurate: yes for immutable site build, no-traffic staging, direct bundle inspection, and exact revision promotion; complete: yes; lean: yes.
