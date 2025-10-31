# Telegram Bot Project Plan: Collect name, age, and address → MySQL

## Short description

We’ll build an async Python Telegram bot (python-telegram-bot v22.x) that guides users through a three-step conversation (name → age → address), validates inputs, asks for consent, and upserts results into a MySQL database keyed by the user’s Telegram ID. Development runs via long polling against a local Docker MySQL; production runs via HTTPS webhooks on a managed host (Render or Fly.io) with a managed MySQL provider (e.g., PlanetScale). SQLAlchemy 2.x + Alembic handle persistence and migrations. Secrets are stored in .env locally and in platform secret stores in prod. We’ll add /cancel and /delete commands and keep logs minimal (no PII).

---

## Decisions (locked)

-   Language/runtime: Python 3.10+ with python-telegram-bot (PTB) v22.x
-   ORM & migrations: SQLAlchemy 2.x + Alembic
-   DB: MySQL
    -   Dev: Dockerized MySQL locally
    -   Prod: Managed (PlanetScale recommended)
-   Update mechanism: Dev = long polling; Prod = HTTPS webhook + secret header
-   Deployment: Render or Fly.io (both supported; choose one when deploying)
-   Scope: Private chats only; entry via /start
-   Validation: age 13–120 inclusive; address ≤ 255 chars; name ≤ 100 chars
-   Privacy: one-line consent; /delete to erase user record
-   Secrets: .env for local; platform secrets for prod
-   Logging: structured console logs without PII

---

## Architecture overview

-   PTB Application (async) with a ConversationHandler handling states:
    -   ASK_NAME → ASK_AGE → ASK_ADDRESS → SAVE
-   Validation at each step; reprompt on invalid input
-   DB layer with SQLAlchemy engine/session + User model; CRUD module for upsert/delete
-   Webhook route (prod) with secret verification; health route for platform
-   Minimal state in memory during conversation (context.user_data); DB write at SAVE

---

## Project structure (proposed)

```
plan/
  plan.md
  wireframes.md
bot/
  app.py                # entrypoint (polling in dev, webhook server in prod)
  conversation.py       # ConversationHandler + validators
  config.py             # env parsing (TOKEN, DATABASE_URL, ENV, WEBHOOK_* )
  logging.py            # basic JSON-ish logging config
  db/
    models.py           # SQLAlchemy Base + User model
    session.py          # engine/sessionmaker init
    crud.py             # insert_or_update_user, delete_user
migrations/             # Alembic directory (versions/ populated by revisions)
requirements.txt        # or pyproject.toml
.env.example            # sample env entries (no secrets)
docker-compose.yml      # dev-only MySQL + healthcheck
README.md               # how to run locally & deploy
```

---

## Dependencies

-   python-telegram-bot[ext] ~= 22.5
-   SQLAlchemy ~= 2.0
-   Alembic ~= 1.13
-   PyMySQL ~= 1.1 (driver; or mysql-connector-python if preferred)
-   python-dotenv ~= 1.0 (optional/local)

---

## Environment variables

-   TELEGRAM_BOT_TOKEN: BotFather token
-   DATABASE_URL: e.g., `mysql+pymysql://USER:PASSWORD@HOST:3306/DB?charset=utf8mb4`
-   ENV: `development` | `production`
-   WEBHOOK_SECRET: random 32–64 char token (prod)
-   WEBHOOK_DOMAIN: fully-qualified domain for webhook (prod)

---

## Database schema

Table: `users`

-   `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY
-   `telegram_user_id` BIGINT UNSIGNED NOT NULL UNIQUE
-   `name` VARCHAR(100) NOT NULL
-   `age` INT UNSIGNED NOT NULL CHECK (age BETWEEN 13 AND 120)
-   `address` VARCHAR(255) NOT NULL
-   `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
-   `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

Notes

-   Use utf8mb4 for full Unicode support.
-   Idempotency keyed by `telegram_user_id` (unique). Upsert updates name/age/address if record exists.

---

## Migrations (Alembic)

-   `alembic init migrations`
-   Configure env to use SQLAlchemy `Base.metadata`
-   `alembic revision -m "create users" --autogenerate`
-   `alembic upgrade head`

---

## Conversation flow

-   /start
    -   Show consent + start prompt
    -   Ask full name (ASK_NAME)
-   ASK_NAME
    -   Validate non-empty, ≤100; store → ASK_AGE
-   ASK_AGE
    -   Parse int; 13–120; store → ASK_ADDRESS
-   ASK_ADDRESS
    -   Validate non-empty, ≤255; store → SAVE
-   SAVE
    -   Upsert by `telegram_user_id`; send confirmation; end conversation
-   /cancel at any point: abort and clear transient state
-   /delete: delete user by `telegram_user_id` and confirm

---

## Validators

-   `is_valid_name(text)`: non-empty, length ≤ 100
-   `parse_age(text)`: int in [13, 120]; else error
-   `is_valid_address(text)`: non-empty, length ≤ 255

---

## CRUD contract

-   `insert_or_update_user(session, telegram_user_id, name, age, address)`
    -   Get by `telegram_user_id`; if exists update; else create; commit
-   `delete_user(session, telegram_user_id)`
    -   Delete row if exists; commit

---

## Error handling & logging

-   Wrap DB ops; on transient failures, log ERROR and show user a retry message
-   Avoid logging PII (mask name/address); log user_id, state transitions, and errors

---

## Local development

1. Start MySQL via Docker Compose (utf8mb4)
2. Create `.env` from `.env.example` and fill in TELEGRAM_BOT_TOKEN, DATABASE_URL
3. Run Alembic migrations
4. Run bot in polling mode (no public URL required)

---

## Production deployment

Choose Render or Fly.io; both provide automatic TLS and public domains.

Common steps

-   Build and deploy the service (Docker or Python buildpack)
-   Set env: TELEGRAM_BOT_TOKEN, DATABASE_URL, WEBHOOK_SECRET, WEBHOOK_DOMAIN, ENV=production
-   Run Alembic migrations (on deploy or via one-off task)
-   Configure webhook via Telegram Bot API `setWebhook`:
    -   `url = https://<WEBHOOK_DOMAIN>/webhook/<secret-path>`
    -   `secret_token = WEBHOOK_SECRET`
    -   `allowed_updates = ["message"]`
-   Expose a health endpoint: `GET /healthz` → 200 OK

PlanetScale notes

-   Use TLS; copy MySQL connection string from the console
-   Ensure `DATABASE_URL` includes the correct driver (`+pymysql`) and db name

---

## Security & privacy

-   Consent message at start; data stored: name, age, address, and telegram_user_id
-   /delete command to erase record
-   Private chat only (ignore groups) to avoid accidental PII in group chats
-   Webhook secret header validation

---

## Testing

-   Unit tests for validators
-   Integration tests for conversation happy path and a couple invalid branches
-   DB integration tests using test DB (containerized)

---

## Edge cases

-   Re-running /start: flow restarts; upsert ensures latest values saved
-   Stale conversations: set conversation timeout (e.g., 10 minutes)
-   Bot blocked/unblocked: optionally handle `my_chat_member` updates

---

## Next steps

-   Implement files under `bot/` and `db/`
-   Add Alembic migration for `users`
-   Provide `docker-compose.yml` for MySQL dev
-   Smoke test locally with polling
-   Deploy to chosen platform and set webhook
