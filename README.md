# Smart Waste Management & Recycling Operations System

A modular FastAPI backend for waste collection workflows, workforce and vehicle assignment, recycling-center intake, segregation, processing, disposal, complaints, audit logs, dashboards and CSV reporting.

## 1. Beginner setup (local)

Requirements: Python 3.11+, Git (optional), and a terminal.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
uvicorn app.main:app --reload
```

The default local database is SQLite (`waste.db`) so a beginner can run it without installing PostgreSQL. Open **http://127.0.0.1:8000/docs** for Swagger. Health check: `GET /health`.

## 2. Docker + PostgreSQL

```bash
cp .env.example .env
# Change SECRET_KEY before use; keep DATABASE_URL pointing to db service.
docker compose up --build
```

API: http://localhost:8000/docs. Stop with `docker compose down`; preserve data with the named volume. `docker compose down -v` deletes the database volume.

## 3. First login / create the administrator

For this assignment demo, the first user can register with the `super_admin` role:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
 -H 'Content-Type: application/json' \
 -d '{"full_name":"Demo Admin","email":"admin@example.com","password":"StrongPass123","role":"super_admin"}'
```

Then login:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
 -H 'Content-Type: application/json' \
 -d '{"email":"admin@example.com","password":"StrongPass123"}'
```

Copy `access_token`. In Swagger click **Authorize** and enter `Bearer YOUR_ACCESS_TOKEN` (or paste token if Swagger's OAuth dialog asks only for the token). The login response also contains a refresh token. Registering a super admin publicly is intentionally convenient for a local assignment demo; **production must replace this with a one-time bootstrap command or protected invitation flow**.

## 4. Mandatory end-to-end demo (Swagger order)

1. Register/login administrator; use `/auth/me` to verify token.
2. `POST /zones` then `POST /areas`.
3. `POST /categories` (e.g. Plastic, recyclable=true).
4. `POST /customers`.
5. `POST /pickups` with a positive estimated quantity and future date.
6. Create a vehicle (`POST /vehicles`) with capacity greater than or equal to estimated kg.
7. Create a worker with role `driver` (`POST /workers`). Optionally add field workers.
8. Approve pickup with `PATCH /pickups/{id}/status?status=approved`.
9. Create assignment (`POST /assignments`). Vehicle and driver become unavailable/assigned.
10. Complete collection (`POST /collections/{assignment_id}/complete`). Pickup becomes collected; vehicle and workforce become available.
11. Create recycling center (`POST /centers`). `accepted_category_ids` can contain the category ID.
12. Create transfer (`POST /transfers`) using collection, center, vehicle and category IDs; then `POST /transfers/{id}/receive`.
13. Create segregation (`POST /segregations?transfer_id=ID`). Recyclable + non-recyclable + contaminated kg must exactly equal transfer kg.
14. Create processing batch (`POST /processing/batches`). Output cannot exceed input; yield is output/input × 100.
15. Create disposal (`POST /disposals`) and approve (`POST /disposals/{id}/approve`).
16. View `/reports/environmental-impact`, `/reports/dashboard`, `/reports/collections.csv`, and `/audit-logs`.

### Example calculation

A batch receives 100 kg and produces 82 kg recycled output. Processing loss = 100 − 82 = 18 kg. Recycling yield = (82 / 100) × 100 = **82%**.

## 5. API areas

| Area | Main endpoints |
|---|---|
| Auth/users | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`, `/users/{id}/activation` |
| Locations | `/zones`, `/areas` |
| Waste/customer | `/categories`, `/customers` |
| Pickup | `/pickups`, `/pickups/{id}/status` |
| Fleet/workforce | `/vehicles`, `/workers`, `/assignments`, `/collections` |
| Recycling | `/centers`, `/transfers`, `/transfers/{id}/receive`, `/segregations`, `/processing/batches` |
| Disposal | `/disposals`, `/disposals/{id}/approve` |
| Operations | `/maintenance`, `/maintenance/{id}/complete`, `/complaints`, `/notifications` |
| Reports | `/reports/dashboard`, `/reports/environmental-impact`, `/reports/collections.csv`, `/audit-logs` |

All request/response schemas are visible in Swagger. Most list endpoints accept pagination; pickups and zones support filtering. CSV export is provided for collection history.

## 6. Tests

```bash
pytest -q
```

Tests cover health, registration/login/current-user, recycling yield calculation, and rejection of assignments where vehicle capacity is insufficient.

## 7. Alembic migrations

For a new migration after changing models:

```bash
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
```

The first migration is a metadata-based initial migration. For a production deployment, use Alembic as the schema owner and remove the `Base.metadata.create_all` convenience call from `app/main.py` after adding a startup migration/deployment step.

## 8. Role names

`super_admin`, `operations_manager`, `collection_supervisor`, `driver`, `recycling_center_manager`, `field_worker`, `customer`.

## 9. Formula definitions and assumptions

- Processing loss (kg) = input kg − recycled output kg.
- Recycling yield (%) = recycled output kg ÷ processing input kg × 100.
- Dashboard recycling efficiency (%) = sum of processing output kg ÷ sum of collection kg × 100. This can exceed 100% if old inventory is processed during the period; use a common date window for comparable reporting in a production analytics layer.
- Environmental disposed quantity includes **approved** disposal records only.
- The current schema records collection, transfers and batches, but does not yet implement a fully reconciled stock ledger. Production should add immutable inventory movements and enforce aggregate center capacity under transaction/locking.

## 10. Security and production hardening checklist

- Replace the demo public super-admin registration with bootstrap/invitation.
- Set a unique high-entropy `SECRET_KEY`; never commit `.env`.
- Add email/SMS delivery for reset tokens and notifications; current reset-request endpoint is a safe placeholder and admin reset is available for demo.
- Add rate limiting, CORS allowlist, HTTPS, structured logs, secret manager, backups and monitoring.
- Add object-level authorization so customers can only access their own customer/pickup records; current customer listing is role-restricted but some detail workflows are demo-oriented.
- Add stock ledger, capacity reservation, assignment history table, complaint history table, and complete date/zone/category/status report filters for production parity.
- Upload photo files to object storage; this version stores photo reference URLs only.

## 11. Submission checklist

- [x] FastAPI source code and modular folders
- [x] SQLAlchemy database models and ER diagram
- [x] Alembic setup and initial migration
- [x] Swagger/OpenAPI
- [x] Postman collection starter
- [x] Unit and integration tests
- [x] Dockerfile and Compose
- [x] `.env.example` and requirements
- [x] Setup guide and demo walkthrough
- [ ] Git repository URL (create a repository and push this folder)
- [ ] Your own API screenshots (run Swagger and capture successful requests)
- [ ] Record the end-to-end demo (use the sequence above)

**Honest scope note:** This is a runnable assignment-grade foundation covering the primary domain and demo workflow, not a fully audited enterprise production system. Advanced optional items (Redis caching, WebSockets, live email, GPS/maps, Excel, CI/CD, full maintenance scheduling, full monthly/zone/driver report matrix) are documented as extension work rather than claimed as implemented.
