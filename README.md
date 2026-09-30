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
