"""Add description and objective to project table

Revision ID: add_project_desc_obj
Revises: 
Create Date: 2024-12-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_project_desc_obj'
down_revision = None  # Update this if you have previous migrations
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add description column if not exists
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='project' AND column_name='description'
            ) THEN
                ALTER TABLE project ADD COLUMN description TEXT;
            END IF;
        END $$;
    """)
    
    # Add objective column if not exists
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='project' AND column_name='objective'
            ) THEN
                ALTER TABLE project ADD COLUMN objective TEXT;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop columns if they exist
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='project' AND column_name='objective'
            ) THEN
                ALTER TABLE project DROP COLUMN objective;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='project' AND column_name='description'
            ) THEN
                ALTER TABLE project DROP COLUMN description;
            END IF;
        END $$;
    """)

