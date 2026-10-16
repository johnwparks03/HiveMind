-- E6-S2: central chunk index (pgvector). Chunk text and 384-dim embeddings of published files,
-- searched by POST /retrieval/search. Rows are removed with their file by cascade.

CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;

CREATE TABLE public_chunks (
    file_id     text    NOT NULL REFERENCES public_files(file_id) ON DELETE CASCADE,
    chunk_index integer NOT NULL,
    text        text    NOT NULL,
    embedding   vector(384) NOT NULL,
    PRIMARY KEY (file_id, chunk_index)
);

CREATE INDEX idx_public_chunks_embedding ON public_chunks USING hnsw (embedding vector_cosine_ops);

-- Null until a chunk upload commits (PUT /files/{id}/chunks, final batch).
ALTER TABLE public_files ADD COLUMN chunks_indexed_at timestamptz, ADD COLUMN chunk_count integer;
