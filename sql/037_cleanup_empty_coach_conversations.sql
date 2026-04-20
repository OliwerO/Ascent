-- =============================================
-- 037_cleanup_empty_coach_conversations.sql
-- =============================================
-- Delete coach conversations that have zero turns. Caused by an earlier
-- version of CoachView where tapping "+" eagerly created a DB row before
-- the first message was sent. Current version only creates on send, so
-- this is a one-shot cleanup — safe to re-run (idempotent).
-- =============================================

DELETE FROM coach_conversations
WHERE id IN (
    SELECT c.id
    FROM coach_conversations c
    LEFT JOIN coach_turns t ON t.conversation_id = c.id
    WHERE t.id IS NULL
);
