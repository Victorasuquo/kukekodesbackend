# Phase 5 release runbook

This is the executable evidence record for the final launch gate. Run it against staging first and attach command output to `VERIFY_PHASE_3_IN_CHROME.md`.

## Observability

- Set `LOG_LEVEL=INFO`; ship Docker/Caddy JSON logs to the VPS log collector.
- Monitor `/livez` every 30 seconds and `/readyz` every 60 seconds. Alert on 2 consecutive failures.
- Alert on HTTP 5xx > 2%, p95 API latency > 750ms, Redis unavailable, and Celery queue age > 5 minutes.

## Migration and backup

```sh
python -m alembic upgrade head
pg_dump --format=custom "$DATABASE_URL" > "backup-$(date +%Y%m%d%H%M).dump"
```

Restore into a disposable database with `pg_restore`, then run `/readyz` and the smoke tests before accepting the release.

## Rollback

```sh
IMAGE_TAG=<previous-known-good> docker compose pull api worker scheduler
IMAGE_TAG=<previous-known-good> docker compose up -d api worker scheduler
curl --fail https://$API_DOMAIN/readyz
```

## Performance and accessibility

- Run Lighthouse against the deployed frontend in mobile mode and record Core Web Vitals.
- Exercise login, catalog, lesson, progress, community, and admin journeys with keyboard-only navigation and a screen reader.
- Run the backend load profile in `deploy/load-smoke.sh`; investigate any p95 over the agreed budget.

## Pilot release

Create all pilot records through the UI/API, not SQL. Record learner and admin completion of the full journey, then promote the image only after the evidence is attached.
