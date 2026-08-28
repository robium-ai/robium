# LeRobotDataset: format, loading, recording

The LeRobotDataset format (currently **v3.0**), how to load or stream one
for training, how recording and dataset-editing CLIs use it, and how
episode visualization hands off to Rerun. Hub mechanics beyond "this is the
LeRobotDataset shape a hub repo has" (auth, upload/download, model/dataset
cards) are the `huggingface` skill's territory, not this file's.

Sources: `huggingface/lerobot`'s `docs/source/lerobot-dataset-v3.mdx`,
`docs/source/il_robots.mdx`, `docs/source/using_dataset_tools.mdx`, and the
README, all fetched directly via raw GitHub URLs on 2026-07-10 (`main`
branch). The `lerobot/pusht` dataset's `meta/info.json` was fetched directly
from `huggingface.co/datasets/lerobot/pusht` to confirm it is already on
format v3.0 (206 episodes, 25,650 frames); this is the dataset this
skill's examples and Quick start use throughout.

## Format v3.0: what changed and why

v3.0 (included in `lerobot >= 0.4.0`; the installed `lerobot` on 2026-07-10
is 0.6.1) replaced v2.1's one-file-per-episode layout with **file-based
storage**: many episodes are concatenated into fewer, larger Parquet and MP4
files, with episode boundaries resolved through metadata rather than
filenames. This is what makes `StreamingLeRobotDataset` (below) practical at
scale: fewer, larger files mean less filesystem overhead when streaming
directly from the Hub instead of downloading first.

**Three storage pillars:**

1. **Tabular data** (states, actions, timestamps): Apache Parquet, memory-
   mapped or streamed via the `datasets` stack.
2. **Visual data** (camera frames): MP4, frames from the same episode
   grouped, videos sharded per camera.
3. **Metadata**: JSON/Parquet describing schema, FPS, normalization stats,
   and episode segmentation (start/end offsets into the shared files).

**Directory layout (simplified):**

- `meta/info.json`: schema (feature names/dtypes/shapes), FPS, codebase
  version, path templates for locating data/video shards.
- `meta/stats.json`: global feature statistics (mean/std/min/max) for
  normalization, exposed as `dataset.meta.stats`.
- `meta/tasks.jsonl`: natural-language task descriptions mapped to integer
  IDs, for task-conditioned policies.
- `meta/episodes/`: per-episode records (lengths, tasks, offsets) as
  chunked Parquet.
- `data/`: frame-by-frame Parquet shards, each typically holding many
  episodes.
- `videos/`: MP4 shards per camera, each typically holding many episodes.

## Loading a dataset for training

```python
from lerobot.datasets import LeRobotDataset

repo_id = "lerobot/pusht"
dataset = LeRobotDataset(repo_id)   # downloads + caches locally

sample = dataset[100]
# {'observation.state': tensor(...), 'action': tensor(...),
#  'observation.image': tensor([C, H, W]), 'timestamp': tensor(...), ...}
```

`delta_timestamps` requests a temporal window (seconds relative to the
current frame) instead of a single frame per key, e.g.
`{"observation.image": [-0.2, -0.1, 0.0]}` returns a `[T, C, H, W]` stack.
`LeRobotDataset` returns plain dicts of PyTorch tensors and works directly
with `torch.utils.data.DataLoader`. See `examples/load-dataset-snippet.py`
for a runnable version against `lerobot/pusht`.

The README's own quick example uses a slightly different import path,
`from lerobot.datasets.lerobot_dataset import LeRobotDataset`; both resolve
to the same class; the shorter `from lerobot.datasets import LeRobotDataset`
(used in the v3 doc and above) is the one this skill uses consistently.

## Streaming without downloading

```python
from lerobot.datasets import StreamingLeRobotDataset

dataset = StreamingLeRobotDataset("lerobot/pusht")  # iterates from the Hub directly
```

Useful for datasets too large to comfortably cache locally, or a quick look
before committing to a full download.

## Image transforms (training-time augmentation)

Transforms (`ColorJitter`-based brightness/contrast/saturation/hue,
`SharpnessJitter`, or arbitrary `torchvision.transforms.v2`) are applied at
**training time only**: recording/creation always stores raw images, so
augmentation choices can change later without re-recording. Pass an
`ImageTransforms` instance (built from an `ImageTransformsConfig`, disabled
by default) as `LeRobotDataset(..., image_transforms=...)`. Preview the
effect of a config before a real run with:

