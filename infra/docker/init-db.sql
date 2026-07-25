-- Healthcare OS — Database initialization
-- Runs on first container start to set up extensions.

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Enable btree_gin for composite indexes
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create a notice that initialization is complete
DO $$
BEGIN
    RAISE NOTICE 'Healthcare OS database initialized successfully.';
END $$;
