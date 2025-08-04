"""add_case_info_table

Revision ID: 0c9b261a87d8
Revises: 11f2bfaf9bc0
Create Date: 2025-08-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c9b261a87d8'
down_revision: Union[str, None] = '11f2bfaf9bc0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create cases table
    op.create_table(
        'cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_number', sa.String(length=100), nullable=False, comment='案号'),
        sa.Column('applicant', sa.String(length=100), nullable=False, comment='申请人'),
        sa.Column('respondent', sa.String(length=100), nullable=False, comment='被申请人'),
        sa.Column('third_party', sa.String(length=100), nullable=True, comment='第三人'),
        sa.Column('applicant_address', sa.String(length=500), nullable=False, comment='申请人联系地址'),
        sa.Column('respondent_address', sa.String(length=500), nullable=False, comment='被申请人联系地址'),
        sa.Column('third_party_address', sa.String(length=500), nullable=True, comment='第三人联系地址'),
        sa.Column('closure_date', sa.Date(), nullable=True, comment='结案日期'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='状态'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cases_id'), 'cases', ['id'], unique=False)
    op.create_index('ix_cases_case_number', 'cases', ['case_number'], unique=True)
    op.create_index('ix_cases_status', 'cases', ['status'], unique=False)
    op.create_index('ix_cases_created_at', 'cases', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop cases table
    op.drop_index('ix_cases_created_at', table_name='cases')
    op.drop_index('ix_cases_status', table_name='cases')
    op.drop_index('ix_cases_case_number', table_name='cases')
    op.drop_index(op.f('ix_cases_id'), table_name='cases')
    op.drop_table('cases')