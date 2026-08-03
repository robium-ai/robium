# Final State of the Old Repo (what actually existed and worked)

Source: `~/repos/robium-old` at HEAD (`bf0d996 feat: Complete filter management system
implementation`).

## What shipped and worked (per README/status + smoke tests 6/7 passing)

- **Auth**: signup/login/JWT/me/change-password/refresh/logout; bcryptjs hashing;
  role-based access (user/admin); React AuthContext with auto-logout on 401.
- **Projects**: create/list/get/update-settings/delete/clone; owner-scoped;
  admin-only convert-to-template; tags; metadata JSON (use_cases, capabilities,
  robots, simulators) used for filtering.
- **Templates**: projects with `is_template=1`; "Use Template" clone flow with
  custom name; template versioning fields (author, version, visibility).
- **Dockerfile generation**: on-demand from project config; view in UI; cached on
  disk; delete/regenerate.
- **GitHub integration** (admin-token based): create repo on project create/clone,
  push scaffold (README, Dockerfile, docker-compose.yml, .gitignore, .dockerignore,
  dev scripts, src/.keep); fork-based template cloning with fallback; repo fields
  persisted on project. Encrypted per-user PAT was designed in the PRD but the
  shipped path used the server `GITHUB_TOKEN` (admin-only).
- **Filtering UX**: Hugging Face–style chip sidebar with facet counts; dynamic
  filter categories/values managed from an admin panel (last thing built).
- **Admin panel**: user management, project/template management, filter category
  and value management, dashboard counts.
- **Profile**: view/edit profile, change password.

## Stack (final)

- Monorepo: npm workspaces — `packages/{backend,frontend,shared}`.
- Backend: Express + TypeScript + SQLite (file `database.sqlite`, WAL mode,
  migrations auto-run on startup), Joi validation, Helmet/CORS/Morgan,
  JWT, Octokit.
- Frontend: React 18 + TypeScript + **MUI** (PRD flirted with Tailwind/shadcn but
  settled on MUI), React Router, Axios `ApiService` singleton.
- Shared: minimal in final era (types); rich in legacy era (schemas/templates/modules).
- Docker: root docker-compose (frontend 3000, backend 8000), per-package Dockerfiles.
- Response convention: `{ success, data?, message?, error? }` everywhere.

## Final backend file map

```
packages/backend/src/
├── index.ts
├── middleware/ (auth, errorHandler)
├── routes/ (auth, users, projects, dockerfiles, admin, integrations.github)
├── services/ (GitHubService, ProjectScaffoldService)
├── scripts/ (migrate, seed-users, seed-projects, seed-templates, seed-all)
└── utils/ (database, migrations, logger)
```

Frontend pages: Login, Register, Projects, ProjectCreate, ProjectDetail, ProjectEdit,
ProjectSettings, Templates, Settings, Profile, Admin, NotFound.

## What was designed but NOT in the final code

- Everything robotics-runtime: container lifecycle, ROS workspace, WebSockets,
  log streaming, RViz/Gazebo, execution environment. (Existed partially in
  `archive/legacy/` with services like ContainerLifecycleService, DockerService,
  LogStreamingService, WorkspaceMountingService, AutomatedCleanupService,
  TemplateEngine, CachingService.)
- Module/ROS-package catalog (legacy had DB schemas + JSON module files).
- Per-user GitHub PAT connection (PRD section 10; only admin token shipped).
- LLM assistant, marketplace, collaboration (never started).

## Known state/quirks at handoff

- Smoke test expectation: 6/7 passing (7th requires admin token).
- SQLite file committed at `packages/backend/database.sqlite`.
- `.env` was removed from git tracking late (`7d1518f`); an API-key-pattern scrub
  commit exists (`1c59ee3`) — treat old git history as potentially sensitive.
- 22/22 Taskmaster tasks marked done; all were UI/admin polish, confirming the
  final phase was spent on CRUD refinement, not robotics.
