# KukeKodes Production Phase Tracker

This tracker is shared by the backend and frontend repositories. The frontend lives in `kukekodesfrontend`; the backend lives in `kukekodesbackend`. Keep this file updated in both repositories whenever a phase changes status.

## Status Legend

- `Not started`: no implementation work has landed.
- `In progress`: implementation is underway, but the phase exit gate is not fully satisfied.
- `Blocked`: work needs credentials, infrastructure, a product decision, or another dependency before it can continue.
- `Complete`: backend, frontend, tests, verification evidence, observability, and documented failure states satisfy the phase exit gate.

## Phase Progress

| Phase | Status | Backend Scope | Frontend Scope | Exit Gate |
| --- | --- | --- | --- | --- |
| Phase 0: Stabilize and establish truth | Complete | Canonical route import checks, admin route mounting, admin-only dependency test, `/livez`, `/readyz`, safer error envelope, production config validation, Alembic scaffold, initial learner-id/email migration, Docker/Caddy/worker/scheduler/Redis scaffold, OpenAPI check, backend CI scaffold | `VITE_API_BASE_URL`, no hardcoded Cloud Run URL, no Vercel API proxy rewrite, `/admin/login`, guarded `/admin`, `/admin/courses/new`, direct module API client use, missing TS API types/methods fixed, fake claims and dead footer links removed, frontend CI scaffold | Local install/build/test gates pass; visible production routes are not fake or obviously dead; OpenAPI has no duplicate operation IDs |
| Phase 1: Identity, security, and organizations | Not started | Learner-ID auth, non-unique contact email, credentials table, refresh sessions, recovery, logout-all, deactivation, guardian/consent, organizations, memberships, invitations, cohorts, assignments, scoped RBAC, rate limits, audit logs | Learner-ID login copy/flows, admin/learner session split, organization switching, onboarding, invitations, consent screens, tenant-aware route guards | Two learners can share one email while keeping isolated credentials, sessions, enrollments, and progress; admin/student/tenant boundaries cannot be crossed |
| Phase 2: Complete the learning core | Not started | Courses, modules, lessons, enrollments, assignments, progress, quizzes, certificates, notifications, publish checks, optimistic concurrency, transcript/resource storage | Admin course authoring, student dashboard, catalog, enrollment, lesson viewer, resume state, quizzes, certificates, transcript-first low-data path | Admin creates/publishes a course through the UI; learner enrolls/gets assigned, resumes, completes lessons/quizzes, and receives a verifiable certificate |
| Phase 3: Community, live sessions, Gemini, and exercises | Not started | Moderated community APIs, live-session APIs, Gemini gateway, quotas, safety controls, JS/Python exercise submissions | Real forum UI, live-session join/recording states, AI tutor states, code exercise UI, unsupported feature hiding | Every linked module completes an authenticated browser journey and has loading, empty, error, forbidden, provider-outage, and offline states |
| Phase 4: Admin analytics and Resend communication | Not started | Analytics definitions, overview/users/orgs/courses/cohorts/drop-off/engagement/moderation/email/AI endpoints, Resend replacement, webhooks, outbox-driven reminders | Platform and organization dashboards, email health, moderation queue, exports, reminder preview and preferences | Admin totals reconcile with PostgreSQL queries; org admins see only tenant data; reminders are previewable, idempotent, preference-aware, timezone-aware, and traceable |
| Phase 5: Low-bandwidth, reliability, and launch | Not started | Indexes, pool budgets, Redis limits, provider timeouts, circuit breakers, telemetry, uptime checks, alerts, backups, restore/rollback drills | PWA shell, cached manifests/transcripts/resources, IndexedDB progress queue, conflict-safe replay, data-saver mode, click-to-load YouTube, route splitting, accessibility/performance cleanup | No open P0/P1 defects; CI/E2E pass; latency budget met; backup restore and rollback proven; pilot organization completes full journey |

## Current Phase 0 Evidence

- Backend compile passes: `python -m compileall -q app scripts`.
- Backend OpenAPI check passes: `python -m scripts.check_openapi`.
- Backend focused tests pass: `python -m pytest app/tests -q --disable-warnings --maxfail=1`.
- Docker Compose config validates: `docker compose --env-file .env.example config --quiet`.
- Alembic has one head: `20260912_0001`.
- Frontend type-check passes: `npm run typecheck`.
- Frontend lint passes with existing fast-refresh warnings only: `npm run lint`.
- Frontend production build passes: `npm run build`.

## Current Known Gaps

- Chrome automation could not run in Codex because Chrome browser control is unavailable until the ChatGPT browser extension is enabled under Settings -> Computer use.
- Backend still needs full Phase 1 identity tables and server-side refresh-token storage; Phase 0 only created the first learner-id/email migration boundary.
- The current frontend still stores access and refresh tokens in local storage until Phase 1 replaces that with memory-held access tokens and HttpOnly refresh cookies.
- Route-level code splitting and bundle-size reduction remain Phase 5 work.

## Tracking Rules

- Mark a phase `Complete` only when backend, frontend, tests, browser verification, observability, documentation, and failure behavior satisfy the exit gate.
- Do not add fake data, invented metrics, demo fallbacks, public compliance claims, or production-visible dead controls to satisfy a visual state.
- Keep OpenAPI and Alembic migrations as the shared contract boundaries between backend and frontend work.
- Update this tracker in both repositories in the same commit series whenever status changes.
