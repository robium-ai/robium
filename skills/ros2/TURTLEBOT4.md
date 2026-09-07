# TurtleBot 4 and Create 3 evidence

This card records Robium observations from the `tb4-teleop` application. Treat
them as signatures to compare, not as universal TurtleBot defaults.

- **No ROS graph after boot:** on 2026-07-24, `turtlebot4.service` failed with
  `rcl node's rmw handle is invalid` while `wlan0` was down. The robot's
  CycloneDDS configuration bound to `wlan0`, so restoring Wi-Fi and restarting
  the service restored 24 topics. Establish network-interface health before
  rewriting DDS configuration.

- **Lidar works but the base does not:** `/scan` is produced on the Pi and does
  not prove that the Create 3 application is connected. In the observed wedge,
  `/motion_control`, `/wheel_status`, and `/battery_state` disappeared while the
  base still answered at `192.168.186.2` over `usb0`.

- **Recovering that base wedge:** the reproducible recovery was the Create 3
  application restart endpoint, with a JSON body:

  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{}' \
    http://192.168.186.2/api/restart-app
  ```

  A bare POST hung in that setup. About 30 seconds after the JSON request,
  `/motion_control` returned and the `/cmd_vel` subscription count changed from
  0 to 1. Pi-side DDS edits, clock matching, base reboot, and a physical power
  cycle did not reproduce the recovery. Re-check the current Create 3 API before
  automating this endpoint.

- **Inspecting base topics:** the observed Create 3 publishers were best-effort.
  CLI inspection needed `--qos-reliability best_effort`. For an alive check,
  fast topics such as `/imu` or `/wheel_status` were less ambiguous than the
  slowly published `/battery_state`.

- **Reverse motion stops early:** this can be the base's safety behavior rather
  than teleop packet loss. The observed `motion_control` parameter supported
  `none`, `backup_only`, and `full`; `backup_only` retained cliff safety while
  removing the backup limit. Verify the current
  [Create 3 safety documentation](https://iroboteducation.github.io/create3_docs/api/safety/)
  before changing a physical robot's safety settings.
