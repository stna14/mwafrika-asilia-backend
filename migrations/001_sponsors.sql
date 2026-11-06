-- Approval required before execution. MySQL 8 / InnoDB.
-- Preflight: media_files must exist; sponsors must not exist.
-- DDL auto-commits in MySQL. This creates one empty table, no seed records.
CREATE TABLE sponsors (
 id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(180) NOT NULL,
 logo_media_id BIGINT NULL,
 website_url VARCHAR(500) NULL,
 description TEXT NULL,
 display_order INT NOT NULL DEFAULT 0,
 is_active BOOLEAN NOT NULL DEFAULT TRUE,
 publish_status VARCHAR(20) NOT NULL DEFAULT 'draft',
 created_at DATETIME NOT NULL,
 updated_at DATETIME NOT NULL,
 CONSTRAINT fk_sponsors_logo FOREIGN KEY (logo_media_id) REFERENCES media_files(id) ON DELETE RESTRICT,
 CONSTRAINT ck_sponsors_publication CHECK (publish_status IN ('draft','published')),
 CONSTRAINT ck_sponsors_order CHECK (display_order >= 0),
 INDEX ix_sponsors_public_order (is_active,publish_status,display_order,id)
) ENGINE=InnoDB;
-- Rollback (separate approval, only if no sponsor data must be retained): DROP TABLE sponsors;
