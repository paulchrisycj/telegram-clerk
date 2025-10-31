"""
Conversation handler and validators for the Telegram bot.
"""
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from bot.db.crud import insert_or_update_user, delete_user
from bot.db.session import get_db_session
from bot.logging_config import get_logger

logger = get_logger(__name__)

# Conversation states
ASK_NAME, ASK_AGE, ASK_ADDRESS = range(3)


# ===== Validators =====

def is_valid_name(text: str) -> bool:
    """
    Validate user's name.

    Args:
        text: The name to validate

    Returns:
        bool: True if valid, False otherwise
    """
    return bool(text and text.strip() and len(text.strip()) <= 100)


def parse_age(text: str) -> int:
    """
    Parse and validate age.

    Args:
        text: The age string to parse

    Returns:
        int: The parsed age

    Raises:
        ValueError: If age is invalid or out of range
    """
    try:
        age = int(text.strip())
        if age < 13 or age > 120:
            raise ValueError(f"Age {age} is out of range (13-120)")
        return age
    except ValueError as e:
        raise ValueError(f"Invalid age: {e}")


def is_valid_address(text: str) -> bool:
    """
    Validate user's address.

    Args:
        text: The address to validate

    Returns:
        bool: True if valid, False otherwise
    """
    return bool(text and text.strip() and len(text.strip()) <= 255)


# ===== Command Handlers =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /start command - begin the conversation.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: Next conversation state (ASK_NAME)
    """
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started conversation")

    # Check if it's a private chat
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "Please send me a direct message to use this bot. "
            "I don't work in group chats for privacy reasons."
        )
        return ConversationHandler.END

    # Clear any previous conversation data
    context.user_data.clear()

    # Send consent and first prompt
    await update.message.reply_text(
        "Hi! I can store your name, age, and address in my database "
        "to help with future interactions. By continuing, you agree "
        "that I will store these details until you delete them.\n\n"
        "You can reply /cancel anytime to stop.\n\n"
        "Let's get started. What's your full name?"
    )

    return ASK_NAME


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /cancel command - abort the conversation.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: ConversationHandler.END
    """
    user_id = update.effective_user.id
    logger.info(f"User {user_id} cancelled conversation")

    context.user_data.clear()

    await update.message.reply_text(
        "No problem — I've cancelled the current process.\n"
        "Send /start whenever you want to try again."
    )

    return ConversationHandler.END


async def delete_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /delete command - delete user's stored data.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: ConversationHandler.END
    """
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested data deletion")

    try:
        with get_db_session() as session:
            deleted = delete_user(session, user_id)

        if deleted:
            await update.message.reply_text(
                "Your stored details have been deleted.\n"
                "You can provide them again anytime with /start."
            )
        else:
            await update.message.reply_text(
                "No stored data found for your account.\n"
                "You can provide your details with /start."
            )

    except Exception as e:
        logger.error(f"Error deleting user data for {user_id}: {e}")
        await update.message.reply_text(
            "Sorry, there was an error deleting your data. Please try again later."
        )

    return ConversationHandler.END


# ===== Conversation Steps =====

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle name input and proceed to ask age.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: Next conversation state (ASK_AGE or ASK_NAME if invalid)
    """
    user_id = update.effective_user.id
    name = update.message.text

    if not is_valid_name(name):
        logger.info(f"User {user_id} provided invalid name")
        await update.message.reply_text(
            "I couldn't read that name. Please enter your full name\n"
            "(1–100 characters, letters/numbers/spaces allowed)."
        )
        return ASK_NAME

    # Store name in context
    context.user_data['name'] = name.strip()
    logger.info(f"User {user_id} provided valid name")

    await update.message.reply_text(
        f"Great, thanks {name.strip()}.\n"
        f"How old are you? (Please enter a number between 13 and 120)"
    )

    return ASK_AGE


async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle age input and proceed to ask address.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: Next conversation state (ASK_ADDRESS or ASK_AGE if invalid)
    """
    user_id = update.effective_user.id
    age_text = update.message.text

    try:
        age = parse_age(age_text)
        context.user_data['age'] = age
        logger.info(f"User {user_id} provided valid age")

        await update.message.reply_text(
            "Got it. What's your address?\n"
            "(Max 255 characters; you can include apartment/unit, etc.)"
        )

        return ASK_ADDRESS

    except ValueError as e:
        logger.info(f"User {user_id} provided invalid age: {e}")

        # Check if it's a range error or parsing error
        if "out of range" in str(e):
            await update.message.reply_text(
                "Thanks! For this bot, the allowed age is between 13 and 120.\n"
                "Please enter a number in that range."
            )
        else:
            await update.message.reply_text(
                "That doesn't look like a valid age. Please enter a number\n"
                "between 13 and 120 (e.g., 27)."
            )

        return ASK_AGE


async def ask_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle address input, save to database, and end conversation.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: ConversationHandler.END
    """
    user_id = update.effective_user.id
    address = update.message.text

    if not is_valid_address(address):
        logger.info(f"User {user_id} provided invalid address")
        await update.message.reply_text(
            "Please enter a non-empty address up to 255 characters.\n"
            "For example: 123 Main St, Springfield, IL 62704"
        )
        return ASK_ADDRESS

    context.user_data['address'] = address.strip()
    logger.info(f"User {user_id} provided valid address")

    # Save to database
    name = context.user_data['name']
    age = context.user_data['age']
    address = context.user_data['address']

    try:
        with get_db_session() as session:
            user = insert_or_update_user(
                session,
                telegram_user_id=user_id,
                name=name,
                age=age,
                address=address
            )

        logger.info(f"Successfully saved data for user {user_id}")

        await update.message.reply_text(
            "All set! I've saved your details.\n\n"
            f"Name: {name}\n"
            f"Age: {age}\n"
            f"Address: {address}\n\n"
            "You can update these later by sending /start again,\n"
            "or erase them anytime with /delete."
        )

    except Exception as e:
        logger.error(f"Error saving user data for {user_id}: {e}")
        await update.message.reply_text(
            "Sorry, there was an error saving your data. Please try again later."
        )

    # Clear conversation data
    context.user_data.clear()

    return ConversationHandler.END


# ===== Create the ConversationHandler =====

def create_conversation_handler() -> ConversationHandler:
    """
    Create and configure the conversation handler.

    Returns:
        ConversationHandler: Configured conversation handler
    """
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_address)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),  # Allow restarting
        ],
        conversation_timeout=600,  # 10 minutes
    )
