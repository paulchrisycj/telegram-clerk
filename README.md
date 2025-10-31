# Telegram Bot - User Data Collection

A production-ready async Telegram bot built with Python that collects user information (name, age, address) through an interactive conversation and stores it in a MySQL database.

## Features

- **Interactive conversation flow** with validation
- **MySQL database** storage with SQLAlchemy ORM
- **Database migrations** using Alembic
- **Development mode** with long polling
- **Production mode** with HTTPS webhooks
- **Privacy-focused** with /delete command and consent messaging
- **Structured logging** without PII
- **Docker support** for local MySQL development

## Project Structure

```
telegram-bot/
├── plan/
│   ├── plan.md              # Detailed project plan
│   └── wireframes.md        # UX flow and wireframes
├── bot/
│   ├── app.py               # Main entrypoint (polling/webhook)
│   ├── conversation.py      # ConversationHandler & validators
│   ├── config.py            # Environment configuration
│   ├── logging_config.py    # Logging setup
│   └── db/
│       ├── models.py        # SQLAlchemy User model
│       ├── session.py       # Database connection
│       └── crud.py          # Database operations
├── migrations/              # Alembic migration files
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Local MySQL setup
├── .env.example             # Environment variables template
└── README.md               # This file
```

## Prerequisites

- Python 3.10 or higher
- MySQL 8.0 (or Docker for local development)
- A Telegram Bot Token from [@BotFather](https://t.me/botfather)

## Local Development Setup

### 1. Clone and Setup

```bash
# Navigate to project directory
cd telegram-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start MySQL Database

```bash
# Start MySQL using Docker Compose
docker-compose up -d

# Verify MySQL is running
docker-compose ps
```

### 3. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and set your values:
# - TELEGRAM_BOT_TOKEN: Get from @BotFather
# - DATABASE_URL: Use the local MySQL connection string
```

Example `.env` for local development:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_URL=mysql+pymysql://bot_user:bot_password@localhost:3306/telegram_bot?charset=utf8mb4
ENV=development
```

### 4. Run Database Migrations

```bash
# Run Alembic migrations to create tables
alembic upgrade head
```

### 5. Start the Bot

```bash
# Run in development mode (polling)
python -m bot.app
```

The bot will start polling for updates. Test it by sending `/start` to your bot on Telegram.

## Bot Commands

- `/start` - Begin the conversation to collect user information
- `/cancel` - Cancel the current conversation
- `/delete` - Delete your stored information

## Conversation Flow

1. User sends `/start`
2. Bot asks for full name (validates: non-empty, ≤100 characters)
3. Bot asks for age (validates: integer between 13-120)
4. Bot asks for address (validates: non-empty, ≤255 characters)
5. Bot saves data to database and shows confirmation
6. User can update by running `/start` again or delete with `/delete`

## Production Deployment

### Supported Platforms

- [Render](https://render.com)
- [Fly.io](https://fly.io)

### Environment Variables (Production)

```env
TELEGRAM_BOT_TOKEN=your_token_here
DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname?charset=utf8mb4
ENV=production
WEBHOOK_SECRET=random-32-to-64-character-secret-token
WEBHOOK_DOMAIN=your-app.onrender.com
```

### Deployment Steps

#### Option 1: Deploy to Render

1. **Create a new Web Service** on Render
2. **Connect your repository**
3. **Configure the service:**
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m bot.app`
4. **Add environment variables** (see above)
5. **Create a MySQL database** on PlanetScale or another provider
6. **Deploy!**

#### Option 2: Deploy to Fly.io

1. **Install flyctl**: `brew install flyctl` (or see [Fly.io docs](https://fly.io/docs/hands-on/install-flyctl/))
2. **Login**: `fly auth login`
3. **Create app**: `fly launch` (follow prompts)
4. **Set secrets**:
   ```bash
   fly secrets set TELEGRAM_BOT_TOKEN=your_token
   fly secrets set DATABASE_URL=your_db_url
   fly secrets set ENV=production
   fly secrets set WEBHOOK_SECRET=your_secret
   fly secrets set WEBHOOK_DOMAIN=your-app.fly.dev
   ```
5. **Deploy**: `fly deploy`

### Setting Up the Webhook

After deployment, set the webhook URL using the Telegram Bot API:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.onrender.com/webhook",
    "secret_token": "your-webhook-secret",
    "allowed_updates": ["message"]
  }'
```

Verify webhook is set:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

### Database Migration in Production

Run migrations as a one-off task before starting the bot:

```bash
# Render: Use a custom build script
alembic upgrade head && python -m bot.app

# Fly.io: SSH into instance and run
fly ssh console
alembic upgrade head
```

## Database Schema

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT | Primary key (auto-increment) |
| telegram_user_id | BIGINT | Unique Telegram user ID |
| name | VARCHAR(100) | User's full name |
| age | INT | User's age (13-120) |
| address | VARCHAR(255) | User's address |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Viewing Logs

Development mode logs are printed to stdout. In production, use your platform's logging:

```bash
# Render: View logs in dashboard
# Fly.io: fly logs
```

### Database Management

```bash
# Create a new migration
alembic revision -m "description" --autogenerate

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Troubleshooting

### Bot doesn't respond

- Check that `TELEGRAM_BOT_TOKEN` is correct
- Verify the bot is running (`docker-compose ps` or check platform logs)
- In production, verify webhook is set correctly

### Database connection errors

- Check `DATABASE_URL` format and credentials
- Ensure MySQL is running (`docker-compose ps`)
- Verify network connectivity to database

### Webhook not receiving updates

- Verify `WEBHOOK_DOMAIN` matches your actual domain
- Check `WEBHOOK_SECRET` is set correctly
- Use `getWebhookInfo` to verify webhook is registered

## Security Notes

- Never commit `.env` file to version control
- Use strong random secrets for `WEBHOOK_SECRET`
- Run the bot only in private chats to prevent PII leaks
- Logs do not contain PII (names, addresses)
- Users can delete their data anytime with `/delete`

## License

MIT License - feel free to use this project as a template for your own bots!

## Support

For issues or questions:
1. Check the [plan documentation](plan/plan.md)
2. Review the [wireframes](plan/wireframes.md)
3. Open an issue in the repository
