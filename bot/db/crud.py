"""
CRUD operations for the User model.
"""
from typing import Optional

from sqlalchemy.orm import Session

from bot.db.models import User
from bot.logging_config import get_logger

logger = get_logger(__name__)


def insert_or_update_user(
    session: Session,
    telegram_user_id: int,
    name: str,
    age: int,
    address: str
) -> User:
    """
    Insert a new user or update an existing user's information.

    Args:
        session: SQLAlchemy database session
        telegram_user_id: Telegram user ID (unique identifier)
        name: User's full name
        age: User's age
        address: User's address

    Returns:
        User: The created or updated User object

    Raises:
        Exception: If database operation fails
    """
    try:
        # Try to find existing user
        user = session.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()

        if user:
            # Update existing user
            logger.info(f"Updating user data for telegram_user_id={telegram_user_id}")
            user.name = name
            user.age = age
            user.address = address
        else:
            # Create new user
            logger.info(f"Creating new user record for telegram_user_id={telegram_user_id}")
            user = User(
                telegram_user_id=telegram_user_id,
                name=name,
                age=age,
                address=address
            )
            session.add(user)

        session.flush()  # Flush to get the updated values
        return user

    except Exception as e:
        logger.error(f"Error upserting user {telegram_user_id}: {e}")
        raise


def delete_user(session: Session, telegram_user_id: int) -> bool:
    """
    Delete a user by their Telegram user ID.

    Args:
        session: SQLAlchemy database session
        telegram_user_id: Telegram user ID

    Returns:
        bool: True if user was deleted, False if user was not found

    Raises:
        Exception: If database operation fails
    """
    try:
        user = session.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()

        if user:
            logger.info(f"Deleting user record for telegram_user_id={telegram_user_id}")
            session.delete(user)
            session.flush()
            return True
        else:
            logger.info(f"No user found to delete for telegram_user_id={telegram_user_id}")
            return False

    except Exception as e:
        logger.error(f"Error deleting user {telegram_user_id}: {e}")
        raise


def get_user(session: Session, telegram_user_id: int) -> Optional[User]:
    """
    Get a user by their Telegram user ID.

    Args:
        session: SQLAlchemy database session
        telegram_user_id: Telegram user ID

    Returns:
        Optional[User]: The User object if found, None otherwise
    """
    try:
        return session.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
    except Exception as e:
        logger.error(f"Error retrieving user {telegram_user_id}: {e}")
        raise
