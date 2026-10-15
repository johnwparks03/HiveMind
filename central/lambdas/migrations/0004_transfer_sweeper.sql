-- E4-S5: transfer sweeper.

-- Set once the sweeper has deleted the transfer's S3 object. Rows with swept_at set are never
-- looked at again, which is what makes a run idempotent.
ALTER TABLE transfers ADD COLUMN swept_at timestamptz;

-- The sweeper's only scan: transfers whose object may still exist, oldest first.
CREATE INDEX idx_transfers_unswept ON transfers (created_at) WHERE swept_at IS NULL;
