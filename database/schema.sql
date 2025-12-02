
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY
);


CREATE TABLE items (
    item_id VARCHAR(50) PRIMARY KEY
);


CREATE TABLE interactions (
    interaction_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    item_id VARCHAR(50) NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
    rating NUMERIC NOT NULL,
    timestamp BIGINT NOT NULL
);


CREATE TABLE recommendations (
    user_id VARCHAR(50) PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    recommended_items JSONB NOT NULL,
    computed_at TIMESTAMP DEFAULT NOW()
);


CREATE TABLE local_requests (
    request_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    timestamp BIGINT NOT NULL,
    latency_ms NUMERIC NOT NULL,
    limit_val INT NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT
);


-- interactions
CREATE INDEX idx_interactions_user_id ON interactions (user_id);
CREATE INDEX idx_interactions_item_id ON interactions (item_id);
CREATE INDEX idx_interactions_timestamp ON interactions (timestamp);

-- local_requests
CREATE INDEX idx_local_requests_user_id ON local_requests (user_id);
CREATE INDEX idx_local_requests_timestamp ON local_requests (timestamp);


