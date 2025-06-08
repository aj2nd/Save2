"""
Create transactions table

Version: 1.0.0
Created: 2025-06-08 23:48:20
Author: anandhu723

Revision ID: 001_create_transactions
Revises: 
Create Date: 2025-06-08 23:48:20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '001_create_transactions'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='AED'),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('user_id', UUID(), nullable=False),
        sa.Column('blockchain_hash', sa.String(66), nullable=True),
        sa.Column('metadata', JSONB(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('idx_transactions_type', 'transactions', ['type'])
    op.create_index('idx_transactions_status', 'transactions', ['status'])
    op.create_index('idx_transactions_timestamp', 'transactions', ['timestamp'])
    op.create_index('idx_transactions_blockchain_hash', 'transactions', ['blockchain_hash'])
    
    # Create updated_at trigger function
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """)
    
    # Create trigger
    op.execute("""
    CREATE TRIGGER update_transactions_updated_at
        BEFORE UPDATE ON transactions
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

def downgrade():
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_transactions_updated_at ON transactions")
    
    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop indexes
    op.drop_index('idx_transactions_blockchain_hash')
    op.drop_index('idx_transactions_timestamp')
    op.drop_index('idx_transactions_status')
    op.drop_index('idx_transactions_type')
    op.drop_index('idx_transactions_user_id')
    
    # Drop table
    op.drop_table('transactions')
