-- AstroAgent Initial Schema
-- Run this in Supabase SQL Editor

-- Users table (custom auth, not Supabase Auth)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    default_language TEXT DEFAULT 'en',
    chart_format TEXT DEFAULT 'south_indian',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Family Vault: birth profiles
CREATE TABLE IF NOT EXISTS birth_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    relationship TEXT,
    birth_date DATE NOT NULL,
    birth_time TIME,
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    timezone TEXT NOT NULL,
    place_name TEXT,
    computed_chart JSONB,
    computed_dashas JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    profile_id UUID REFERENCES birth_profiles(id) ON DELETE SET NULL,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    language TEXT,
    tool_calls JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_profiles_user ON birth_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
