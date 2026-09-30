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