```bash
lerobot-imgtransform-viz --repo-id=<id> --output-dir=./transform_examples --n-examples=5
```

This is a `references/policies-and-training.md`-adjacent concern (it only
matters once training starts) but lives in the dataset loading path, so it's
documented here.

## Recording episodes

`lerobot-record` drives a real robot through a teleoperation device, saves
frames into a LeRobotDataset, and pushes it to the Hub on completion:

```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem585A0076841 \
  --robot.id=my_awesome_follower_arm \
  --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 1920, height: 1080, fps: 30}}" \
  --teleop.type=so101_leader \
  --teleop.port=/dev/tty.usbmodem58760431551 \
  --teleop.id=my_awesome_leader_arm \
  --display_data=true \
  --dataset.repo_id=${HF_USER}/record-test \
  --dataset.num_episodes=5 \
  --dataset.single_task="Grab the black cube"
```

Status: unverified; fetched directly from `docs/source/lerobot-dataset-v3.mdx`
and `docs/source/il_robots.mdx` on 2026-07-10; robot/teleop type strings and
camera indices above are placeholders; real values are hardware-specific.

Episode-boundary keyboard controls during recording (Right Arrow/`n` = next,
Left Arrow/`r` = re-record, Esc/`q` = stop) work over X11, Wayland, and
headless/SSH sessions as long as `lerobot-record` runs in an interactive
terminal. **Keyboard teleoperation itself** (as opposed to the recording
control flow) needs a global key backend and only works on X11, a Windows
desktop, or macOS with Accessibility permission granted, not Wayland or
headless. `hf auth login --token ${HUGGINGFACE_TOKEN}` must be run before
recording pushes to the Hub; that login/token mechanic is the
`huggingface` skill's territory; it's only referenced here because
`lerobot-record` calls it inline.

**Always call `finalize()` before `push_to_hub()`** when hand-rolling a
recording loop (as opposed to using `lerobot-record`, which does this for
you); it flushes buffered episode metadata and closes Parquet writers.
Skipping it leaves corrupt Parquet files that won't load:

```python
dataset = LeRobotDataset.create(...)
for episode in range(num_episodes):
    for frame in episode_data:
        dataset.add_frame(frame)
    dataset.save_episode()
dataset.finalize()      # required before push_to_hub()
dataset.push_to_hub()
```

## Replaying an episode

`lerobot-replay --robot.type=<id> --dataset.repo_id=<id> --dataset.episode=0`
drives a real robot through a previously recorded episode's actions, useful
for testing repeatability or cross-robot transfer within the same model.

## Editing an existing dataset

`lerobot-edit-dataset` covers delete-episodes, split, merge, add/remove
feature, and image-to-video conversion operations without hand-writing
Parquet/MP4 manipulation:

```bash
lerobot-edit-dataset \
  --repo_id lerobot/pusht \
  --operation.type delete_episodes \
  --operation.episode_indices "[0, 2, 5]"
```

`--new_repo_id` preserves the original dataset and writes the result to a
new repo id instead of modifying in place. Run `lerobot-edit-dataset --help`
for the full operation list.

## Visualizing episodes

`lerobot-dataset-viz --repo-id=lerobot/pusht --episode-index=0` renders a
full episode (all modalities) through Rerun; the Rerun mechanics themselves
(what you're looking at, session/recording concepts) belong to the `rerun`
skill; this skill only owns invoking the
command. Two more modes (verified 2026-07-12, manip-trial):
`--display-mode foxglove` serves the episode to the Foxglove app (bind
port via `--web-port`, default 8765) instead of Rerun, and
`--save 1 --output-dir <dir>` writes a `.rrd` file headlessly with no
viewer at all, the CI-friendly artifact path. A hosted viewer also exists at
[huggingface.co/spaces/lerobot/visualize_dataset](https://huggingface.co/spaces/lerobot/visualize_dataset)
for browsing a dataset without running anything locally. See `SKILL.md`'s
Platform gotchas for the headless/remote-streaming variant
(`--mode distant --grpc-port=<port>`).

## Migrating v2.1 → v3.0

A converter script aggregates per-episode Parquet/MP4 files into the larger
v3.0 shards and rewrites `meta/episodes/*`:

```bash
python -m lerobot.scripts.convert_dataset_v21_to_v30 --repo-id=<HF_USER/DATASET_ID>
```

Most current-generation hub datasets (including `lerobot/pusht`, confirmed
via its `meta/info.json` on 2026-07-10) are already on v3.0; this is
relevant mainly for older datasets recorded before the format change.
