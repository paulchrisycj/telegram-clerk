"""
Main application entrypoint for the Telegram bot.
Supports both polling (development) and webhook (production) modes.
"""
import sys
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler

from bot.config import Config
from bot.conversation import create_conversation_handler, delete_user_data
from bot.db.session import check_db_connection
from bot.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def health_check(request: web.Request) -> web.Response:
    """
    Health check endpoint for production deployment platforms.

    Args:
        request: aiohttp request object

    Returns:
        web.Response: HTTP 200 OK response
    """
    return web.Response(text="OK", status=200)


async def webhook_handler(request: web.Request) -> web.Response:
    """
    Handle incoming webhook requests from Telegram.

    Args:
        request: aiohttp request object

    Returns:
        web.Response: HTTP 200 response
    """
    # Verify webhook secret
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret_token != Config.WEBHOOK_SECRET:
        logger.warning("Invalid webhook secret token received")
        return web.Response(status=403)

    # Get the bot application from app state
    application: Application = request.app["application"]

    # Process the update
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        return web.Response(status=500)

    return web.Response(status=200)


def create_application() -> Application:
    """
    Create and configure the Telegram bot application.

    Returns:
        Application: Configured bot application
    """
    # Create application
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # Add conversation handler
    conversation_handler = create_conversation_handler()
    application.add_handler(conversation_handler)

    # Add standalone /delete command handler (works outside conversation)
    application.add_handler(CommandHandler("delete", delete_user_data))

    logger.info("Bot application created and configured")
    return application


async def run_polling(application: Application) -> None:
    """
    Run the bot in polling mode (development).

    Args:
        application: The bot application
    """
    logger.info("Starting bot in POLLING mode (development)")

    # Initialize the application
    await application.initialize()
    await application.start()

    # Start polling
    await application.updater.start_polling(
        allowed_updates=["message", "callback_query"]
    )

    logger.info("Bot is now polling for updates. Press Ctrl+C to stop.")

    # Keep the bot running
    try:
        # This will block until the application is stopped
        await application.updater.idle()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        # Cleanup
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


async def run_webhook(application: Application) -> None:
    """
    Run the bot in webhook mode (production).

    Args:
        application: The bot application
    """
    logger.info("Starting bot in WEBHOOK mode (production)")

    # Initialize the application
    await application.initialize()
    await application.start()

    # Set webhook
    webhook_url = Config.get_webhook_url()
    logger.info(f"Setting webhook to: {webhook_url}")

    await application.bot.set_webhook(
        url=webhook_url,
        allowed_updates=["message", "callback_query"],
        secret_token=Config.WEBHOOK_SECRET,
    )

    # Create web application
    app = web.Application()
    app["application"] = application

    # Add routes
    app.router.add_get("/healthz", health_check)
    app.router.add_post(Config.WEBHOOK_PATH, webhook_handler)

    # Start web server
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    logger.info(f"Starting webhook server on port {port}")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"Webhook server running on port {port}. Press Ctrl+C to stop.")

    # Keep the server running
    try:
        # Wait forever
        import asyncio
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        # Cleanup
        await runner.cleanup()
        await application.stop()
        await application.shutdown()


def main() -> None:
    """
    Main entry point for the bot application.
    """
    logger.info("=" * 60)
    logger.info("Telegram Bot Starting")
    logger.info(f"Environment: {Config.ENV}")
    logger.info("=" * 60)

    # Check database connection
    if not check_db_connection():
        logger.error("Failed to connect to database. Exiting.")
        sys.exit(1)

    # Create application
    application = create_application()

    # Run in appropriate mode
    import asyncio

    if Config.is_production():
        asyncio.run(run_webhook(application))
    else:
        asyncio.run(run_polling(application))


if __name__ == "__main__":
    main()
