"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='lawyer'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('jurisdiction', sa.String(50), nullable=True),
        sa.Column('practice_area', sa.String(100), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('doc_metadata', sa.JSON(), nullable=True),
        sa.Column('indexing_status', sa.String(50), nullable=True, server_default='pending'),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_id', 'documents', ['id'])
    op.create_index('ix_documents_document_type', 'documents', ['document_type'])
    op.create_index('ix_documents_jurisdiction', 'documents', ['jurisdiction'])
    op.create_index('ix_documents_practice_area', 'documents', ['practice_area'])
    op.create_index('idx_document_type_jurisdiction', 'documents', ['document_type', 'jurisdiction'])
    
    # Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('start_char', sa.Integer(), nullable=True),
        sa.Column('end_char', sa.Integer(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_chunks_id', 'document_chunks', ['id'])
    op.create_index('idx_chunk_document', 'document_chunks', ['document_id', 'chunk_index'])
    
    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('jurisdiction', sa.String(50), nullable=True),
        sa.Column('mode', sa.String(50), nullable=True, server_default='question'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_sessions_id', 'chat_sessions', ['id'])
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_messages_id', 'chat_messages', ['id'])
    
    # Create templates table
    op.create_table(
        'templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('jurisdiction', sa.String(50), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('form_schema', sa.JSON(), nullable=False),
        sa.Column('optional_sections', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_templates_id', 'templates', ['id'])
    op.create_index('ix_templates_category', 'templates', ['category'])
    op.create_index('ix_templates_jurisdiction', 'templates', ['jurisdiction'])
    
    # Create due_diligence_checks table
    op.create_table(
        'due_diligence_checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_name', sa.String(500), nullable=False),
        sa.Column('check_type', sa.String(50), nullable=False),
        sa.Column('jurisdiction', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=True, server_default='pending'),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('risk_indicators', sa.JSON(), nullable=True),
        sa.Column('risk_items', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_due_diligence_checks_id', 'due_diligence_checks', ['id'])
    op.create_index('ix_due_diligence_checks_check_type', 'due_diligence_checks', ['check_type'])
    op.create_index('ix_due_diligence_checks_jurisdiction', 'due_diligence_checks', ['jurisdiction'])
    op.create_index('ix_due_diligence_checks_status', 'due_diligence_checks', ['status'])
    
    # Create clauses table
    op.create_table(
        'clauses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('jurisdiction', sa.String(50), nullable=True),
        sa.Column('practice_area', sa.String(100), nullable=True),
        sa.Column('language', sa.String(10), nullable=True, server_default='ru'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_clauses_id', 'clauses', ['id'])
    op.create_index('ix_clauses_category', 'clauses', ['category'])
    op.create_index('ix_clauses_jurisdiction', 'clauses', ['jurisdiction'])
    op.create_index('ix_clauses_practice_area', 'clauses', ['practice_area'])
    op.create_index('idx_clause_category_jurisdiction', 'clauses', ['category', 'jurisdiction'])


def downgrade() -> None:
    op.drop_table('clauses')
    op.drop_table('due_diligence_checks')
    op.drop_table('templates')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS vector')

