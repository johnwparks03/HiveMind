-- E4-S2: transfer API.

-- Why a transfer failed, as the contract's error_code (owner_unresponsive | file_unavailable |
-- upload_failed). size_bytes is what the owner reported on completion.
ALTER TABLE transfers ADD COLUMN error_code text, ADD COLUMN size_bytes bigint;

-- One in-flight transfer per (file, requester): a duplicate request reuses it, and two
-- concurrent requests cannot both insert.
CREATE UNIQUE INDEX uq_transfers_in_flight ON transfers (file_id, requester_id)
    WHERE status IN ('requested', 'uploading', 'ready');

-- Access log stays ids-only; transfer requests also record which transfer and a short outcome
-- code (requested | reused | owner_offline | send_failed). Never filenames or content.
ALTER TABLE access_log ADD COLUMN transfer_id uuid, ADD COLUMN outcome text;
