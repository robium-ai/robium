# Cloud Run failure router

Start with the first boundary whose evidence is wrong.

- **Build or deploy is rejected**
  - Compare the current `gcloud` command, quota, region, resource request,
    service account, and VPC capacity with official documentation.
  - An image build failure is different from a service revision that cannot be
    scheduled or routed.

- **Container starts locally but boot stalls on Cloud Run**
  - Check whether a request remains open and whether the service uses
    request-based CPU.
  - Continuing logs while a request is open, then silence after it closes,
    points to CPU allocation rather than application deadlock.

- **Gazebo or ROS processes run but topics/world data are absent**
  - Inspect discovery configuration and the first real simulator and DDS data,
    not only process presence.
  - A permanent world-name request loop in the tested Gazebo topology indicates
    the sticky relay race described in `GAZEBO-ROS2.md`.

- **Viewer connects but status or stop reaches another instance**
  - Check affinity-cookie delivery, origin, credentialed requests, and the
    gateway's session-routing or first-claim state.
  - Repeated 409 or 403 responses with otherwise healthy instances distinguish
    routing/claim mismatch from readiness failure.

- **WebSocket drops at a repeatable duration**
  - Compare the elapsed time with the configured Cloud Run request timeout and
    application session cap.
  - Test the real upgrade protocol through the public route; local bridge
    success does not prove proxy compatibility.

- **First boot is much slower than later boots**
  - Separate image pull time from application readiness using revision logs and
    app timestamps.
  - Record the measured cold-start range instead of hiding it behind fake
    progress.

- **Edge returns a malformed-response 503**
  - For a hand-written HTTP server, verify status line, content length, and an
    explicit connection-close header when the socket is closed.

- **VPC deployment reports insufficient addresses**
  - Size the subnet for maximum concurrent instances, not for one container.
  - Inspect current allocation rules before changing the service or network.

- **Public shell is reachable**
  - Treat that as a security review boundary: inspect runtime credentials,
    network egress, filesystem persistence, authentication, and authorization.
  - Do not rely on container isolation or an unauthenticated Cloud Run setting
    as the threat model.
