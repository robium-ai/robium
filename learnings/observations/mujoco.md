## clamp reset state to the UI control bounds <!-- id: obs-mujoco-001 -->
status: ready
proof: 1
signal: noise
sources: [lrn-0817-11]
target: mujoco (new-section) — distinguish joint state, actuator control, and rounded widget ranges; clamp initial values to the widget's actual bounds before binding them
evidence: a reset joint position fell just outside the slider minimum and Gradio rejected the value ✓ · clamping against the slider's own bounds passed test_reset_state_is_clamped_into_the_slider_range ✓ · clamping only to the true actuator range was ruled out because rounded display bounds remained narrower ✓

## calibrate grasp height from contact points, not the TCP site <!-- id: obs-mujoco-002 -->
status: ready
proof: 1
signal: figured-out-from-scratch
sources: [lrn-0817-17]
target: mujoco#empirical-grasp-calibration (update) — measure fingertip/object contact positions relative to the TCP and sweep grasp height before tuning speed or grip force
evidence: measured jaw contacts pinched about 9 mm below the TCP while the initial expert aimed at cube-center TCP height ✓ · lowering GRASP_Z to 0.006 m produced 100 percent grasp-then-lift survival and raised end-to-end performance to 79/100 ✓ · grip-angle, carry-speed, easing, and yaw sweeps were ruled out before correcting the geometric aim error ✓

## position-controlled grippers may eject objects when held fully closed <!-- id: obs-mujoco-003 -->
status: ready
proof: 1
signal: figured-out-from-scratch
sources: [lrn-0817-18]
target: mujoco#gripper-polarity-empirical (update) — calibrate a stable hold command as well as open/closed polarity; more time at the actuator minimum can worsen a grasp
evidence: slower carrying at the fully closed target reduced success from 3/12 to 0/12 ✓ · commanding a neutral hold instead of the actuator minimum removed the speed/grip interaction after grasp-height correction ✓ · squeezing harder and assuming slower motion was safer were ruled out ✓

## use an environment's operational-space controller before implementing IK <!-- id: obs-mujoco-004 -->
status: ready
proof: 1
signal: better-method
sources: [lrn-0817-19]
target: mujoco#ik-fails-silently (update) — when the environment exposes TCP control, let its controller solve IK and record the resulting joint targets required by the application's action contract
evidence: the scripted expert risked duplicating IK, grasp, and success logic in the application ✓ · pd_ee_pose control with recorded actuator joint targets replayed successfully through the app's pd_joint_pos mode ✓ · copying the upstream Jacobian loop and recording TCP poses as dataset actions were ruled out ✓
