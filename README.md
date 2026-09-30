# Salary Management System

## Local backend and demo data

From the repository root, start the local API and PostgreSQL database, apply the schema
migrations, and seed the demo dataset:

```sh
cd backend
docker compose --env-file .env.example up -d --build
docker compose --env-file .env.example exec backend alembic upgrade head
docker compose --env-file .env.example exec backend python -m app.seed --reset
```

The seed command replaces all existing employee and compensation records with exactly
10,000 deterministic employees and current compensation for 9,500 of them. The remaining
500 employees intentionally have no compensation so compensation coverage insights can be
demonstrated. Running the command again produces the same dataset. `--reset` is required
because seeding deletes the current employee and compensation data before inserting the
demo records.

## Frontend

The React/Next.js application is in `frontend/`. Start the backend and PostgreSQL as above,
then in another terminal run:

```sh
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open <http://localhost:3000>. `BACKEND_API_URL` in `frontend/.env.local` is the backend
origin used by the Next.js same-origin API rewrite; the example points to
`http://localhost:8000`. Set it to the deployed backend origin when deploying the frontend.
Browser requests stay on the frontend origin, so they do not require a permissive backend
CORS policy. Use Node.js 20.9 or newer. Create a production build with `npm run build` and
serve it with `npm start`.

## Public deployment (Railway)

The simplest hosted setup is one Railway project/environment with three services: Railway
PostgreSQL, the backend, and the Next.js frontend. Keep all three in the same region. The
managed database is private and persistent; only the frontend needs a public HTTPS domain.
The frontend's Next.js rewrite calls the backend over Railway's private network, so browser
requests remain same-origin and the backend does not need a permissive CORS policy.

### Create and configure the services

1. Create a Railway project and add a PostgreSQL service named `Postgres`.
2. Add this GitHub repository as a service named `backend`. Set its root directory to
   `/backend`, use the existing `Dockerfile`, and set `PORT=8000` and
   `DATABASE_URL=${{Postgres.DATABASE_URL}}` in its Variables. Do not copy values from
   `backend/.env.example` into production.
3. In the backend service's Deploy settings, set the pre-deploy command to
   `alembic upgrade head` and the health check path to `/health`. This applies migrations
   before a release; it does not run database migrations in the application startup command.
4. Add the same GitHub repository as a service named `frontend`. Set its root directory to
   `/frontend`, build command to `npm ci && npm run build`, and start command to `npm start`.
   Set `BACKEND_API_URL` to
   `http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:8000`. Railway makes service variables
   available while building and running Next.js, so the rewrite receives this value in both
   phases.
5. Generate a public Railway domain for the frontend service. Use that HTTPS URL for the
   application. Keep the backend and database private unless direct public API access is
   specifically needed.

Railway reference variables keep the database URL and private backend address synchronized
without storing credentials in the repository. The backend maps standard `postgresql://`
database URLs to the installed psycopg 3 driver. Never use `.env.example` as production
configuration.

### Migrate and seed once

After the first backend deployment succeeds, confirm the database is a new, empty deployment
database. The pre-deploy command should have applied the migrations. Verify the Alembic
revision with `railway ssh --service backend -- alembic current`, then run the existing seed
command once:

```sh
railway ssh --service backend -- python -m app.seed --reset
```

This inserts exactly 10,000 employees and 9,500 current compensation records; 500 employees
have no compensation. `--reset` deletes existing employee and compensation data, so run it
only against the new deployment database and do not attach it to the service startup or
pre-deploy command. The seed itself is transactional. Confirm the reported counts and inspect
the Insights endpoint before handing the URL to reviewers.

### Deployment variables and checks

Production configuration uses only these application variables in the Railway service
settings:

| Service | Variable | Value |
| --- | --- | --- |
| backend | `DATABASE_URL` | Reference `${{Postgres.DATABASE_URL}}` |
| backend | `PORT` | `8000` |
| frontend | `BACKEND_API_URL` | `http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:8000` |

Railway generates and stores the database credentials. Do not put the resolved database URL,
password, or any Railway token in a tracked file or paste one into this README. A deployment
does not use `backend/.env.example` or `frontend/.env.example`.

Before delivery, verify `/health`, the Alembic current revision, and the employee/compensation
counts on the backend service. Then open the frontend's HTTPS domain and exercise the dashboard,
directory search/filters/pagination, employee detail, missing compensation, a compensation
update, and Insights. Refresh the updated employee and confirm its compensation persists.
