"""add_activity_log_table

Revision ID: 11f2bfaf9bc0
Revises: 79e2ac959f72
Create Date: 2025-08-04 02:01:03.789061

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11f2bfaf9bc0'
down_revision: Union[str, None] = '79e2ac959f72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create activity_logs table
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False, comment='动作类型'),
        sa.Column('description', sa.Text(), nullable=False, comment='动作描述'),
        sa.Column('entity_type', sa.String(length=50), nullable=True, comment='实体类型'),
        sa.Column('entity_id', sa.String(length=100), nullable=True, comment='实体ID'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='状态: success, info, warning, error'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_logs_id'), 'activity_logs', ['id'], unique=False)
    op.create_index('ix_activity_logs_created_at', 'activity_logs', ['created_at'], unique=False)
    op.create_index('ix_activity_logs_action_type', 'activity_logs', ['action_type'], unique=False)
    op.create_index('ix_activity_logs_user_id', 'activity_logs', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop activity_logs table
    op.drop_index('ix_activity_logs_user_id', table_name='activity_logs')
    op.drop_index('ix_activity_logs_action_type', table_name='activity_logs')
    op.drop_index('ix_activity_logs_created_at', table_name='activity_logs')
    op.drop_index(op.f('ix_activity_logs_id'), table_name='activity_logs')
    op.drop_table('activity_logs')
