"""Added likes YOU NEED TO pip install Flask-Migrate

Revision ID: c5fde97e45fd
Revises: 
Create Date: 2025-04-05 22:13:34.126968

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5fde97e45fd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('listing', schema=None) as batch_op:
        batch_op.add_column(sa.Column('likes', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('listing', schema=None) as batch_op:
        batch_op.drop_column('likes')

    # ### end Alembic commands ###
