"""Manually updating status column

Revision ID: f8e897a19b76
Revises: ee3bc016a4bc
Create Date: 2025-02-23 21:46:28.215910

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8e897a19b76'
down_revision = 'ee3bc016a4bc'
branch_labels = None
depends_on = None


def upgrade():
    # Create a new column with the correct constraints
    op.add_column('payments', sa.Column('status_new', sa.String(), nullable=False, server_default="pending"))
    
    # Copy data from old column to new column
    op.execute('UPDATE payments SET status_new = status')

    # Drop the old column
    op.drop_column('payments', 'status')

    # Rename the new column to match the original column name
    op.alter_column('payments', 'status_new', new_column_name='status')

def downgrade():
    op.add_column('payments', sa.Column('status_old', sa.String(), nullable=True))
    op.execute('UPDATE payments SET status_old = status')
    op.drop_column('payments', 'status')
    op.alter_column('payments', 'status_old', new_column_name='status')