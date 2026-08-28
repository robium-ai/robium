# Hub operations checklist

Use this compact reference after confirming the installed `hf` version. Run the
specific command group's `--help` before using a flag not shown here.

## Read-only CLI path

```bash
hf version
hf auth whoami
hf models info ORG/MODEL
hf datasets info ORG/DATASET
hf download ORG/REPO [FILES...] --repo-type model|dataset|space
hf spaces info ORG/SPACE
hf spaces logs ORG/SPACE --build
hf jobs hardware
hf jobs list
hf jobs inspect JOB_ID
hf jobs logs JOB_ID
```

Authentication can be established with `hf auth login`. Never print or place a
token directly in a logged command. `HF_TOKEN` is suitable only when a scoped
secret has already been supplied through the environment or CI secret store.

## Dataset Viewer API

Base URL: `https://datasets-server.huggingface.co`

| Endpoint | Purpose | Key query parameters |
|---|---|---|
| `/is-valid` | Viewer processing status | `dataset` |
| `/splits` | Subsets/configs and splits | `dataset` |
| `/first-rows` | Preview first rows | `dataset`, `config`, `split` |
| `/rows` | Fetch a slice, maximum 100 rows | previous plus `offset`, `length` |
| `/parquet` | Discover Parquet exports | `dataset` |
| `/size` | Rows and byte sizes | `dataset` |
| `/statistics` | Precomputed column statistics | `dataset`, `config`, `split` |

For gated/private data, pass `Authorization: Bearer <token>` through a secure
HTTP client configuration. Do not paste a token into source, shell history, or
captured logs. Start with `/splits`; use the returned config and split values in
row/statistics calls.

## Mutation preflight

Before creating a repo or uploading, state and confirm:

1. account or organization namespace;
2. model/dataset/space type;
3. public/private visibility;
4. exact local source and destination path;
5. whether files are only added/replaced or any deletion is requested;
6. license/card/robotics metadata and, for reproducible publication, revision.

Before starting a Job, state and confirm hardware, namespace, image or UV
command, timeout, secrets, output destination, and cost exposure. Use
`hf jobs hardware` and live `hf jobs run --help` or `hf jobs uv run --help`;
do not encode a stale flavor list here.

## Source verification

Checked directly on 2026-08-27 against the official Hugging Face CLI guide and
reference, Dataset Viewer quickstart, Jobs overview/manage guides, and local
`hf` 1.24.0 help. Re-check the live help for the target version.
