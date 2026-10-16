-- E6-S3: staging area for batched chunk uploads (PUT /files/{id}/chunks). Batches accumulate here and
-- are swapped into public_chunks in one transaction on the final batch, so readers never see a
-- partial set. Rows cascade with the file; the sweeper clears abandoned uploads.

CREATE TABLE public_chunks_staging (
    file_id       text        NOT NULL REFERENCES public_files(file_id) ON DELETE CASCADE,
    chunk_index   integer     NOT NULL,
    batch         integer     NOT NULL,
    total_batches integer     NOT NULL,
    text          text        NOT NULL,
    embedding     vector(384) NOT NULL,
    staged_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (file_id, chunk_index)
);

CREATE INDEX idx_public_chunks_staging_staged_at ON public_chunks_staging (staged_at);
