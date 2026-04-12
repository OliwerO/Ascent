import type { VercelRequest, VercelResponse } from '@vercel/node'

/**
 * POST /api/garmin-push-trigger
 *
 * Writes a workout push request to Supabase coaching_log table.
 * The Mac-side sync watcher picks this up and runs workout_push.py.
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
    const pushDate = targetDate || today
    const twoMinAgo = new Date(Date.now() - 2 * 60 * 1000).toISOString()

    // Rate limit — check for recent unacknowledged push request
    const checkResp = await fetch(
      `${supabaseUrl}/rest/v1/coaching_log?type=eq.workout_push_request&acknowledged=eq.false&created_at=gte.${twoMinAgo}`,
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
          error: 'Push already queued. Please wait a couple of minutes.',
        })
      }
    }

    // Write push request to coaching_log
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
        type: 'workout_push_request',
        channel: 'app',
        message: `Workout push to Garmin requested from app for ${pushDate}`,
        data_context: {
          requested_at: new Date().toISOString(),
          date: pushDate,
        },
        acknowledged: false,
      }),
    })

    if (!insertResp.ok) {
      const err = await insertResp.text()
      return res.status(502).json({ error: 'Failed to create push request', detail: err })
    }

    return res.status(200).json({
      ok: true,
      message: 'Push request queued. Workout should appear on your watch within ~2 minutes.',
    })
  } catch (err) {
    return res.status(500).json({ error: 'Request failed', detail: String(err) })
  }
}
