-- =============================================
-- 030: In-app Coach Conversations
-- Tables for the conversational coach surface in the React app.
-- A Mac-side daemon (scripts/coach_relay.py) watches for pending user
-- turns and writes assistant responses back via the service role.
-- =============================================

CREATE TABLE IF NOT EXISTS coach_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    title TEXT,
    cli_session_id UUID NOT NULL DEFAULT gen_random_uuid(),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived'))
);

CREATE TABLE IF NOT EXISTS coach_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES coach_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'complete' CHECK (status IN ('pending', 'in_progress', 'complete', 'error')),
    error TEXT,
    context_snapshot JSONB,
    kb_refs TEXT[]
);

CREATE INDEX IF NOT EXISTS idx_coach_turns_conversation ON coach_turns (conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_coach_turns_pending ON coach_turns (status, created_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_coach_conversations_status ON coach_conversations (status, started_at DESC);

ALTER TABLE coach_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE coach_turns ENABLE ROW LEVEL SECURITY;

-- Single-athlete app: anon can read everything, insert conversations and user turns.
-- Only service_role (the Mac daemon) can insert assistant turns or update status.
CREATE POLICY "anon_read_conversations" ON coach_conversations
    FOR SELECT TO anon USING (true);

CREATE POLICY "anon_insert_conversations" ON coach_conversations
    FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_update_conversations" ON coach_conversations
    FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "anon_read_turns" ON coach_turns
    FOR SELECT TO anon USING (true);

-- Anon can only insert USER turns; assistant turns are service_role only.
CREATE POLICY "anon_insert_user_turns" ON coach_turns
    FOR INSERT TO anon WITH CHECK (role = 'user');
