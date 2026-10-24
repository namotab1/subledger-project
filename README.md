# SubLedger - SaaS Subscription & Billing System

SubLedger is a simplified billing backend. It manages plans, customers, subscriptions, invoices, payment attempts and an append-only ledger. It is built as a layered application (routes, services, repositories, models, schemas) so the business rules are easy to read, test and extend.

It is a billing foundation, not a Stripe or Razorpay clone: there is no real payment gateway.

The design is documented in [DESIGN.md](DESIGN.md): ERD, service and repository tables, business-rule ownership, the design pattern used, and the invoice and payment flows.

## Tech stack

FastAPI, SQLAlchemy 2, Pydantic v2, PostgreSQL 16, Docker Compose, pytest.

## Project structure

```
subledger/
├── app/
│   ├── main.py              # FastAPI app, error handling, startup
│   ├── config.py            # settings from environment variables
│   ├── db.py                # engine, session, Base, get_db
│   ├── dependencies.py      # builds repositories and services (dependency injection)
│   ├── exceptions.py        # domain errors (mapped to HTTP in main.py)
│   ├── models/              # SQLAlchemy tables and constraints
│   ├── schemas/             # Pydantic request / response models
│   ├── repositories/        # all database access
│   ├── services/            # business rules and workflows
│   ├── routes/              # HTTP endpoints
│   └── utils/billing.py     # billing-period date maths
├── tests/                   # 38 tests
├── SubLedger.postman_collection.json   # 40 requests, with tests
├── Dockerfile
├── docker-compose.yml       # PostgreSQL + the API
├── .env.example
├── requirements.txt
├── DESIGN.md
└── README.md
```

## Setup

### Option A: run everything with Docker

```bash
cp .env.example .env          # then edit the passwords
docker compose up --build
```

The API is at http://localhost:8000 and the interactive Swagger docs are at http://localhost:8000/docs.

### Option B: run the API locally, database in Docker

```bash
cp .env.example .env
docker compose up -d db                       # PostgreSQL only
python -m venv venv
source venv/bin/activate                      # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Tables are created automatically when the app starts. There is no migration tool in the base version (see Limitations).

### Environment variables

| Variable | Purpose | Example |
|---|---|---|
| `DB_NAME` | PostgreSQL database name (used by Docker Compose) | `subledger_db` |
| `DB_USER` | PostgreSQL user (used by Docker Compose) | `subledger_user` |
| `DB_PASSWORD` | PostgreSQL password (used by Docker Compose) | `change_me` |
| `DATABASE_URL` | Connection string used by the app when run locally | `postgresql+psycopg2://subledger_user:change_me@localhost:5432/subledger_db` |
| `INVOICE_DUE_DAYS` | Days between the billing period start and the invoice due date | `14` |

Never commit `.env`. Inside Docker Compose, `DATABASE_URL` is overridden to use the host name `db`.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/plans` | Create a subscription plan |
| GET | `/plans` | List plans (optional `?status=active`) |
| PATCH | `/plans/{plan_id}` | Update or deactivate a plan |
| POST | `/customers` | Create a customer |
| GET | `/customers` | List customers |
| GET | `/customers/{customer_id}` | Fetch a customer |
| GET | `/customers/{customer_id}/ledger` | Fetch the customer's ledger history |
| POST | `/subscriptions` | Create (and activate) a subscription |
| GET | `/subscriptions` | List subscriptions (optional `?customer_id=` and `?status=`) |
| PATCH | `/subscriptions/{subscription_id}/cancel` | Cancel a subscription |
| POST | `/invoices/generate` | Generate an invoice for a subscription |
| GET | `/invoices/{invoice_id}` | Fetch an invoice with its payment attempts |
| POST | `/payments/record` | Record a payment attempt (success or failed) |
| GET | `/health` | Health check |

Money values are returned as strings (for example `"49.99"`) so no precision is lost.

### Status codes

| Code | Meaning |
|---|---|
| 201 | Created |
| 404 | Plan, customer, subscription or invoice not found |
| 409 | Conflict: duplicate email, duplicate active subscription, inactive plan, cancelled subscription, invoice cannot accept payments |
| 422 | Invalid input or a violated business rule: price not above 0, overpayment, currency mismatch, bad billing period |

Business errors have the form `{"error": "conflict", "detail": "A customer with email 'a@b.com' already exists."}`.

### Example walkthrough

```bash
# 1. Plan
curl -X POST localhost:8000/plans -H "Content-Type: application/json" \
  -d '{"name":"Pro","price":"49.99","billing_cycle":"monthly","currency":"USD"}'

# 2. Customer
curl -X POST localhost:8000/customers -H "Content-Type: application/json" \
  -d '{"name":"Asha","email":"asha@example.com","company_name":"Acme"}'

