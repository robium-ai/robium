# Robium — Legacy Project Memory

This directory preserves the complete knowledge of the previous Robium project
(`~/repos/robium-old`, developed ~2024–2025 with Cursor + Taskmaster) so the next
version can be designed with full awareness of what was built, what was learned,
and what was abandoned.

## Contents

| File | What it covers |
|------|----------------|
| [01-project-history.md](01-project-history.md) | The two eras of the project: the original ambitious vision and the scoped-down redesign, and how/why it evolved |
| [02-original-vision.md](02-original-vision.md) | The full original PRD: web-based robotics IDE, module catalog, containerized execution, simulation |
| [03-final-state.md](03-final-state.md) | Exactly what existed and worked in the last state of the code |
| [04-architecture.md](04-architecture.md) | Technical architecture, stack, database schema, API surface of both eras |
| [05-robotics-domain-model.md](05-robotics-domain-model.md) | The ROS2 domain knowledge: module catalog format, package metadata, templates, base-image strategy |
| [06-analysis-and-lessons.md](06-analysis-and-lessons.md) | Critical analysis from robotics, startup, and open-source community perspectives; lessons for v2 |

## One-paragraph summary

Robium started as a **web-based robotics development studio** — an IDE where users
compose ROS2 applications from a curated module catalog, run them in isolated Docker
containers built from a unified base image, and interact with logs/RViz/Gazebo through
the browser. Over time it was **scoped down to a project-configuration and Dockerfile
generation platform** (React + Express + SQLite) with auth, project/template management,
Hugging Face–style filtering, and GitHub repo publishing. The last commits were UI
polish on an admin filter-management panel. The robotics execution core (containers,
ROS workspace, simulation) was designed and partially prototyped in the legacy era but
was explicitly cut from the final MVP.
