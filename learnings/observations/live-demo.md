## exposing a robot behind NAT while keeping existing DNS rules out every "no-server" tunnel — the answer is a small dial-out relay VM <!-- id: obs-live-demo-001 -->
status: tentative
proof: 1
signal: figured-out-from-scratch
sources: [lrn-0802-05]
target: live-demo (new-section) — checked `live-demo`, `cloud-run`, and
  `environments/references/robot-networking.md` for existing anchors on
  relay VMs, dial-out tunnels, or DNS-ownership constraints (grep for
  "relay VM|dial-out|NAT|Cloudflare|ngrok|Tailscale|reverse tunnel|CGNAT" —
  zero hits in live-demo and cloud-run; robot-networking.md matches only on
  'NAT' in its LAN-side DDS-multicast section, unrelated to public dial-out
  relays); genuinely new content, not an update. Proposed
  addition: Cloudflare Tunnel / ngrok free / Tailscale all require *their*
  DNS, *their* hostname, or *their* client app on every viewing device — if
  the constraint is "reach a robot behind NAT at a URL on DNS you already
  own, from any device with just a link," none of the free "no-server"
  options qualify; the answer is a small public endpoint (e.g. a GCE
  e2-micro) that the robot-side box dials *out* to, which the existing DNS
  provider then A-records to directly.
evidence: proof=1, signal=figured-out-from-scratch (not user-correction, no
  3x ✓, not external) — does **not** clear the ready bar on its own, hence
  `status: tentative`, correctly. The reasoning is sound and internally
  consistent (each ruled-out option is ruled out for a specific, named
  reason) but nothing was built or verified this session — the assistant's
  own framing was "let me spin this up as a proper robium-website effort,"
  i.e. explicitly deferred, not shipped. Also: this session had the robium
  plugin not loaded (same session as lrn-0802-01/obs-new-skills-001), so the
  non-firing of `live-demo`/`cloud-run` here is plausibly the same
  environment condition rather than proof of a distinct trigger-surface gap
  in either skill — recorded as content (figured-out-from-scratch), not as
  a second no-skill-fired claim, to avoid the same mis-signing this run's
  architect entry was corrected for. Promote to `ready` once (a) a relay VM
  actually ships and reaches a demo through it (a passing check), or (b) a
  second independent session hits the same constraint (proof=2).

## capability semantics must survive local provider substitution <!-- id: obs-live-demo-002 -->
status: ready
proof: 1
signal: figured-out-from-scratch
sources: [lrn-0825-06]
target: live-demo#instance-lifecycle-gateway-contract (update) — distinguish the control-plane session ID from a longer browser capability and map capability-scoped gateway phases independently of the local or remote provider
evidence: the local Docker gateway returned `ready` while the orchestrator remained `BOOTING` ✓ · 44 orchestrator tests plus a rebuilt Linux/amd64 allocate-to-delete lifecycle passed after capability-driven mapping ✓ · provider-identity mapping and reuse of the too-short session ID were both ruled out ✓

## preserve controller-owned capability state across sparse provider responses <!-- id: obs-live-demo-003 -->
status: ready
proof: 1
signal: figured-out-from-scratch
sources: [lrn-0826-02]
target: live-demo#instance-lifecycle-gateway-contract (update) — merge a newly generated browser capability and hard expiry from controller-owned allocation input into the immediate response when a provider's create API returns only sparse resource identity
evidence: GraphQL returned a Pod without echoing environment state ✓ · the merged response immediately authorized claim/status/UI/rollout while missing and foreign capabilities returned 404 ✓ · waiting for a later environment read and reusing the control-plane ID were ruled out ✓

## verify Cloud Run traffic, not only the deployed service template <!-- id: obs-live-demo-004 -->
status: ready
proof: 1
signal: figured-out-from-scratch
sources: [lrn-0826-04]
target: live-demo#gcloud-run-deploy-demo-flags (update) — after deploying to a service with tagged/manual traffic, compare latest-created and latest-ready revisions plus the traffic map, route to latest explicitly when needed, and probe the public path
evidence: both deploy commands reported success while old tagged revisions still held 100% traffic ✓ · explicit `--to-latest` made the controller's disabled VLA route and the site's VLA pages publicly reachable ✓ · service-template image inspection and deploy-summary trust were ruled out ✓
