# status: unverified
# source: https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_container.html
#         (Container Installation page, fetched directly this session) and
#         https://catalog.ngc.nvidia.com/orgs/nvidia/containers/isaac-sim
#         (NGC catalog, confirming the `6.0.1` tag is current as of this
#         session). Re-verify the tag against the NGC catalog before using
#         this command in a real project — Isaac Sim ships new container
#         tags with each release.

# Prerequisites: Docker, the NVIDIA Container Toolkit installed on the host
# (Linux only — see the environments skill's GPU-and-remote reference for
# that generic setup), and a working `nvidia-smi` inside a test container
# to confirm GPU passthrough before running Isaac Sim itself.

# Create the cache/config/data directories once, before the first run, and
# make sure they're owned by the UID the container runs as (1234 below —
# the value the docs use for a non-root container user):
mkdir -p ~/docker/isaac-sim/{cache/main,cache/computecache,logs,config,data,pkg}
mkdir -p ~/.cache/ov/hub
sudo chown -R 1234:1234 ~/docker/isaac-sim ~/.cache/ov/hub

docker run --name isaac-sim --entrypoint bash -it --gpus all \
    -e "ACCEPT_EULA=Y" \
    -e "PRIVACY_CONSENT=Y" \
    --rm --network=host \
    -v ~/docker/isaac-sim/cache/main:/isaac-sim/.cache:rw \
    -v ~/docker/isaac-sim/cache/computecache:/isaac-sim/.nv/ComputeCache:rw \
    -v ~/docker/isaac-sim/logs:/isaac-sim/.nvidia-omniverse/logs:rw \
    -v ~/docker/isaac-sim/config:/isaac-sim/.nvidia-omniverse/config:rw \
    -v ~/docker/isaac-sim/data:/isaac-sim/.local/share/ov/data:rw \
    -v ~/docker/isaac-sim/pkg:/isaac-sim/.local/share/ov/pkg:rw \
    -v ~/.cache/ov/hub:/var/cache/hub:rw \
    -u 1234:1234 \
    nvcr.io/nvidia/isaac-sim:6.0.1

# Inside the container, launch headless (see the ros2-integration and
# setup-and-requirements references for the ROS 2 bridge and the WebRTC
# livestream ports needed to view the result remotely):
#
#   ./runheadless.sh -v

# Flag notes:
# - `--gpus all`            required GPU passthrough (NVIDIA Container Toolkit).
# - `--network=host`        required for WebRTC livestreaming to work, not
#                            just a convenience — the signaling/media ports
#                            below need to be reachable directly.
# - `-e "ACCEPT_EULA=Y"`    required; the container will not start without it.
# - `-e "PRIVACY_CONSENT=Y"` optional telemetry opt-in, included here for
#                            parity with the upstream example command.
# - the `-v` cache/config/data mounts persist Omniverse's shader and asset
#   cache across container restarts, so a second run isn't a cold start
#   that re-downloads/re-compiles everything from scratch.
# - `-u 1234:1234`          runs as a non-root UID matching the directories
#                            created above; a mismatched UID/ownership here
#                            is a common source of permission errors.
