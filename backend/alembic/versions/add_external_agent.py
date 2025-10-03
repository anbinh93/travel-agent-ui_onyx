"""Add external_agent table

Revision ID: add_external_agent
Revises: 
Create Date: 2025-01-03 14:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_external_agent_001'
down_revision = '2b75d0a8ffcb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create external_agent table
    op.create_table(
        'external_agent',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('api_endpoint', sa.String(), nullable=False),
        sa.Column('api_key', sa.String(), nullable=True),
        sa.Column('auth_type', sa.String(), nullable=False, server_default='bearer'),
        sa.Column('default_model', sa.String(), nullable=True),
        sa.Column('default_temperature', sa.Float(), nullable=True, server_default='0.7'),
        sa.Column('default_max_tokens', sa.Integer(), nullable=True, server_default='2000'),
        sa.Column('supports_streaming', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('system_prompt', sa.String(), nullable=True),
        sa.Column('additional_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('icon_color', sa.String(), nullable=True),
        sa.Column('icon_emoji', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_test_status', sa.String(), nullable=True),
        sa.Column('last_test_error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_external_agent_name'), 'external_agent', ['name'], unique=True)
    op.create_index(op.f('ix_external_agent_is_active'), 'external_agent', ['is_active'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_external_agent_is_active'), table_name='external_agent')
    op.drop_index(op.f('ix_external_agent_name'), table_name='external_agent')
    # Drop table
    op.drop_table('external_agent')
