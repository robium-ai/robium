# RViz2 failures

Check these in order before rebuilding or restarting the stack.

- **Nothing renders**
  - Confirm Global Options → Fixed Frame names a live frame.
  - Prove a current transform exists from that frame to the message frame.
  - An empty display and a red transform warning are often the same TF failure.

- **The topic publishes but its display stays empty**
  - Compare the publisher's actual type and QoS with the display.
  - Best-effort sensors and transient-local maps are common cases where a
    display's default policy is incompatible.
  - Inspect the `ros2` skill only if this is a graph/QoS issue rather than an
    RViz setting.

- **Data appears frozen or repeatedly expires in simulation**
  - Confirm `/clock` advances and RViz plus every producer agree on
    `use_sim_time`.
  - Check timestamps and TF freshness, not only topic frequency.

- **A saved config loses one display**
  - Look for a missing plugin or package on the new machine. RViz can load the
    remainder of the config while one display is greyed out or errored.
  - Re-check topic namespaces and frame names when moving between robots.

- **RViz is needed on a remote or headless host**
  - RViz2 is a Qt/OpenGL desktop application, not a web server. Use `foxglove`
    for the normal remote path instead of making X forwarding a project
    dependency.
  - Because ROS 2 has no normal native macOS workflow, running RViz2 on a Mac
    also inherits the container/display constraints from `environments`.

For Nav2, a useful evidence set contains TF and RobotModel plus map, global and
local costmaps, plan, footprint, and the raw sensor feeding the costmaps. Once
those inputs render correctly, route incorrect navigation behavior to
`navigation`.