# 3. Subscription
curl -X POST localhost:8000/subscriptions -H "Content-Type: application/json" \
  -d '{"customer_id":1,"plan_id":1}'

# 4. Invoice
curl -X POST localhost:8000/invoices/generate -H "Content-Type: application/json" \
  -d '{"subscription_id":1}'

# 5. Partial payment, then the rest
curl -X POST localhost:8000/payments/record -H "Content-Type: application/json" \
  -d '{"invoice_id":1,"amount":"20.00","currency":"USD","status":"success","provider_reference":"pay_001"}'
curl -X POST localhost:8000/payments/record -H "Content-Type: application/json" \
  -d '{"invoice_id":1,"amount":"29.99","currency":"USD","status":"success","provider_reference":"pay_002"}'

# 6. Ledger
curl localhost:8000/customers/1/ledger
```

After step 5 the invoice is `partially_paid`, then `paid`. The ledger shows `invoice_created`, `payment_success`, `payment_success`.

## Postman collection

`SubLedger.postman_collection.json` (repository root) walks through the whole workflow and checks every business rule: 40 requests in 8 folders (Health, Plans, Customers, Subscriptions, Invoices, Payments, Ledger, Cancel subscription). Requests that exercise a rule have the rule number in their name, matching the table in [DESIGN.md](DESIGN.md#6-business-rule-ownership).

1. Start the API (`docker compose up --build`, or Option B above).
2. In Postman choose **Import** and select the file. The `base_url` collection variable is preset to `http://127.0.0.1:8000`.
3. Open the collection and click **Run**, keeping the order as it is.

Every request has test scripts that assert the status code and the important parts of the response. Ids are passed from one request to the next through collection variables, and a fresh customer email is generated on every run, so the collection can be re-run against the same database. Swagger UI is also available at http://localhost:8000/docs.

## Business rules

| Rule | Result when violated |
|---|---|
| Plan price must be greater than 0 | 422 |
| Customer email must be unique (case-insensitive) | 409 |
| A subscription cannot be created for an inactive plan | 409 |
| A customer cannot have two active subscriptions to the same plan | 409 |
| Invoice `amount_due` is the plan price at the time the invoice is generated | n/a |
| A successful payment cannot exceed the remaining unpaid amount | 422 |
| A fully paid invoice becomes `paid`; a partial payment makes it `partially_paid` | n/a |
| A failed payment does not increase `amount_paid` | n/a |
| Ledger entries are append-only and traceable through `reference_id` | n/a |

Where each rule is enforced (schema, service, repository, database) is in the table in [DESIGN.md](DESIGN.md#6-business-rule-ownership).

## Tests

```bash
pytest
```

38 tests cover the business rules above, plus the supporting rules (billing periods, currency matching, payable invoice states, ledger immutability). Most go through the real API with a fresh in-memory SQLite database per test. `tests/test_services_unit.py` tests the payment and invoice services with fake repositories and no database.

Tests never touch the PostgreSQL database; `tests/conftest.py` forces an in-memory SQLite database.

## Assumptions

1. Creating a subscription also activates it. There is no separate pending state.
2. A subscription's first billing period runs from `start_date` (default today) for one month, one quarter or one year depending on the plan's billing cycle.
3. An invoice is created with status `issued`, and its due date is `INVOICE_DUE_DAYS` after the period start.
4. A failed payment is always recorded (when the invoice can accept payments), even if its amount is larger than the balance, because it changes nothing. The balance rule applies to successful payments.
5. Invoice generation can be called more than once for the same subscription and period; each call creates a new invoice priced at the plan's current price. This lets a price change show up on the next invoice.
6. Ledger `reference_id` values look like `invoice:12` and `payment_attempt:7`.
7. Currency is a 3-letter code, upper-cased, and defaults to `USD`. A payment must use the invoice's currency.
8. There is no authentication or RBAC (out of scope in the brief).

## Limitations

- **No migrations.** Tables are created at startup with `create_all`. Changing a model later needs a migration tool such as Alembic.
- **No pagination** on list endpoints.
- **No idempotency key on payments.** Sending the same `provider_reference` twice records two attempts. The balance rule still prevents overpaying.
- **`overdue` and `void` are never set automatically.** `overdue` invoices accept payments, but nothing moves an invoice into that status because there is no scheduler.
- **Cancelling a subscription does not void its open invoices**, and changing a plan's billing cycle does not recalculate existing subscription periods.
- **No proration, tax or multi-currency conversion.**
- **Ledger immutability** is enforced by the application (no update or delete path, plus ORM guards that raise). A bulk SQL `UPDATE` run directly on the database would bypass the ORM guards; a database trigger would close that gap.
- **Row locking is not covered by the automated tests**, because they run on SQLite, which ignores `SELECT ... FOR UPDATE`. It was verified manually against PostgreSQL.
