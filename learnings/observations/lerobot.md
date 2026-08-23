## dataset rows may mix joint degrees with gripper percent <!-- id: obs-lerobot-001 -->
status: ready
proof: 1
signal: figured-out-from-scratch
sources: [lrn-0817-09]
target: lerobot#load-hub-dataset (update) — verify per-channel units and use the environment's published conversion helper instead of applying one vector-wide conversion
evidence: recorded rows contained degree-scale joints and a percent-scale gripper while the simulator expected radians ✓ · so101-nexus's dataset_row_to_sim_qpos conversion passed the dataset contract tests and the UI now labels recorded units explicitly ✓ · vector-wide numpy.deg2rad was ruled out because it corrupts the gripper channel ✓

## video-backed datasets require LeRobot's dataset extra <!-- id: obs-lerobot-002 -->
status: ready
proof: 1
signal: wrong-guidance
sources: [lrn-0817-10]
target: lerobot#load-hub-dataset (update) — document `lerobot[dataset]` as the minimum install for reading datasets whose cameras are stored as video
evidence: bare `lerobot` resolved and imported but all seven dataset tests failed at video-frame decoding ✓ · `lerobot[dataset]==0.6.0` supplied torchcodec and restored 49/49 passing tests ✓ · bare LeRobot was ruled out despite its successful import ✓
