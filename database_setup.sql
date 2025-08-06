-- Database setup for DollarPunk
-- Run this script to create the database and user

-- Create database
CREATE DATABASE IF NOT EXISTS dollarpunk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (change password as needed)
CREATE USER IF NOT EXISTS 'dollarpunk_user'@'localhost' IDENTIFIED BY 'dollarpunk_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON dollarpunk.* TO 'dollarpunk_user'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;

-- Use the database
USE dollarpunk;

-- The tables will be created automatically by the application
-- This is just for reference:

/*
CREATE TABLE IF NOT EXISTS data_points (
    id VARCHAR(255) PRIMARY KEY,
    content TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    timestamp DATETIME(3) NOT NULL,
    theme VARCHAR(50) NOT NULL,
    author VARCHAR(255) NOT NULL,
    url TEXT,
    engagement_likes INT DEFAULT 0,
    engagement_shares INT DEFAULT 0,
    engagement_comments INT DEFAULT 0,
    engagement_views INT DEFAULT 0,
    language VARCHAR(10) DEFAULT 'en',
    sentiment_score DECIMAL(5,4),
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    updated_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    INDEX idx_platform (platform),
    INDEX idx_theme (theme),
    INDEX idx_timestamp (timestamp),
    INDEX idx_sentiment (sentiment_score)
);

CREATE TABLE IF NOT EXISTS collection_sessions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM('running', 'completed', 'failed', 'cancelled') DEFAULT 'running',
    start_time DATETIME(3) NOT NULL,
    end_time DATETIME(3),
    total_points INT DEFAULT 0,
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    updated_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
);

CREATE TABLE IF NOT EXISTS alpha_vantage_queries (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36),
    topics TEXT NOT NULL,
    limit_count INT DEFAULT 50,
    api_key_hash VARCHAR(64) NOT NULL,
    query_time DATETIME(3) NOT NULL,
    points_retrieved INT DEFAULT 0,
    status ENUM('success', 'failed', 'partial') DEFAULT 'success',
    error_message TEXT,
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (session_id) REFERENCES collection_sessions(id) ON DELETE SET NULL,
    INDEX idx_session (session_id),
    INDEX idx_query_time (query_time)
);
*/

-- Show the created database
SHOW DATABASES LIKE 'dollarpunk'; 