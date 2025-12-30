"""admin notifs

Revision ID: 3c4d5e6f7a8b
Revises: 2b231de97dc3
Create Date: 2025-12-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c4d5e6f7a8b'
down_revision = '2b231de97dc3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    
    op.add_column('admins', sa.Column('usage_warning_percent', sa.Integer(), nullable=True))
    op.add_column('admins', sa.Column('days_warning', sa.Integer(), nullable=True))
    op.execute('''
        UPDATE admins SET usage_warning_percent = 80, days_warning = 3
    ''')

def downgrade() -> None:
    op.drop_column('admins', 'days_warning')
    op.drop_column('admins', 'usage_warning_percent')
