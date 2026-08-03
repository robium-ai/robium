# Architecture Reference (both eras)

## Final-era database schema (SQLite)

### users
```
id TEXT (uuid), email TEXT UNIQUE, username TEXT UNIQUE, password_hash TEXT,
role TEXT ('user'|'admin'), is_active INTEGER, created_at, updated_at,
github_token_encrypted TEXT NULL, github_username TEXT NULL,
github_connected INTEGER DEFAULT 0
```

### projects (also serves as templates)
```
id TEXT (uuid), name, description, owner_id (FK users),
is_active INTEGER, is_template INTEGER DEFAULT 0, type TEXT, version TEXT,
tags TEXT (JSON), config TEXT (JSON), metadata TEXT (JSON),
github_repo_owner, github_repo_name, github_repo_url, github_repo_id,
template_published_at, template_author, template_version DEFAULT '1.0.0',
template_visibility ('public'|'private') DEFAULT 'public',
created_at, updated_at
```
`metadata` JSON carries the filter facets: `use_cases[]`, `capabilities[]`,
`robots[]`, `simulators[]`.

Plus dynamic filter category/value tables added by the admin filter-management
system (last feature built).

## Final-era API surface

```
/api/auth:     POST signup|login|change-password|refresh|logout, GET me
/api/projects: GET / (search + facet filters + sort), POST /,
               GET /:id, PUT /:id/settings, POST /:id/clone,
               POST /:id/convert-to-template (admin), DELETE /:id,
               GET /templates, GET /facets, GET /templates/facets
/api/dockerfiles: GET /:projectId, POST /:projectId/generate, DELETE /:projectId
/api/integrations/github: POST connect, DELETE disconnect, GET status
/api/admin:    GET /dashboard (+ filter/user management endpoints)
/health
```

## Legacy-era architecture (richer, archived)

- **Services**: DockerfileGenerationService (Handlebars-style templates),
  ContainerLifecycleService, DockerService, TemplateEngine,
  EnvironmentVariableService, ValidationService, CachingService,
  LogStreamingService (WebSocket), WorkspaceMountingService,
  AutomatedCleanupService.
- **WebSocket server** alongside HTTP: heartbeat, connection limits, graceful
  shutdown, real-time log/status streaming.
- **Migrations** (9): initial schema, project configuration, ros_packages,
  modules, projects, plus cleanup migrations (removed category/status/public,
  added tags, added supported_robots to modules).
- **Legacy DB extras**: `modules`, `module_dependencies`, `module_packages`,
  `ros_packages`, `ros_package_versions`, `ros_package_dependencies`,
  activity logs, container state tables.
- **Shared package (legacy)**: JSON Schemas (`project-config`,
  `environment-config`, `project-metadata`, `ros2-package`, `simulation-config`),
  TypeScript types, project templates, module JSON catalog, validation utilities,
  schema loader.
- **ros/ workspace**: Dockerfile + compose for containerized ROS2 (Humble+) builds,
  `ros` helper script (setup/build), `meta/core.vcs.yaml` for upstream deps via
  vcstool.
- Observability: request IDs, timing, structured logger, unified error pipeline.

## Conventions worth keeping

- Uniform API response shape `{ success, data?, error? }`.
- Migrations run idempotently on startup.
- Owner-scoped queries by default; admin bypass explicit.
- GitHub failures non-blocking (project creation succeeds even if repo push fails).
- Tokens encrypted at rest (`APP_ENCRYPTION_KEY`), redacted in logs.
- Env vars: `PORT`, `CORS_ORIGIN`, `JWT_SECRET`, `GITHUB_TOKEN`, `GITHUB_FORK_ORG`,
  `APP_ENCRYPTION_KEY`.
