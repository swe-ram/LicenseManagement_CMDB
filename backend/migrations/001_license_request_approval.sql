ALTER TABLE license_requests
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(64);

ALTER TABLE license_requests
    ADD COLUMN IF NOT EXISTS urgency VARCHAR(64) NOT NULL DEFAULT 'Standard';

ALTER TABLE license_requests
    ADD COLUMN IF NOT EXISTS requester_identity VARCHAR(255);

ALTER TABLE license_requests
    ALTER COLUMN approver_id DROP NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT request_number
        FROM license_requests
        GROUP BY request_number
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Cannot enforce unique license request numbers: duplicate request_number values exist.';
    END IF;
END
$$;

CREATE UNIQUE INDEX IF NOT EXISTS ix_license_requests_request_number
    ON license_requests (request_number);

CREATE UNIQUE INDEX IF NOT EXISTS uq_license_requests_employee_idempotency
    ON license_requests (employee_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;
