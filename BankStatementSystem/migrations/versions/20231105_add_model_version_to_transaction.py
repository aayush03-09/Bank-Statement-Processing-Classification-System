from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20231105_add_model_version_to_transaction'
down_revision = None  # replace with actual previous revision if needed
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('transactions', sa.Column('model_version', sa.String(length=64), nullable=True))

def downgrade():
    op.drop_column('transactions', 'model_version')
