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
| Phase 1: Identity, security, and organizations | Complete | Learner-ID auth, non-unique contact email, credentials table, refresh sessions, recovery, logout-all, admin-audience sessions, guardian/consent tables, organizations, memberships, invitations, cohorts, assignments, scoped RBAC boundary tests, local CORS for split repos | Learner-ID login copy/flows, admin/learner session split, `/admin/login`, session bootstrap from backend, admin organizations screen, create organization, add member by learner ID, invitation token creation, cohort creation, tenant-aware route guards | Two learners can share one email while keeping isolated credentials, sessions, enrollments, and progress; admin/student/tenant boundaries cannot be crossed |
| Phase 2: Complete the learning core | Complete | Courses, modules, lessons, enrollments, assignments, progress, quizzes, certificates, notifications, publish checks, optimistic concurrency, transcript/resource storage | Admin course authoring, student dashboard, catalog, enrollment, lesson viewer, resume state, quizzes, certificates, transcript-first low-data path | Admin creates/publishes a course through the UI; learner enrolls/gets assigned, resumes, completes lessons/quizzes, and receives a verifiable certificate |
| Phase 3: Community, live sessions, Gemini, and exercises | In progress | Mongo-backed moderated community threads/replies/reports/blocks, live-session scheduling/join/attendance/recording, server-side Gemini quota/degraded gateway, JavaScript-only exercise submissions, Alembic migration and mounted routers | Real forum UI with composer/replies/report/block and failure/empty states, live-session join/replay states, AI tutor provider/quota states, code submission history; unsupported Python runtime hidden | Browser evidence for Mongo-backed community and a real provider-backed AI/live/exercise journey remains before marking complete |
| Phase 4: Admin analytics and Resend communication | In progress | Existing admin analytics/export endpoints; Resend HTTP provider adapter replacing SendGrid; remaining webhook/outbox and tenant-scoped reporting work | Existing admin course/org surfaces; analytics, email health, moderation queue, exports, and reminder UI still to be completed | Admin totals reconcile with PostgreSQL queries; org admins see only tenant data; reminders are previewable, idempotent, preference-aware, timezone-aware, and traceable |
| Phase 5: Low-bandwidth, reliability, and launch | In Progress | Dependency readiness now pings Redis; Docker Compose provides Redis/API/worker/scheduler/Caddy; remaining telemetry, backup, and load evidence tracked in verification checklist | PWA manifest and production service-worker shell added; remaining offline progress queue, data-saver UX, and performance evidence tracked in verification checklist | No open P0/P1 defects; CI/E2E pass; latency budget met; backup restore and rollback proven; pilot organization completes full journey |

## Current Phase 0 Evidence

- Backend compile passes: `python -m compileall -q app scripts`.
- Backend OpenAPI check passes: `python -m scripts.check_openapi`.
- Backend focused tests pass: `python -m pytest app/tests -q --disable-warnings --maxfail=1`.
- Docker Compose config validates: `docker compose --env-file .env.example config --quiet`.
- Alembic Phase 0 migration exists: `20260912_0001`.
- Frontend type-check passes: `npm run typecheck`.
- Frontend lint passes with existing fast-refresh warnings only: `npm run lint`.
- Frontend production build passes: `npm run build`.

## Current Phase 1 Evidence

- Backend compile passes: `python -m compileall -q app scripts`.
- Backend OpenAPI check passes: `python -m scripts.check_openapi` with 85 paths and 100 operations.
- Backend focused tests pass: `python -m pytest app/tests -q --disable-warnings --maxfail=1` with 8 tests.
- Clean Alembic migration smoke passes against disposable PostgreSQL database `kukekodes_phase1_smoke_1789276144`; current head is `20260912_0002`.
- API smoke passes for duplicate contact email learners, learner-ID login, admin `/api/v1/admin/auth/login`, organization creation, member add by learner ID, invitation token creation, cohort creation, and learner-scoped organization listing.
- Frontend type-check passes: `npm run typecheck`.
- Frontend lint passes with existing fast-refresh warnings only: `npm run lint`.
- Frontend production build passes: `npm run build`.
- Browser verification passes on `http://127.0.0.1:5173` against backend `http://127.0.0.1:8010`:
  - Admin logs in at `/admin/login` and reaches `/admin`.
  - Admin creates an organization at `/admin/organizations`.
  - Admin adds learner `KK-FSWYMP5O` by learner ID.
  - Admin creates a single-use invitation token.
  - Admin creates `Browser Pilot Cohort`.
  - Admin logout clears both learner and admin refresh-cookie scopes.
  - Learner logs in at `/auth?tab=login` with learner ID and reaches `/dashboard`.
  - Learner attempting `/admin` is redirected back to `/dashboard`.

## Current Known Gaps

- This machine's private backend `.env` still overrides `CORS_ORIGINS` without Vite port `5173`; update local `.env` to include `http://localhost:5173` and `http://127.0.0.1:5173`, or pass `CORS_ORIGINS` when running the backend locally.
- MongoDB is not running locally, so startup logs degraded development mode. This does not block Phase 1 auth/organization testing, but MongoDB must be available before Phase 3 community/AI work.
- The generated Alembic console script in `.kukekodes_venv/bin/alembic` has an old shebang path on this machine; use `python -m alembic ...` or recreate the virtualenv.
- Route-level code splitting and bundle-size reduction remain Phase 5 work.

## Phase 2 Verification Ledger

- [x] Clean and upgrade Alembic migrations reach `20260913_0003` (local PostgreSQL smoke database).
- [x] Backend compile, OpenAPI (91 paths/106 operations), and complete test suite pass (12 tests).
- [x] Frontend type-check, lint, production build, and API-client contract tests pass.
- [x] Admin creates a course, module, transcript-first lesson, and quiz through `/admin/courses/new`.
- [x] Publish validation blocks incomplete content and publishes valid content.
- [x] Learner enrolls through the UI and resumes a saved lesson position (42 seconds survives reload).
- [x] Learner completes every lesson and passes the quiz through the UI (100% server-scored attempt).
- [x] Certificate is persisted and its public verification endpoint confirms it (`is_valid: true`).
- [x] Core Phase 2 browser journey has no new console errors or broken internal navigation; prior startup-only API errors were from the stopped backend before the local service was restarted.
- [x] Loading, empty, error, and permission states are visibly implemented and checked in the admin/learner flows.

## Phase 3 Verification Ledger

- [x] Phase 3 routers are mounted and OpenAPI exposes 110 paths / 128 operations.
- [x] Alembic migration `20260914_0004_phase3` upgrades the local PostgreSQL smoke database.
- [x] Backend compile and Phase 3 contract tests pass; full backend suite passes (14 tests).
- [x] Frontend type-check, production build, and API contract tests pass (7 tests).
- [x] Frontend implements community, live sessions, Gemini tutor, and supported JavaScript exercise workflows with loading/empty/error/provider-unavailable states.
- [ ] Chrome authenticated end-to-end verification against live MongoDB/Gemini/provider services.

## Tracking Rules

- Mark a phase `Complete` only when backend, frontend, tests, browser verification, observability, documentation, and failure behavior satisfy the exit gate.
- Do not add fake data, invented metrics, demo fallbacks, public compliance claims, or production-visible dead controls to satisfy a visual state.
- Keep OpenAPI and Alembic migrations as the shared contract boundaries between backend and frontend work.
- Update this tracker in both repositories in the same commit series whenever status changes.
