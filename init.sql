-- Database initialization script
-- This file is executed when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist (this is handled by POSTGRES_DB env var)
-- CREATE DATABASE IF NOT EXISTS noti_db;

-- Create user if it doesn't exist (this is handled by POSTGRES_USER env var)
-- CREATE USER IF NOT EXISTS noti_user WITH PASSWORD 'noti_password';

-- Grant privileges
-- GRANT ALL PRIVILEGES ON DATABASE noti_db TO noti_user;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';
