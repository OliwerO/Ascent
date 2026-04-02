import type { VercelRequest, VercelResponse } from '@vercel/node'

/**
 * POST /api/egym-sync
 *
 * Writes an eGym sync request to Supabase coaching_log table.
 * The Mac-side sync watcher picks this up and runs egym_sync.py locally.
 * This avoids geo-blocking issues (Netpulse rejects non-EU IPs).
 */
export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const supabaseUrl = process.env.SUPABASE_URL
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY

  if (!supabaseUrl || !supabaseKey) {
    return res.status(500).json({ error: 'Missing server configuration' })
  }

  try {
    const today = new Date().toISOString().slice(0, 10)

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
        type: 'egym_sync_request',
        channel: 'app',
        message: 'On-demand eGym sync requested from Ascent app',
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
      message: 'eGym sync queued. Your Mac will run it within 5 minutes.',
    })
  } catch (err) {
    return res.status(500).json({ error: 'Request failed', detail: String(err) })
  }
}
