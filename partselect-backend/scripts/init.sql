
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";     -- Generate UUIDs
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- Fuzzy text search

-- Products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    part_number VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL CHECK (category IN ('refrigerator', 'dishwasher')),
    brand VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    in_stock BOOLEAN DEFAULT TRUE,
    image_urls JSONB DEFAULT '[]'::jsonb,
    specifications JSONB DEFAULT '{}'::jsonb,
    rating DECIMAL(3, 2),
    reviews_count INTEGER DEFAULT 0,
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', name || ' ' || COALESCE(description, ''))
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_products_part_number ON products(part_number);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_search ON products USING GIN(search_vector);
CREATE INDEX idx_products_name_trgm ON products USING gin(name gin_trgm_ops);

-- Compatibility table
CREATE TABLE compatibility (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    part_number VARCHAR(50) REFERENCES products(part_number) ON DELETE CASCADE,
    model_number VARCHAR(100) NOT NULL,
    brand VARCHAR(100),
    compatible BOOLEAN DEFAULT TRUE,
    confidence_score DECIMAL(3, 2) DEFAULT 1.0,
    source VARCHAR(50) DEFAULT 'manual',
    notes TEXT,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(part_number, model_number)
);

CREATE INDEX idx_compat_part ON compatibility(part_number);
CREATE INDEX idx_compat_model ON compatibility(model_number);

-- Installation guides
CREATE TABLE installation_guides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    part_number VARCHAR(50) REFERENCES products(part_number) ON DELETE CASCADE,
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'moderate', 'hard')),
    estimated_time_minutes INTEGER,
    tools_required JSONB DEFAULT '[]'::jsonb,
    video_url VARCHAR(500),
    pdf_url VARCHAR(500),
    chromadb_doc_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_install_part ON installation_guides(part_number);

-- Troubleshooting KB
CREATE TABLE troubleshooting_kb (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appliance_type VARCHAR(50) CHECK (appliance_type IN ('refrigerator', 'dishwasher')),
    brand VARCHAR(100),
    issue_title VARCHAR(255) NOT NULL,
    symptoms JSONB DEFAULT '[]'::jsonb,
    possible_causes JSONB DEFAULT '[]'::jsonb,
    diagnostic_steps JSONB DEFAULT '[]'::jsonb,
    recommended_parts JSONB DEFAULT '[]'::jsonb,
    chromadb_doc_id VARCHAR(100),
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ts_appliance ON troubleshooting_kb(appliance_type);
CREATE INDEX idx_ts_brand ON troubleshooting_kb(brand);

-- Conversations (for LangGraph state)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    state JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_thread ON conversations(thread_id);
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);

-- Auto-update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_installation_guides_updated_at BEFORE UPDATE ON installation_guides
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Seed data
INSERT INTO products (part_number, name, description, category, price, brand, in_stock)
VALUES 
    ('PS11752778', 'Ice Maker Assembly', 
     'Replacement ice maker assembly for refrigerators. Includes mounting bracket and wire harness.',
     'refrigerator', 89.99, 'Whirlpool', true),
    ('WPW10408179', 'Water Inlet Valve', 
     'Water inlet valve controls water flow to ice maker and dispenser.',
     'refrigerator', 45.50, 'Whirlpool', true)
ON CONFLICT (part_number) DO NOTHING;

INSERT INTO compatibility (part_number, model_number, brand, compatible, confidence_score, source)
VALUES
    ('PS11752778', 'WDT780SAEM1', 'Whirlpool', true, 1.0, 'manufacturer'),
    ('PS11752778', 'WDT750SAHZ0', 'Whirlpool', true, 1.0, 'manufacturer')
ON CONFLICT (part_number, model_number) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✓ Database initialized successfully with schema and seed data!';
END $$;