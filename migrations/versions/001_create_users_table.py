"""create users table

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users table."""
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(),
            server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
            nullable=False
        ),
        sa.CheckConstraint('age >= 13 AND age <= 120', name='age_range_check'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_user_id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # Create index on telegram_user_id for faster lookups
    op.create_index(
        'ix_users_telegram_user_id',
        'users',
        ['telegram_user_id'],
        unique=True
    )


def downgrade() -> None:
    """Drop users table."""
    op.drop_index('ix_users_telegram_user_id', table_name='users')
    op.drop_table('users')
