# status: unverified
# source: assembled from huggingface/lerobot's docs/source/lerobot-dataset-v3.mdx
# ("Load a dataset for training" section) and its README's own LeRobotDataset
# example, both fetched directly via raw GitHub URLs this session (main
# branch). The `lerobot/pusht` repo id and its shape (206 episodes, 25,650
# frames, "observation.image" + "observation.state" + "action" features)
# were confirmed by fetching that dataset's meta/info.json directly from
# huggingface.co this session, not assumed from memory.
#
# Pairs with examples/train-act-command.md, which trains an ACT policy
# against this same dataset (lerobot/pusht) — the feature names printed
# below (observation.image, observation.state, action) are exactly what
# that training command's policy adapts to automatically.
#
# Requires: uv add "lerobot[dataset]"  (see SKILL.md's Quick start for the
# fuller install used by the rest of this skill's examples)

from lerobot.datasets import LeRobotDataset

REPO_ID = "lerobot/pusht"


def main() -> None:
    # Downloads and caches the dataset under ~/.cache/huggingface/lerobot/
    # the first time it's loaded; subsequent loads reuse the local cache.
    dataset = LeRobotDataset(REPO_ID)

    print(f"repo_id: {REPO_ID}")
    print(f"num_episodes: {dataset.num_episodes}")
    print(f"num_frames: {dataset.num_frames}")
    print(f"fps: {dataset.fps}")
    print(f"features: {sorted(dataset.features.keys())}")

    # Random access by frame index — returns a dict of PyTorch tensors.
    sample = dataset[0]
    print(f"observation.state shape: {tuple(sample['observation.state'].shape)}")
    print(f"observation.image shape: {tuple(sample['observation.image'].shape)}")
    print(f"action shape: {tuple(sample['action'].shape)}")

    # A temporal window instead of a single frame: request the current frame
    # plus the two preceding it (seconds relative to t, so this depends on
    # `dataset.fps`). Useful for policies that condition on recent history.
    delta_timestamps = {"observation.image": [-0.2, -0.1, 0.0]}
    windowed = LeRobotDataset(REPO_ID, delta_timestamps=delta_timestamps)
    windowed_sample = windowed[0]
    # Shape becomes [T, C, H, W] instead of [C, H, W] for the windowed key.
    print(
        "windowed observation.image shape: "
        f"{tuple(windowed_sample['observation.image'].shape)}"
    )


if __name__ == "__main__":
    main()
