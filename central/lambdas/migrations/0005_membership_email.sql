-- Group members list: show teammates by email. Cognito can't be queried from the VPC Lambdas
-- (no NAT), so each agent reports its own email. Nullable: existing members fill it in on their next GET /team.
ALTER TABLE memberships ADD COLUMN email text;
