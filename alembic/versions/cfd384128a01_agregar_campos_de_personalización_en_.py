"""Agregar campos de personalización en tenants

Revision ID: cfd384128a01
Revises: c008d931f68f
Create Date: 2025-01-31 13:54:31.400504

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cfd384128a01'
down_revision: Union[str, None] = 'c008d931f68f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tenants', sa.Column('nombre_camarero', sa.String(length=50), nullable=True))
    op.add_column('tenants', sa.Column('nombre_local', sa.String(length=100), nullable=True))
    op.add_column('tenants', sa.Column('numero_mesa_minimo', sa.Integer(), nullable=True))
    op.add_column('tenants', sa.Column('numero_mesa_maximo', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tenants', 'numero_mesa_maximo')
    op.drop_column('tenants', 'numero_mesa_minimo')
    op.drop_column('tenants', 'nombre_local')
    op.drop_column('tenants', 'nombre_camarero')
    # ### end Alembic commands ###
