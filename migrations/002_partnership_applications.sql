-- Explicit approval required before execution. MySQL 8 / InnoDB.
-- Preflight: partnership_applications must not exist. Adds one empty table only.
-- MySQL DDL auto-commits. This script never seeds or modifies existing records.
CREATE TABLE partnership_applications (
 id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 public_id VARCHAR(64) NOT NULL,
 contact_name VARCHAR(180) NOT NULL,
 email VARCHAR(180) NOT NULL,
 phone VARCHAR(32) NOT NULL,
 organization VARCHAR(180) NOT NULL,
 organization_type VARCHAR(80) NOT NULL,
 website_url VARCHAR(500) NULL,
 partnership_type VARCHAR(120) NOT NULL,
 proposal TEXT NOT NULL,
 proposed_contribution TEXT NULL,
 timeline VARCHAR(180) NOT NULL,
 proposal_url VARCHAR(500) NULL,
 consent BOOLEAN NOT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'submitted',
 admin_notes TEXT NULL,
 created_at DATETIME NOT NULL,
 updated_at DATETIME NOT NULL,
 UNIQUE INDEX ix_partnership_applications_public_id (public_id),
 INDEX ix_partnership_applications_email (email),
 INDEX ix_partnership_applications_status (status),
 INDEX ix_partnership_applications_created_at (created_at),
 CONSTRAINT ck_partnership_consent CHECK (consent = TRUE),
 CONSTRAINT ck_partnership_status CHECK (status IN ('submitted','under_review','shortlisted','approved','rejected'))
) ENGINE=InnoDB;
-- Rollback requires separate approval and retention review: DROP TABLE partnership_applications;
