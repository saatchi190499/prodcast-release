-- AI Documents compatibility migration, based on prodcast-ai f9be817 docker/init.sql.
-- Run in a transaction as the prodcast_ai role, after installing pgvector.
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY, source_path TEXT NOT NULL UNIQUE,
    allowed_principals TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    content_sha256 TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0), content TEXT NOT NULL,
    embedding vector(1024), page INTEGER, section TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE (document_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks USING hnsw (embedding vector_cosine_ops);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS allowed_principals TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];
ALTER TABLE document_chunks ALTER COLUMN embedding DROP NOT NULL;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS page INTEGER;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS section TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS document_acl_idx ON documents USING gin (allowed_principals);
CREATE INDEX IF NOT EXISTS document_text_idx ON document_chunks USING gin (to_tsvector('simple',content));
ALTER TABLE documents ADD COLUMN IF NOT EXISTS display_name TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS managed_file TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS byte_size BIGINT NOT NULL DEFAULT 0;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'ready';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS error_message TEXT NOT NULL DEFAULT '';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS indexed_at TIMESTAMPTZ;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS job_version BIGINT NOT NULL DEFAULT 0;
UPDATE documents SET display_name=regexp_replace(source_path, '^.*/', '') WHERE display_name IS NULL;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS modules TEXT[] NOT NULL DEFAULT ARRAY['chat']::TEXT[];
