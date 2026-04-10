import type { VercelRequest, VercelResponse } from '@vercel/node'

/**
 * POST /api/garmin-sync-trigger
 *
 * Writes a sync request to Supabase coaching_log table.
 * The Mac-side sync watcher picks this up and runs garmin_sync.py.
 * This allows triggering a Garmin sync from the mobile app after
 * an activity (e.g., snowboarding) without waiting for the nightly cron.
 */
export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  // Authenticate request — accept either the dedicated sync secret
  // or the Supabase anon key (which the client already has)
  const syncSecret = process.env.SYNC_TRIGGER_SECRET
  const supabaseAnon = process.env.VITE_SUPABASE_KEY
  const authHeader = req.headers['x-ascent-token'] as string | undefined
  const isAuthed = authHeader && (
    (syncSecret && authHeader === syncSecret) ||
    (supabaseAnon && authHeader === supabaseAnon)
  )
  if (!isAuthed) {
    return res.status(401).json({ error: 'Unauthorized' })
  }

  const supabaseUrl = process.env.SUPABASE_URL
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY

  if (!supabaseUrl || !supabaseKey) {
    return res.status(500).json({ error: 'Missing server configuration' })
  }

  try {
    const today = new Date().toISOString().slice(0, 10)
    const twoMinAgo = new Date(Date.now() - 2 * 60 * 1000).toISOString()

    // Check for recent unacknowledged sync request (rate limiting)
    const checkResp = await fetch(
      `${supabaseUrl}/rest/v1/coaching_log?type=eq.sync_request&acknowledged=eq.false&created_at=gte.${twoMinAgo}`,
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
          error: 'Sync already queued. Please wait a couple of minutes.',
        })
      }
    }

    // Write sync request to coaching_log
    const upsertResp = await fetch(`${supabaseUrl}/rest/v1/coaching_log`, {
      method: 'POST',
      headers: {
        apikey: supabaseKey,
        Authorization: `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json',
        Prefer: 'return=representation',
      },
      body: JSON.stringify({
        date: today,
        type: 'sync_request',
        channel: 'app',
        message: 'On-demand Garmin sync requested from Ascent app',
        data_context: { requested_at: new Date().toISOString() },
        acknowledged: false,
      }),
    })

    if (!upsertResp.ok) {
      const err = await upsertResp.text()
      return res.status(502).json({ error: 'Failed to create sync request', detail: err })
    }

    return res.status(200).json({
      ok: true,
      message: 'Sync request queued. Data should arrive within ~1 minute.',
    })
  } catch (err) {
    return res.status(500).json({ error: 'Request failed', detail: String(err) })
  }
}
