# ROS 2 integration

The `isaacsim.ros2.bridge` extension, which ROS 2 distros it officially
supports per platform, the OmniGraph node pattern used to publish/subscribe
topics, and a worked clock-publisher example. Source:
`docs.isaacsim.omniverse.nvidia.com`'s ROS 2 installation and tutorial pages
— the distro-support table is a direct fetch this session; the extension
name and OmniGraph node identifiers are drawn from OmniGraph node
references visible in a fetched tutorial page (search-synthesis level
confidence) — re-verify the exact extension id and node names against the
live docs or the running Extensions window before depending on them in a
real project.

## Officially supported ROS 2 distros (direct fetch this session)

| Platform | Supported distros | Recommended |
|---|---|---|
| Ubuntu 24.04 | Jazzy | Jazzy |
| Ubuntu 22.04 | Humble, Jazzy | Jazzy |
| Windows 11 | Humble | Humble |

**This is narrower than robium's general ROS 2 default.** The `architect`
and `environments` skills default new robium projects to **Lyrical Luth**
(the current newest LTS) generally, with Jazzy Jalisco reserved for the
Nav2 vertical — but Isaac Sim's ROS 2 bridge does not officially test or
support Lyrical Luth as of this session's fetch. Don't assume a
Lyrical-Luth-based project gets a working Isaac Sim bridge out of the box;
either target Jazzy (or Humble) for the Isaac-Sim-facing part of a project,
or use the experimental path below and validate it yourself before relying
on it.

**Experimental: any natively-installed distro.** The docs note Isaac Sim
"experimentally supports loading any ROS 2 distro that is natively
installed on your platform" (Ubuntu 22.04 or 24.04 only) by sourcing the
host's own ROS 2 install before Isaac Sim launches, rather than using the
bridge's bundled internal ROS 2 libraries. Only Humble and Jazzy remain
officially tested and recommended; treat any other distro (including
Lyrical Luth) run this way as unverified for a given project until you've
confirmed the bridge actually works against it.

Additional notes from the same fetch:

- The bridge ships internal ROS 2 libraries for both Humble and Jazzy,
  including Cyclone DDS compiled against Python 3.12, so it does not
  strictly require a host ROS 2 install for those two distros.
- Zenoh middleware support is currently available only for ROS 2 Jazzy on
  Linux.

## The bridge extension

The ROS 2 bridge is the extension `isaacsim.ros2.bridge`. It exposes a set
of OmniGraph nodes — building blocks wired together in an Action Graph,
either through the GUI or programmatically via `omni.graph.core`'s
`Controller.edit()` in a standalone Python script — that publish or
subscribe ROS 2 messages from the running simulation. Confirmed node names
from a fetched tutorial: `isaacsim.ros2.bridge.ROS2Context` (the shared ROS 2
context every publisher/subscriber node references) and
`isaacsim.ros2.bridge.ROS2PublishClock` (publishes `/clock` from the
simulation's own time). The bridge also ships publish/subscribe node
variants per ROS 2 message type (image, twist, joint state, TF, and
others) — check the Extensions window's node browser or the live tutorial
pages for the exact node name before wiring one into a real graph rather
than guessing the naming pattern.

## Worked example: publishing `/clock`

From a fetched standalone-Python ROS 2 tutorial page this session — creates
an Action Graph that reads the simulation's own time and publishes it as
`/clock`:

```python
import omni.graph.core as og

og.Controller.edit(
    {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
            ("Context", "isaacsim.ros2.bridge.ROS2Context"),
            ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),
        ],
        og.Controller.Keys.CONNECT: [
            ("ReadSimTime.outputs:simulationTime",
             "PublishClock.inputs:timeStamp"),
            ("Context.outputs:context", "PublishClock.inputs:context"),
        ],
        og.Controller.Keys.SET_VALUES: [
            ("PublishClock.inputs:topicName", "/clock"),
        ],
    },
)
```

Every publisher/subscriber node in a graph shares one `ROS2Context` node
(the `Context.outputs:context` → `<node>.inputs:context` connection above)
— don't create a separate context per node, it's meant to be shared across
the whole graph the same way a single ROS 2 node handle is shared across a
process elsewhere.

Subscribing follows the same graph-node pattern in reverse (a subscribe
node's output feeds application logic instead of a publish node consuming
simulation state) — the docs illustrate this with an example where an
incoming empty ROS 2 message teleports a cube to a random location; the
exact subscribe node name for a given message type should be checked the
same way as any other node in this extension.

## Generic ROS 2 mechanics

Workspaces, colcon, launch files, TF2 concepts, and QoS are the `ros2`
skill's territory, not re-taught here — this reference stops at what the
bridge extension itself publishes and subscribes.
