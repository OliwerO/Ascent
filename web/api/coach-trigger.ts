import type { VercelRequest, VercelResponse } from '@vercel/node'

/**
 * POST /api/coach-trigger
 *
 * Triggers an on-demand coaching evaluation from the Ascent app.
 * Writes a coach_evaluation_request to coaching_log, which the
 * Mac-side sync_watcher picks up and runs coach_evaluate.py.
 *
 * Body: { date?: string }  — defaults to today
 */
export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const supabaseAnon = process.env.SUPABASE_ANON_KEY
  const authHeader = req.headers['x-ascent-token'] as string | undefined
  if (!authHeader || authHeader !== supabaseAnon) {
    return res.status(401).json({ error: 'Unauthorized' })
  }

  const supabaseUrl = process.env.SUPABASE_URL
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY
  if (!supabaseUrl || !supabaseKey) {
    return res.status(500).json({ error: 'Missing server configuration' })
  }

  try {
    const { date: targetDate } = (req.body || {}) as { date?: string }
    const today = new Date().toISOString().slice(0, 10)
    const evalDate = targetDate || today
    const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()

    // Rate limit — check for recent unacknowledged evaluation request
    const checkResp = await fetch(
      `${supabaseUrl}/rest/v1/coaching_log?type=eq.coach_evaluation_request&acknowledged=eq.false&created_at=gte.${fiveMinAgo}`,
      {
        headers: {
          apikey: supabaseKey,
          Authorization: `Bearer ${supabaseKey}`,
        },
      }
    )
    if (checkResp.ok) {
      const existing = await checkResp.json()
      if (existing.length > 0) {
        return res.status(429).json({
          ok: false,
          error: 'Evaluation already queued. Give it a minute to process.',
        })
      }
    }

    // Write evaluation request to coaching_log
    const insertResp = await fetch(`${supabaseUrl}/rest/v1/coaching_log`, {
      method: 'POST',
      headers: {
        apikey: supabaseKey,
        Authorization: `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json',
        Prefer: 'return=representation',
      },
      body: JSON.stringify({
        date: today,
        type: 'coach_evaluation_request',
        channel: 'app',
        message: `On-demand coaching evaluation requested from app for ${evalDate}`,
        data_context: {
          requested_at: new Date().toISOString(),
          date: evalDate,
        },
        acknowledged: false,
      }),
    })

    if (!insertResp.ok) {
      const err = await insertResp.text()
      return res.status(502).json({ error: 'Failed to create evaluation request', detail: err })
    }

    return res.status(200).json({
      ok: true,
      message: 'Coaching evaluation queued. Decision should appear within ~30 seconds.',
    })
  } catch (err) {
    return res.status(500).json({ error: 'Request failed', detail: String(err) })
  }
}
