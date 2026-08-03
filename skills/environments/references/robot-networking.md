# Robot networking for real-robot bring-up

Getting a laptop (usually a Mac) onto a physical robot's network well enough
to SSH in, reconfigure it, and run ROS 2 against it. This is the messy,
pre-virtual layer: before any container or lockfile matters, you have to
reach the robot at all. Battle-tested on a real TurtleBot 4 (tb4-teleop,
2026-07-24/25). Everything here is about *host/LAN plumbing*; the parity
mechanics for the environment that runs on top live in the other references.

## Headless first contact on no shared network

When the robot ships headless and there's no shared Wi-Fi yet, cable a
direct Ethernet link (USB-Ethernet on the Mac) and find the robot over
IPv6 link-local:

```bash
ping6 -c 4 ff02::1%en5      # all-nodes multicast on the direct iface
ndp -a                       # read the neighbor table for fe80::... entries
ssh ubuntu@fe80::...%en5     # SSH the link-local addr, scoped to the iface
```

**IPv6 link-local is flaky for unicast SSH.** Multicast ping (`ff02::1`)
answers reliably, but the `ndp -a` entries expire and drop under load;
an `apt` install over that SSH will stall out. The stable fix is to add an
IPv4 alias in the robot's own static subnet and SSH *that* instead. If the
robot's eth0 is statically `192.168.185.3`:

```bash
sudo ifconfig en5 inet 192.168.185.10 netmask 255.255.255.0 alias
ssh ubuntu@192.168.185.3
```

## Reconfiguring the robot's Wi-Fi via netplan

On Ubuntu the Wi-Fi config lives at `/etc/netplan/50-wifis.yaml`
(NetworkManager renderer). The file is marked do-not-edit, but a direct
edit followed by `netplan generate` / `netplan apply` works. Keep it
`chmod 600`; netplan warns when the file is world-readable.

Applying the change bounces eth0, which will kill the very SSH session you
issued it from. Detach the apply so it survives the bounce:

```bash
sudo chmod 600 /etc/netplan/50-wifis.yaml
sudo netplan generate
sudo nohup netplan apply >/tmp/netplan.log 2>&1 &
```

With `autoconnect: yes` (NetworkManager default) the new Wi-Fi persists
across reboots.

## DDS multicast, NAT, and where the bridge must run

- **DDS multicast discovery does NOT cross NAT.** If you cable the Mac to a
  router's WAN port and turn on macOS Internet Sharing, the Mac ends up
  *behind* NAT and ROS 2 sees **zero topics**: discovery multicast never
  reaches the robot's LAN. The teleop host must sit on the robot's own LAN
  subnet, not behind a NAT boundary.
- **macOS has no native ROS 2, and Docker Desktop's Linux VM breaks DDS
  multicast to the physical LAN.** So a Mac can't be a ROS 2 participant on
  the robot's wire either natively or via a container. The consequence for
  visualization: the ROS↔browser bridge (foxglove_bridge / rosbridge) must
  run **on the robot** (talking DDS over localhost), and the browser
  connects to it over a plain TCP WebSocket. See the foxglove skill for the
  bridge side; this is why "run the bridge on the Mac" is a dead end.

## macOS Internet Sharing failure modes

- **Sharing from an iPhone-hotspot uplink won't activate.** `bridge100`
  (192.168.2.1) never comes up. Worse, the half-on state *breaks the direct
  cable*: the robot still answers IPv6 multicast ping but unicast SSH times
  out. Turning Internet Sharing OFF restores the cable. (For a Mac cabled to
  a robot LAN losing its own internet, see the network-service-order gotcha
  in SKILL.md, a separate issue.)

## DHCP and MAC-address gotchas on the shared SSID

- **Two DHCP servers behind one SSID hand out different subnets on the same
  L2.** A Wi-Fi extender running its own DHCP will put the robot and the
  laptop on different subnets even though they share one SSID; they become
  mutually unreachable. Fix by pinning static IPs on both:
  - netplan: `dhcp4: false` plus explicit `addresses:`, `routes:`, and
    `nameservers:`.
  - or NetworkManager: `nmcli con mod <name> ipv4.method manual` (with
    `ipv4.addresses` / `ipv4.gateway` / `ipv4.dns`).
  Both persist across reboots.
- **Wi-Fi MAC randomization hides the hardware MAC from the router's DHCP
  table.** The table shows a randomized `a8:e2:91:...` address, not the
  hardware `d8:3a:dd:...`. Don't try to find the robot by grepping for its
  hardware MAC; identify it by hostname / successful SSH, or sidestep the
  whole problem with static IPs.

## Validating a camera panel on a Mac (no V4L2)

macOS Docker cannot pass a USB webcam into a container; V4L2 is
Linux-only, so the container has no `/dev/video*` to bind. To exercise an
MJPEG video panel locally on a Mac without the real camera, serve a synthetic
multipart stream:

- Serve a local `multipart/x-mixed-replace` source (e.g. an ffmpeg
  `testsrc`) that a browser `<img>` will render as a live MJPEG feed.
- ffmpeg's built-in `-listen` HTTP server sends `application/octet-stream`,
  which a browser `<img>` will **not** render; you need a proper multipart
  server in front, not raw ffmpeg `-listen`.
