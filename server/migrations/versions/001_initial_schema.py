"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-10-26

Creates all initial tables:
- documents: Store uploaded documents
- vectors: Store document embeddings and chunks
- chats: Store chat sessions
- messages: Store chat messages
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('file_name', sa.Text(), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('file_type', sa.Text(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('upload_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('chunk_count', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('status', sa.Text(), server_default=sa.text("'pending'"), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_documents_upload_date', 'documents', ['upload_date'])

    # Create vectors table
    op.create_table(
        'vectors',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('doc_id', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', sa.LargeBinary(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_vectors_doc_id', 'vectors', ['doc_id'])

    # Create chats table
    op.create_table(
        'chats',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('documents', sa.Text(), server_default=sa.text("'[]'"), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chats_updated_at', 'chats', ['updated_at'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('chat_id', sa.Text(), nullable=False),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources', sa.Text(), nullable=True),
        sa.Column('model_used', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_messages_chat_id', 'messages', ['chat_id'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('idx_messages_chat_id', table_name='messages')
    op.drop_table('messages')

    op.drop_index('idx_chats_updated_at', table_name='chats')
    op.drop_table('chats')

    op.drop_index('idx_vectors_doc_id', table_name='vectors')
    op.drop_table('vectors')

    op.drop_index('idx_documents_upload_date', table_name='documents')
    op.drop_table('documents')
