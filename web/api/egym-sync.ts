import type { VercelRequest, VercelResponse } from '@vercel/node'

const EGYM_API = 'https://mobile-api.int.api.egym.com'

// Metric type → body_composition column mapping
const METRIC_MAP: Record<string, { col: string; convert: (v: number) => number }> = {
  WEIGHT_KG: { col: 'weight_grams', convert: (v) => Math.round(v * 1000) },
  BMI: { col: 'bmi', convert: (v) => v },
  BODY_FAT_PERCENTS: { col: 'body_fat_pct', convert: (v) => v },
  BODY_WATER_PERCENTS: { col: 'body_water_pct', convert: (v) => v },
  SKELETAL_MUSCLE_MASS_KG: { col: 'muscle_mass_grams', convert: (v) => Math.round(v * 1000) },
  BODY_FAT_MASS_KG: { col: '_fat_mass_kg', convert: (v) => v }, // used for lean mass calc
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const brand = process.env.EGYM_BRAND
  const username = process.env.EGYM_USERNAME
  const password = process.env.EGYM_PASSWORD
  const supabaseUrl = process.env.SUPABASE_URL
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY

  if (!brand || !username || !password || !supabaseUrl || !supabaseKey) {
    return res.status(500).json({ error: 'Missing server configuration' })
  }

  try {
    // 1. Login to eGym via Netpulse
    const loginResp = await fetch(`https://${brand}.netpulse.com/np/exerciser/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'User-Agent': 'NetpulseFitness/3.11 (com.netpulse.netpulsefitness; build:853; iOS 17.2.0) Alamofire/5.4.4',
        'x-np-user-agent': 'clientType=MOBILE_DEVICE; devicePlatform=IOS; deviceUid=0B7F0E30-9598-43EF-8DA6-7018BD289B3C; applicationName=EGYM Fitness; applicationVersion=3.11; applicationVersionCode=853; containerName=NetpulseFitness;',
        'x-np-app-version': '3.11',
      },
      body: new URLSearchParams({ username, password, relogin: 'false' }),
    })

    if (!loginResp.ok) {
      const body = await loginResp.text()
      return res.status(502).json({ error: `eGym login failed (${loginResp.status})`, detail: body })
    }

    const loginData = await loginResp.json()
    const userId = loginData.uuid
    const cookie = loginResp.headers.get('set-cookie') ?? ''

    // 2. Fetch body metrics
    const bodyResp = await fetch(
      `${EGYM_API}/measurements/api/v1.0/exercisers/${userId}/body/latest`,
      { headers: { Accept: 'application/json', Cookie: cookie } }
    )
    const bodyMetrics = bodyResp.ok ? await bodyResp.json() : []

    // 3. Fetch bio age
    const bioResp = await fetch(
      `${EGYM_API}/analysis/api/v1.0/exercisers/${userId}/bioage`,
      { headers: { Accept: 'application/json', Cookie: cookie } }
    )
    const bioAge = bioResp.ok ? await bioResp.json() : null

    // 4. Extract body composition fields
    const row: Record<string, unknown> = {}
    const rawEntries: unknown[] = []
    let fatMassKg: number | null = null

    for (const entry of bodyMetrics) {
      const type = entry.type ?? ''
      const value = entry.value
      if (value == null) continue

      rawEntries.push({
        type,
        value,
        source: entry.source ?? '',
        sourceLabel: entry.sourceLabel ?? '',
        createdAt: entry.createdAt ?? '',
      })

      const mapping = METRIC_MAP[type]
      if (mapping && !mapping.col.startsWith('_')) {
        if (!(mapping.col in row)) {
          row[mapping.col] = mapping.convert(value)
        }
      }
      if (type === 'BODY_FAT_MASS_KG') fatMassKg = value
    }

    // Compute lean body mass
    if (row.weight_grams && fatMassKg != null) {
      row.lean_body_mass_grams = (row.weight_grams as number) - Math.round(fatMassKg * 1000)
    }

    // Flatten bio ages
    const bioSummary: Record<string, number> = {}
    if (bioAge) {
      for (const section of Object.values(bioAge)) {
        if (typeof section !== 'object' || section === null) continue
        for (const [key, val] of Object.entries(section as Record<string, unknown>)) {
          if (typeof val === 'object' && val !== null && 'value' in val) {
            bioSummary[key] = (val as { value: number }).value
          }
        }
      }
    }

    if (Object.keys(row).length === 0) {
      return res.status(200).json({ ok: false, message: 'No body metrics found' })
    }

    const today = new Date().toISOString().slice(0, 10)

    // 5. Upsert to Supabase
    const upsertRow = {
      date: today,
      source: 'egym',
      ...row,
      raw_json: {
        body_metrics: rawEntries,
        bio_age: bioSummary,
        synced_at: new Date().toISOString(),
      },
    }

    const upsertResp = await fetch(`${supabaseUrl}/rest/v1/body_composition?on_conflict=date,source`, {
      method: 'POST',
      headers: {
        apikey: supabaseKey,
        Authorization: `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json',
        Prefer: 'resolution=merge-duplicates',
      },
      body: JSON.stringify(upsertRow),
    })

    if (!upsertResp.ok) {
      const err = await upsertResp.text()
      return res.status(502).json({ error: 'Supabase upsert failed', detail: err })
    }

    return res.status(200).json({
      ok: true,
      date: today,
      weight_kg: row.weight_grams ? (row.weight_grams as number) / 1000 : null,
      body_fat_pct: row.body_fat_pct ?? null,
      muscle_mass_kg: row.muscle_mass_grams ? (row.muscle_mass_grams as number) / 1000 : null,
      lean_mass_kg: row.lean_body_mass_grams ? (row.lean_body_mass_grams as number) / 1000 : null,
      body_water_pct: row.body_water_pct ?? null,
      bmi: row.bmi ?? null,
      bio_age: bioSummary,
    })
  } catch (err) {
    return res.status(500).json({ error: 'Sync failed', detail: String(err) })
  }
}
