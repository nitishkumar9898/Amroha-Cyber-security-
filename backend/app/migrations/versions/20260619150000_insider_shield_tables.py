'''sql
"""Create insider_shield tables
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

# revision identifiers, used by Alembic.
revision = '20260619150000'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'user_behavior_baselines',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False, index=True),
        sa.Column('feature_vector', pg.JSONB, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'access_events',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False, index=True),
        sa.Column('resource', sa.String, nullable=False),
        sa.Column('action', sa.String, nullable=False),
        sa.Column('outcome', sa.String, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'exfiltration_events',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False, index=True),
        sa.Column('data_size_bytes', sa.Integer, nullable=False),
        sa.Column('entropy', sa.Float, nullable=True),
        sa.Column('details', pg.JSONB, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'psych_profiles',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False, unique=True),
        sa.Column('profile_json', pg.JSONB, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'risk_scores',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False, index=True),
        sa.Column('score', sa.Float, nullable=False),
        sa.Column('reason', sa.String, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'insider_alerts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('severity', sa.String, nullable=False),
        sa.Column('message', sa.String, nullable=False),
        sa.Column('payload', pg.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('acknowledged', sa.DateTime, nullable=True),
    )

def downgrade():
    op.drop_table('insider_alerts')
    op.drop_table('risk_scores')
    op.drop_table('psych_profiles')
    op.drop_table('exfiltration_events')
    op.drop_table('access_events')
    op.drop_table('user_behavior_baselines')
'''
