import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import { MessageCircle, Send, Plus, AlertCircle, Loader2, Check, X } from 'lucide-react'
import { LoadingState } from '../components/LoadingState'
import {
  useCoachConversations,
  useCoachTurns,
  createCoachConversation,
  sendCoachMessage,
} from '../hooks/useSupabase'
import type { CoachConversation, CoachTurn } from '../lib/types'

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function TurnBubble({ turn, onConfirm, onReject }: {
  turn: CoachTurn
  onConfirm?: () => void
  onReject?: () => void
}) {
  const isUser = turn.role === 'user'
  const isError = turn.status === 'error'
  const isPending = turn.status === 'pending' || turn.status === 'in_progress'

  const snapshot = turn.context_snapshot as Record<string, unknown> | null
  const proposal = snapshot?.proposal as Record<string, unknown> | undefined
  const proposalExecuted = snapshot?.proposal_executed as boolean | undefined
  const hasActiveProposal = proposal && !proposalExecuted

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-[13px] leading-relaxed ${
          isUser
            ? 'bg-accent-green/20 text-text-primary border border-accent-green/30'
            : isError
            ? 'bg-accent-red/10 text-accent-red border border-accent-red/30'
            : hasActiveProposal
            ? 'bg-accent-yellow/10 text-text-primary border border-accent-yellow/30'
            : 'bg-bg-card text-text-primary border border-border-subtle'
        }`}
      >
        {isError && (
          <div className="flex items-center gap-1.5 text-[11px] text-accent-red mb-1">
            <AlertCircle size={12} /> Coach error
          </div>
        )}
        {isPending && isUser && (
          <div className="flex items-center gap-1.5 text-[11px] text-text-muted mt-1">
            <Loader2 size={12} className="animate-spin" /> Coach is thinking…
          </div>
        )}
        <div className="whitespace-pre-wrap">
          {isError ? turn.error ?? 'Unknown error' : turn.content}
        </div>
        {hasActiveProposal && onConfirm && onReject && (
          <div className="flex gap-2 mt-3 pt-2 border-t border-accent-yellow/20">
            <button
              onClick={onConfirm}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent-green/20 text-accent-green text-[12px] font-semibold hover:bg-accent-green/30 transition-colors min-h-[36px]"
            >
              <Check size={14} /> Apply
            </button>
            <button
              onClick={onReject}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent-red/10 text-accent-red text-[12px] font-semibold hover:bg-accent-red/20 transition-colors min-h-[36px]"
            >
              <X size={14} /> Skip
            </button>
          </div>
        )}
        {proposal && proposalExecuted && (
          <div className="text-[11px] text-accent-green mt-1.5 flex items-center gap-1">
            <Check size={11} /> Applied
          </div>
        )}
        <div className="text-[10px] text-text-dim mt-1">{formatTime(turn.created_at)}</div>
      </div>
    </div>
  )
}

function ConversationList({
  conversations,
  selectedId,
  onSelect,
  onNew,
}: {
  conversations: CoachConversation[]
  selectedId: string | null
  onSelect: (id: string) => void
  onNew: () => void
}) {
  return (
    <div className="bg-bg-card border border-border-subtle rounded-2xl p-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-[11px] uppercase tracking-[0.06em] text-text-muted font-semibold">
          Conversations
        </h3>
        <button
          onClick={onNew}
          className="text-accent-green hover:text-accent-green/80 transition-colors p-1"
          title="New conversation"
        >
          <Plus size={14} />
        </button>
      </div>
      {conversations.length === 0 ? (
        <div className="text-[12px] text-text-muted py-4 text-center">
          No conversations yet. Tap + to start one.
        </div>
      ) : (
        <div className="space-y-1 max-h-32 overflow-y-auto">
          {conversations.map((c) => (
            <button
              key={c.id}
              onClick={() => onSelect(c.id)}
              className={`w-full text-left px-2 py-1.5 rounded-lg text-[12px] transition-colors ${
                selectedId === c.id
                  ? 'bg-accent-green/10 text-text-primary'
                  : 'text-text-muted hover:bg-bg-primary/60 hover:text-text-secondary'
              }`}
            >
              <div className="truncate">{c.title ?? 'Untitled'}</div>
              <div className="text-[10px] text-text-dim">
                {new Date(c.started_at).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                })}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function CoachView() {
  const { data: conversations, loading, error } = useCoachConversations()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  const { data: turns } = useCoachTurns(selectedId)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-select the most recent conversation on first load
  useEffect(() => {
    if (!selectedId && conversations && conversations.length > 0) {
      setSelectedId(conversations[0].id)
    }
  }, [conversations, selectedId])

  // Auto-scroll to bottom on new turns
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [turns])

  const latestTurn = useMemo(() => {
    if (!turns || turns.length === 0) return null
    return turns[turns.length - 1]
  }, [turns])

  const waitingOnCoach =
    latestTurn?.role === 'user' &&
    (latestTurn.status === 'pending' || latestTurn.status === 'in_progress')

  const handleNew = () => {
    // Don't create a DB row eagerly — wait until first message is sent.
    // Clears selection so the next send starts a fresh conversation.
    setSelectedId(null)
    setSendError(null)
    setInput('')
  }

  const handleSend = async () => {
    if (!input.trim() || sending) return
    setSendError(null)
    setSending(true)

    try {
      let convId = selectedId
      if (!convId) {
        const conv = await createCoachConversation(input.slice(0, 60))
        convId = conv.id
        setSelectedId(convId)
      }
      await sendCoachMessage(convId, input.trim())
      setInput('')
    } catch (e) {
      setSendError(e instanceof Error ? e.message : 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

  const handleConfirmProposal = useCallback(async () => {
    if (!selectedId || sending) return
    setSending(true)
    try {
      await sendCoachMessage(selectedId, 'CONFIRM_ACTION')
    } catch (e) {
      setSendError(e instanceof Error ? e.message : 'Failed to confirm')
    } finally {
      setSending(false)
    }
  }, [selectedId, sending])

  const handleRejectProposal = useCallback(async () => {
    if (!selectedId || sending) return
    setSending(true)
    try {
      await sendCoachMessage(selectedId, 'REJECT_ACTION')
    } catch (e) {
      setSendError(e instanceof Error ? e.message : 'Failed to reject')
    } finally {
      setSending(false)
    }
  }, [selectedId, sending])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (loading) return <LoadingState />
  if (error) return <div className="text-accent-red text-sm">{error}</div>

  // Hide conversations that never got a first message — they have no title
  // and no turns. These accumulate if the user tapped + without sending.
  const convs = (conversations ?? []).filter((c) => c.title !== null)

  return (
    <div className="space-y-3">
      <div className="bg-bg-card border border-border-subtle rounded-2xl p-4">
        <div className="flex items-center gap-2 mb-1">
          <MessageCircle size={15} className="text-accent-green" />
          <h2 className="text-[14px] font-semibold text-text-primary">Coach</h2>
        </div>
        <p className="text-[11px] text-text-muted leading-relaxed">
          Ask about today's training, recovery, or why a session was adjusted. Grounded in
          your live data and the knowledge base.
        </p>
      </div>

      <ConversationList
        conversations={convs}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onNew={handleNew}
      />

      <div
        ref={scrollRef}
        className="bg-bg-card border border-border-subtle rounded-2xl p-4 min-h-[280px] max-h-[60vh] overflow-y-auto space-y-2.5"
      >
        {selectedId ? (
          turns && turns.length > 0 ? (
            turns.map((t) => (
              <TurnBubble
                key={t.id}
                turn={t}
                onConfirm={handleConfirmProposal}
                onReject={handleRejectProposal}
              />
            ))
          ) : (
            <div className="text-[12px] text-text-muted py-6 text-center">
              New conversation. Ask the coach anything.
            </div>
          )
        ) : (
          <div className="text-[12px] text-text-muted py-6 text-center">
            Tap the send button or + to start a conversation.
          </div>
        )}
        {waitingOnCoach && (
          <div className="flex items-center gap-2 text-[11px] text-text-muted px-2">
            <Loader2 size={12} className="animate-spin" />
            Coach is thinking…
          </div>
        )}
      </div>

      {sendError && (
        <div className="bg-accent-red/10 text-accent-red text-[12px] px-3 py-2 rounded-xl flex items-center gap-2">
          <AlertCircle size={13} /> {sendError}
        </div>
      )}

      <div className="bg-bg-card border border-border-subtle rounded-2xl p-2 flex items-end gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask the coach…"
          rows={2}
          className="flex-1 bg-transparent text-[13px] text-text-primary placeholder:text-text-dim resize-none focus:outline-none px-2 py-1.5"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || sending}
          className="text-accent-green disabled:text-text-dim transition-colors p-2 min-h-[40px] min-w-[40px] flex items-center justify-center"
          aria-label="Send message"
        >
          {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </div>
    </div>
  )
}
