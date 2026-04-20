# Garmin Fenix 8 metrics: complete evidence-based knowledge base

The Garmin Fenix 8 captures **over 60 distinct health, fitness, and performance metrics** across its sensor suite, but their scientific validity ranges from gold-standard validated to proprietary black boxes with no independent evidence. Of these metrics, only a handful — **overnight HRV trends, resting heart rate, lactate threshold HR, and GPS/barometric elevation** — deserve primary decision-making weight for a mountain athlete. The majority of Garmin's composite scores (Body Battery, Training Readiness, Training Status) obscure their validated inputs behind proprietary weighting schemes and should be decomposed into their raw components for coaching decisions. This document catalogs every metric with evidence-based validity flags, sensor details, algorithmic foundations, validation studies, practical interpretation, and failure modes relevant to mountain athletics.

The Fenix 8 runs on **Firstbeat Analytics algorithms** (Finnish sports science company acquired by Garmin in 2020) paired with the **Elevate Gen 5 optical sensor** (6 green LEDs, red/IR LEDs, ECG electrodes, thermistor), a Synaptics SYN4778 multi-band GNSS chipset, 3-axis accelerometer, gyroscope, magnetometer, barometric altimeter, and a depth sensor new to this generation. All physiological algorithms are identical to the Forerunner 955/965 and Epix Pro series.

---

## I. CARDIOVASCULAR AND HEART METRICS

### Heart rate (resting, max, zones, real-time)

**⚠️ PARTIALLY VALIDATED** — Strong agreement at steady state (CCC >0.95 moderate intensity); degrades significantly during HIIT, cold, and non-rhythmic activities.

**Sensor and data source.** The Elevate Gen 5 PPG sensor uses **6 green LEDs** (~520–530 nm), 2 red/IR LEDs, and 4 photodiodes to detect blood volume changes at the wrist. Sampling is **1 Hz during activities**, variable-rate during 24/7 monitoring. Resting HR is computed as the average of all readings during detected sleep (minimum 4 hours), excluding movement periods. This yields a value typically **5–10 bpm lower** than traditional clinical seated resting HR. Garmin displays a 7-day rolling average.

**Algorithm.** HR zones support three methods: %Max HR, %HRR (Karvonen), and %LTHR. Default zones use age-predicted max (220 − age) until overridden by user data or auto-detection. The PPG algorithm correlates optical signals with accelerometer data — running cadence correlation filtering makes running HR significantly more accurate than cycling, skiing, or strength training HR. Firstbeat's neural networks incorporate HRV-derived respiration rate for additional signal processing.

**Validation evidence.** Garmin Forerunner 945 vs ECG showed **MAE 1.35–2.25 bpm, MAPE <1.39%** at moderate-to-vigorous intensity with CCC >0.95 (2022 peer-reviewed study). A 10-device climate comparison (2025, JMIR) found no statistically significant temperature effect on accuracy after Bonferroni correction. However, during HIIT with rapid HR transitions, MAPE rose to **10.79%** (2018 study). A systematic review of 29 studies found Garmin accuracy highly model-dependent, with some older models showing MAPE up to 25% during specific exercises. Fenix 8-specific testing (DC Rainmaker, Road Trail Run) shows average correlation of **r = 0.989** over sustained runs, with known 1–3 minute lag at activity start.

**Practical interpretation.** Day-to-day RHR noise floor is **±3–5 bpm**; a sustained shift >5 bpm over multiple days signals illness, overtraining, or adaptation. The 7-day average is the actionable metric — a >3 bpm sustained shift in this average is meaningful. At altitude (>2,500 m), RHR increases **10–20% acutely** due to sympathetic activation, normalizing over 7–14 days of acclimatization. HR zones set via %LTHR are the most sport-science-aligned method.

**Failure modes.** Optical HR lags 1–3 minutes at cold start, producing interpolated rather than "no data" readings — creating false confidence. Cold weather vasoconstriction causes **15–20 bpm errors** for several minutes. Trekking poles, ski poles, and scrambling create non-rhythmic wrist motion that breaks cadence-correlated filtering. Dark skin and tattoos reduce signal-to-noise ratio (partially improved with red/IR LEDs). Heavy pack straps and gloves shift sensor position. **For mountain athletes doing high-intensity ski touring or pole-dependent activities, a chest strap (HRM-Pro Plus or Polar H10) is strongly recommended.**

---

### Heart rate variability (overnight HRV status)

**⚠️ PARTIALLY VALIDATED** — CCC = 0.87 vs ECG reference; adequate for trend monitoring via 7-day rolling average, not for absolute single-night values.

**Sensor and data source.** Same Elevate Gen 5 PPG sensor extracts inter-beat intervals (technically pulse-to-pulse intervals, not true R-R intervals from ECG). Data is collected **during detected sleep only**, segmented into 5-minute windows, and averaged across the sleep period. A dedicated HRV Stress app provides real-time readings but requires an external chest strap for ECG-quality R-R intervals.

**Algorithm.** Garmin reports HRV as **RMSSD** (Root Mean Square of Successive Differences) — the standard time-domain metric most sensitive to parasympathetic activity. Internal processing also uses SDRR. The HRV Status feature requires **~19 nights** to establish a personal baseline, then classifies the 7-day rolling average as Balanced (green), Unbalanced (orange), Low (red), or Poor. Firstbeat's frequency-domain analysis (LF/HF power via short-time Fourier Transform) feeds stress/recovery detection internally but is not user-facing.

**Validation evidence.** Dial et al. (2025, Physiological Reports, n=13, 536 nights) found Garmin Fenix 6 nocturnal HRV showed **CCC = 0.87, MAPE = 10.52%** vs ECG reference — behind Oura Gen 4 (CCC = 0.99) and WHOOP 4.0 (CCC = 0.94), but ahead of Polar Grit X Pro (CCC = 0.82). A clinical ECG comparison (62 participants, 2026) found tolerably accurate readings during lying/seated/sleeping states, but **errors exceeding 100 ms during any movement**, with inconsistent error direction across individuals (no universal correction factor possible). PPG-derived HRV at extreme altitude (4,554–6,800 m, Sensors/MDPI 2022) showed discrepancies in high-frequency spectral components vs ECG, attributed to pulse wave velocity changes at altitude.

**Practical interpretation.** Day-to-day RMSSD variation of **±10–15 ms is normal noise**. The 7-day rolling average is the actionable metric — a sustained decline >1 standard deviation below personal baseline for 3+ days signals fatigue, illness onset, or overreaching. Per Plews, Flatt, and Buchheit, the **coefficient of variation (CV) of RMSSD** over a rolling week may be more sensitive to overtraining than the mean alone. At altitude, HRV typically decreases acutely due to sympathetic activation — establish an altitude-specific baseline over ~2 weeks rather than comparing to sea-level norms. Key confounders: alcohol (variable effect on HRV), late/heavy meals (suppress parasympathetic activity for 3–4 hours), illness (drops HRV 1–3 days before symptoms), travel/jet lag, dehydration.

**Failure modes.** In highly trained endurance athletes with very high vagal tone, overnight HRV may plateau ("parasympathetic saturation"), making it insensitive to further training load changes (Plews et al.). PPG cannot measure HRV during any activity or movement — even minor wrist shifts during sleep corrupt the signal. Absolute RMSSD values cannot be compared across brands (Garmin vs WHOOP vs Oura) due to different measurement windows and algorithms. No real-time exercise HRV from the wrist sensor.

---

### Pulse oximetry (SpO2)

**⚠️ PARTIALLY VALIDATED at sea level / ❌ DISCREDITED above 3,000 m** — Systematically overestimates SpO2 at altitude with >50% error rate above 4,800 m.

**Sensor and data source.** Red and infrared LEDs on the Elevate Gen 5 sensor use reflectance photoplethysmography (R-PPG) to measure the ratio of oxygenated to deoxygenated hemoglobin. This differs fundamentally from transmission-mode medical fingertip oximeters. Available as on-demand spot check (~30 seconds stillness), continuous all-day monitoring, or sleep-only monitoring. Garmin explicitly states: **"Not a medical device."**

**Algorithm.** Proprietary motion artifact rejection and ambient light compensation. Exact algorithm undisclosed.

**Validation evidence.** Hermand et al. (2021, Int J Sports Med) found acceptable bias (0.7–0.8%) at sea level to 3,000 m, but **3.3% bias at 3,658 m** and **>80% error rate above 4,800 m**. The device systematically overestimates SpO2 at altitude — dangerously providing false reassurance to hypoxemic climbers. Schiefer et al. (2021, Sensors) found **7% mean difference** vs arterial blood gas at 4,559 m. Weinrauch (2023, JHTAM) documented a **53% measurement failure rate** at sea level (53/100 attempts failed). Multiple studies confirm skin-tone-dependent accuracy bias — incidence of undetected hypoxemia is **3× higher in Black patients**.

**Practical interpretation.** Normal at sea level: 95–100%. At 2,000–3,000 m: 90–95% typical during acclimatization. Use for **trend observation only**, not absolute values. A medical fingertip pulse oximeter weighs <30 g and costs <$25 — carry one for any altitude where SpO2 monitoring matters. Overnight SpO2 dips during sleep at altitude may indicate periodic breathing (Cheyne-Stokes), common above 2,500 m.

**Failure modes.** High failure rate even at sea level. Accuracy catastrophe above 3,000 m. Requires complete stillness. Cold/vasoconstriction degrades signal. Dark skin tones increase both failure rate and overestimation bias. **For mountain athletes, wrist SpO2 is essentially useless for altitude safety decisions — always carry a fingertip oximeter.**

---

### ECG (electrocardiogram)

**⚠️ PARTIALLY VALIDATED** — FDA-cleared for AFib detection only; no independent peer-reviewed validation studies published.

**Sensor and data source.** Four silver electrodes on the caseback (skin contact) paired with the metal bezel (finger contact) create a single-lead ECG circuit during a manually initiated 30-second recording. Not continuous or passive.

**Algorithm.** Classifies waveform as Normal Sinus Rhythm, Atrial Fibrillation, or Inconclusive. FDA 510(k) cleared (January 2023), expanded to Fenix 8 (August 2024). Not designed to detect heart attacks, blood clots, or stroke. Age restriction: not intended for users under 22. Region-restricted (primarily US, EU, Australia).

**Failure modes.** Manual-only (no passive rhythm monitoring like Apple Watch). Single lead cannot detect many cardiac conditions. Requires stillness for 30 seconds. Cold/wet/gloved hands impair electrode contact — significant limitation for mountain athletes. Geographic availability restrictions.

---

### Abnormal heart rate alerts

**❓ PROPRIETARY/UNVALIDATED** — Simple threshold alarm with no independent accuracy assessment.

Alerts when HR exceeds or drops below user-set thresholds after **10 minutes of inactivity**. Does not alert during exercise or configured sleep windows. Cannot detect AFib, arrhythmias, or cardiac events. All optical HR failure modes apply. Known bug: HR broadcasting from the control center can trigger false alerts during exercise.

---

## II. TRAINING LOAD AND PERFORMANCE METRICS

### VO2 max (running and cycling)

**⚠️ PARTIALLY VALIDATED** — Firstbeat reports MAPE ~5% under ideal conditions; independent studies show systematic underestimation of 4–5 ml/kg/min, with poor accuracy (ICC 0.34–0.41) at elite fitness levels (>60 ml/kg/min).

**Sensor and data source.** Running: HR + GPS pace during segments where HR >70% HRmax during steady-state running (≥10 min outdoors). Cycling: HR + power meter data (power meter mandatory, ≥20 min steady effort). User profile data (age, sex, weight, estimated HRmax) feeds the model.

**Algorithm.** Firstbeat compares internal workload (%HRmax → estimated %VO2max) against external workload (running speed or cycling power). Neural networks incorporate HRV-derived respiration rate and on/off-kinetics. Only "credible segments" with stable HR-to-speed/power ratios are used. This is submaximal, field-based, and requires no maximal effort — a key advantage over Cooper or ACSM formulas. Running and cycling VO2max are tracked separately (cycling typically reads **5–10% lower** due to smaller active muscle mass).

**Validation evidence.** Firstbeat internal validation (2017 white paper, n=2,690 runs from 79 runners): error <3.5 ml/kg/min in most cases, **MAPE ~5%**. Southern Illinois University study: bias of −0.3 to −3.2 ml/kg/min. Springer/EJAP 2025 (n=35 Tier 2–3 athletes): mean underestimation of **−4.73 ml/kg/min**, with ICC only **0.34–0.41 and ~10% MAPE** for highly trained athletes (VO2max >59.8). Accuracy degrades significantly if HRmax is incorrectly estimated (±15 bpm error → **7–9% VO2max error**). Consensus: **trend reliability far exceeds absolute accuracy**.

**Practical interpretation.** Meaningful change: ~1 ml/kg/min per month during structured training is typical. Accuracy range: ±3.5 ml/kg/min with correct HRmax and chest strap; ±5–6 ml/kg/min with wrist HR; wider at elite levels. Focus on multi-week trends, not single readings.

**Failure modes — critical for mountain athletes.** Trail running with elevation gain, pack weight, and technical terrain routinely causes 3–5 point underestimates. **VO2max does NOT calculate during ski touring activities.** Altitude reduces SpO2 and elevates HR, causing the algorithm to read artificially lower fitness. Heat/dehydration similarly inflate HR, depressing estimates. Non-steady-state efforts (intervals, fartleks) produce fewer valid segments and may not update. For mountain athletes who primarily ski tour, VO2max will stagnate and Training Status will report misleading "Detraining."

---

### EPOC (excess post-exercise oxygen consumption)

**⚠️ PARTIALLY VALIDATED** — Firstbeat's predictive model validated against laboratory gas exchange; physiological concept well-established but HR-based estimation cannot capture muscular/orthopedic stress.

EPOC is the **base unit** underlying Training Load, Training Effect, and Recovery Time. Firstbeat's patented model (US Patent 7,192,401) estimates EPOC in real-time from HR dynamics: EPOC(t) = f(EPOC(t−1), exercise_intensity(t), Δt). At low intensity (<30–40% VO2max), EPOC does not accumulate significantly. Above ~50% VO2max, accumulation is continuous and steep. Critically, **EPOC decreases during recovery periods** within a session (unlike TRIMP, which always accumulates if HR is above rest). This makes EPOC more sensitive to genuine physiological stress than TRIMP but means it cannot capture muscular load from resistance training, eccentric damage, or load carriage stress that doesn't significantly elevate HR. Cardiac drift from heat/dehydration artificially inflates EPOC.

---

### Training load (acute, chronic, load ratio)

**⚠️ PARTIALLY VALIDATED** (EPOC-based load) / **❌ DISCREDITED** (ACWR as injury predictor)

**Algorithm.** Acute Load uses an exponentially weighted moving average (EWMA) of EPOC-based session loads over ~7–10 days (not a simple rolling sum). Chronic Load is a 28-day rolling average. Load Ratio = Acute ÷ Chronic — Garmin's implementation of ACWR.

**ACWR critique.** Impellizzeri et al. (2020, IJSPP; 2021, Sports Medicine) demonstrated that dividing acute load by **randomly generated** chronic loads produces equivalent odds ratios (OR 1.53 mean) to real ACWR data (OR 2.45). The C-statistic was **0.574 vs 0.5 intercept-only** — negligible predictive value. Lolli et al. (2019) showed mathematical coupling in coupled ACWR (numerator included in denominator). Wang et al. (2020) found the ACWR-injury relationship disappeared when data was analyzed as continuous rather than arbitrarily bucketed. **The existing KB's demotion of ACWR is fully supported by this literature.** Garmin's load ratio is better understood as a periodization awareness tool (am I training more or less than my recent baseline?) rather than an injury predictor.

**Failure modes.** Activities without HR data contribute zero load. Strength training EPOC is often underestimated. Swimming load poorly captured (unreliable wrist HR in water). Load ratio appears alarming when returning from rest (low chronic denominator).

---

### Training status

**❓ PROPRIETARY/UNVALIDATED** — Conceptually sound inputs but proprietary decision logic with no independent validation.

Combines VO2max trend, acute training load, and HRV Status into categorical labels: Productive, Maintaining, Peaking, Recovery, Unproductive, Overreaching, Strained, Detraining. The most useful signals are **Peaking** (confirms taper working) and persistent **Unproductive** (signals recovery deficit). Most misleading: Unproductive during heat acclimatization (VO2max drops from heat, not poor training) and Detraining during planned recovery weeks. **For mountain athletes, ski touring generates load but no VO2max updates, causing Training Status to stall or show false Detraining.**

---

### Training readiness

**❓ PROPRIETARY/UNVALIDATED** — Black box composite of six inputs with proprietary weighting. The existing KB's demotion is fully supported.

Inputs: last night's sleep score, recovery time remaining, HRV status, acute load, 3-night sleep history, 3-day stress history. Score 0–100. The weighting scheme is proprietary and has been revised between device generations without backporting. Individual components (HRV, sleep) have varying degrees of validation, but the composite itself has zero published validation. **Better to examine raw HRV status, sleep data, and stress data separately than to rely on this abstracted number.**

---

### Training effect (aerobic and anaerobic)

**⚠️ PARTIALLY VALIDATED** — Based on EPOC (validated); 0–5 scale mapping is proprietary but physiologically grounded.

Aerobic TE is based on **peak EPOC** (not cumulative), scaled by individual fitness level. This means a long slow run may show low Aerobic TE (1.5) despite producing high fatigue — by design, TE measures VO2max impact, not endurance base building. Anaerobic TE uses heartbeat dynamics to detect high-intensity bursts (10–120 seconds) even when HR hasn't peaked. The 0–5 scale: 0–0.9 = No Effect, 1.0–1.9 = Minor, 2.0–2.9 = Maintaining, 3.0–3.9 = Improving, 4.0–4.9 = Highly Improving, 5.0 = Overloading.

---

### Load focus (low aerobic, high aerobic, anaerobic)

**⚠️ PARTIALLY VALIDATED** — The concept of monitoring intensity distribution is well-supported (Seiler, 2010; Stöggl & Sperlich, 2014); Garmin's specific bucketing thresholds are proprietary.

Each activity's EPOC load is classified into three buckets relative to individual thresholds: Low Aerobic (<VT1), High Aerobic (VT1–VT2), Anaerobic (>VT2). Displayed as color-coded bars over 4 weeks. Most recreational athletes under-train in low aerobic and over-train in high aerobic ("zone 3 trap"). Elite polarized model: ~80% low, ~5% high, ~15% anaerobic. **Incorrect threshold settings cascade into wrong bucket assignments — ensure LTHR is accurate.**

---

### Race predictor

**⚠️ PARTIALLY VALIDATED** (via VO2max validation) — Community consensus: 5K/10K reasonably accurate; marathon predictions **consistently overoptimistic** by 10–20+ minutes for recreational athletes.

Based on VO2max estimate mapped to race times via lookup tables (similar to Jack Daniels' VDOT concept, enhanced with training history since 2022–2024 updates). Assumes flat road running. **Minimally useful for mountain athletes** — predictions don't account for vertical gain, terrain, altitude, or technical difficulty. Best used as a fitness trend tracker, not a pacing target.

---

### Lactate threshold (HR and pace)

**⚠️ PARTIALLY VALIDATED** — Peer-reviewed studies show LTHR within ~5–7% MAPE, but LT pace systematically underestimated by ~12% and 48% data loss rate.

**Algorithm.** Firstbeat analyzes respiratory rate derived from HRV beat-to-beat patterns, combined with HR-pace data, to detect the ventilatory threshold (VT2), assumed to correspond to LT2 (~4 mmol/L). Guided test available; auto-detect during high-intensity runs with chest strap also possible.

**Validation evidence.** Heiber et al. (2024, Open Access J Sports Med, n=26): Pace at LT was **11.96% lower** than field test (p<0.001, d=−1.19). HR at LT was 1.71% lower (not significant). **48% data loss** — many participants failed to produce a valid estimate. Frontiers in Physiology (2025, n=100 total): MAPE for LT HR: **5.95–7.15%**, MAE 8.93–11.44 bpm. Carrier et al. (2021): 6.20% MAPE.

**Practical interpretation.** LTHR is **highly relevant for mountain athletes** — directly applicable for pacing sustained climbs across all modalities (running, ski touring, cycling). LT pace is less useful on trails. Meaningful change: ≥3–5 bpm in LTHR or ≥5–10 sec/km in LT pace after 4–6 weeks signals genuine adaptation. Always distinguishes LT2, not LT1 (aerobic threshold).

**Failure modes.** Requires chest strap for HRV-based detection. High failure rate. Auto-detect less accurate than guided test. Systematically conservative for fit athletes. Cycling LTHR has been documented as drastically wrong in some cases.

---

### Performance condition

**❓ PROPRIETARY/UNVALIDATED** — No peer-reviewed validation as a standalone metric.

Compares real-time HR-pace/power relationship against established VO2max baseline. Each point on the ±20 scale ≈ 1% deviation from baseline. Appears after 6–20 minutes. Useful as a **quick readiness signal** in the first 10 minutes — if PC is −5 to −10, consider reducing workout intensity. **Hills, trail running, heat, and altitude all confound readings** by altering the pace-HR relationship independently of fitness/fatigue.

---

### Real-time stamina

**❓ PROPRIETARY/UNVALIDATED** — No peer-reviewed evaluation; extensive positive anecdotal evidence for events >60 minutes.

**Algorithm.** Two parallel models: **Current Stamina** (0–100%) considers general fatigue, glycogen depletion, and anaerobic capacity — drops sharply above LT, partially recovers below it. **Potential Stamina** (0–100%) focuses on irreversible session fatigue (muscle damage, CNS fatigue, glycogen) — falls progressively and does not recover within a session. Uses EPOC accumulation rate as metabolic stress proxy combined with personalized fatigue resistance curves from training history. Nutrition is NOT a direct input.

**Mountain athlete relevance: HIGH.** Excellent pacing tool for long mountain days (>2 hours). Trail running produces more volatile readings due to gradient changes. Most reliable from half-marathon distance upward. **Key failure: incorrect HRmax is the #1 cause of unreliable readings** (moderate efforts register as near-maximal if HRmax is set too low).

---

### Endurance score

**❓ PROPRIETARY/UNVALIDATED** — No peer-reviewed validation. Known bugs (1,000-point jumps from incorrect FTP).

Scale 1–11,000+. Uses VO2max as foundation, layers training history (duration, intensity, speed, power across all HR-tracked activities). Longest recorded activities carry significant weight. Cross-activity: every HR-tracked activity contributes. Useful as a long-term endurance base barometer. Shifts of **100+ points sustained over a week** reflect genuine training adaptation.

---

### Hill score

**❓ PROPRIETARY/UNVALIDATED** — No published correlation with mountain race performance despite being the most mountain-relevant metric in the suite.

Scale 1–100 with age/gender categories. Three components: **Hill Strength** (steep, short climbs), **Hill Endurance** (sustained moderate climbs), and VO2max. Requires outdoor running/walking/hiking on ≥2% grade — **treadmill incline and cycling uphill do not contribute**. Ski touring/splitboarding may not trigger hill detection depending on activity classification. The 2% minimum grade is low for mountain athletes (meaningful segments are typically 6–15%+). **Treat as a directional indicator, not a performance benchmark.**

---

### Recovery time

**⚠️ PARTIALLY VALIDATED** — EPOC model validated; specific implementation lacks direct validation against measured recovery markers.

Core: Firstbeat's EPOC model estimates metabolic disturbance, scaled by individual fitness (Activity Class). Updated to incorporate sleep, HRV, and stress data (~2020). Typical ranges: 0–6 h (easy), 6–24 h (moderate), 24–48 h (hard), 48–72 h (very hard), 72–96 h+ (race/extreme). Estimates readiness for next **hard** effort, not for any activity.

**Critical mountain athlete limitation:** Recovery Time captures cardiovascular recovery well but **underestimates neuromuscular recovery after eccentric-dominant exercise** (long mountain descents, heavy pack days). Conversely, it **overestimates** after sessions with heat- or dehydration-elevated HR. Strength training produces unrealistically short estimates (low EPOC, high muscular damage).

---

### FTP (functional threshold power, cycling)

**⚠️ PARTIALLY VALIDATED** — FTP concept well-validated in cycling science; Garmin's auto-detect implementation is proprietary with limited independent assessment.

Requires external power meter. Auto-detect during sustained high-intensity rides (≥20 min). Guided test available. Initial estimate from user profile + VO2max is very rough. **Incorrect FTP cascades errors throughout Training Effect, Training Load, Stamina, and Endurance Score** — use a guided test or manual entry from a proper 20-minute test. The5krunner documented Garmin FTP estimates ~8% below actual with drastically wrong cycling LTHR values.

---

## III. RUNNING DYNAMICS

### Cadence

**✅ VALIDATED** — ICC = 0.931 vs motion capture (Adams et al., 2016). Most reliable wrist-derived running metric.

Measured from wrist accelerometer (arm-swing cycle detection) or preferentially from HRM-Pro Plus chest accelerometer. Minimal detectable change: **2.53 spm**. Optimal ranges: elite 170–190 spm, recreational 155–175 spm. Cadence retraining (increasing by 5–10%) has been shown to reduce tibial stress fracture risk. **Failure mode: trekking poles dramatically reduce cadence accuracy** — a WKU study found pole use cut detected steps by ~50% on the pole-hand wrist.

### Stride length

**⚠️ PARTIALLY VALIDATED** — GPS-derived (distance ÷ step count); accuracy tracks GPS quality.

From wrist: entirely dependent on GPS accuracy. With HRM-Pro Plus: torso accelerometer provides biomechanical estimate independent of GPS (enables indoor pace). In open sky: ±2–3%. Under tree cover/switchbacks: degrades significantly.

### Vertical oscillation

**⚠️ PARTIALLY VALIDATED** — Chest-based: ICC = 0.963 (Adams et al., 2016). Wrist-based: noisier, less validated.

Derived from double integration of vertical acceleration. Evidence that vertical oscillation correlates with running economy is **equivocal** — one study found greater VO associated with *improved* RE in national-level runners, opposite of popular coaching advice. Monitor trends within an individual; an increase during long runs may indicate fatigue.

### Vertical ratio

**⚠️ PARTIALLY VALIDATED** — Biomechanically sound concept; direct evidence linking it to outcomes is weak.

Calculated as Vertical Oscillation (cm) ÷ Stride Length (m) × 100. Optimal: <6% excellent; 6–8% good; >10% poor. Inherits accuracy limitations of both VO and stride length.

### Ground contact time (GCT)

**⚠️ PARTIALLY VALIDATED** — ICC = 0.749 (Adams et al., 2016); moderate agreement. GCT's relationship to performance/economy is inconsistent as an absolute metric.

Minimal detectable change: **10 ms**. Ranges: elite 160–210 ms, recreational 250–300+ ms. Varies dramatically with speed. **Not available while walking** — disappears on steep uphills where mountain athletes power-hike.

### GCT balance (L/R)

**⚠️ PARTIALLY VALIDATED** — **Requires chest strap** (only running dynamic that cannot be measured from wrist alone).

This is arguably the **most clinically actionable running dynamic**. GCT imbalance shows the strongest correlation with running economy of any running dynamic metric: **R = 0.808, p < 0.005** — each 1% imbalance → ~3.7% increase in metabolic cost (PMC study on NCAA runners). Optimal: 50/50 ± 1%. Imbalances >2% warrant investigation (leg length discrepancy, injury, muscle weakness).

### Running power (wrist-based)

**❓ PROPRIETARY/UNVALIDATED** — No independent peer-reviewed validation for Garmin's wrist power. Stryd foot pod is partially validated (R² = 0.84 vs VO2).

**Algorithm.** Garmin uses a GOVSS-based model combining GPS speed, barometric altimeter (elevation changes), accelerometer/gyroscope, user mass, and weather-derived wind data. Values are typically **50–140 W higher** than Stryd at equivalent paces due to fundamentally different models. Do NOT compare across platforms. **Mountain athlete use case: power's strongest application is trail/mountain running pacing** — it captures gradient, wind, and terrain effects that pace cannot. Running power on steep terrain is potentially useful but barometric weather changes can introduce error, and the walking-running transition may be poorly handled. **Trekking poles severely compromise all wrist-based measurements.**

**Key finding for the KB:** Neal et al. (2024) found that in a prospective study using wristwatch IMU data, **no individual biomechanical running dynamic variable predicted subsequent injury**. Training load variables (acute load by calculated effort) DID predict injury. Running dynamics are best used for individual trend monitoring and asymmetry detection, not as absolute injury predictors.

---

## IV. SLEEP AND RECOVERY

### Sleep stages

**⚠️ PARTIALLY VALIDATED** — Moderate agreement with PSG (κ = 0.54, 69.7% overall accuracy); consistently poor at detecting wake periods.

**Algorithm.** Firstbeat Advanced Sleep Monitoring combines HRV analysis + accelerometer actigraphy to classify Wake, Light (N1+N2), Deep (N3), REM. A neural network trained via k-fold cross-validation on PSG-scored data performs 30-second epoch classification. On-device preprocessing computes 60+ features; cloud-based neural network performs final classification.

**Validation evidence.** Garmin's own study (2019, n=55): **69.7% accuracy, κ = 0.54** (moderate agreement). Sleep detection sensitivity: 95.8%; wake specificity: only 73.4%. Most common errors: true deep → classified light (29.1%); true REM → classified light (26.4%). Kuula & Pesonen (2021, JMIR, n=20, Firstbeat Bodyguard 2): underestimated REM by 18 min, overestimated wake by 14 min. Schyvens et al. (2025, SLEEP Advances, n=62): Garmin had **29–52% wake specificity** — among the lowest tested devices. The5krunner/Quantified Scientist independent testing (2025): **40–50% stage agreement**, toward the lower end vs Oura, Apple Watch, and WHOOP. Inter-scorer PSG agreement between trained humans is ~83% with κ ≈ 0.78 — a ceiling no consumer wearable reaches.

**Practical interpretation.** Adults typically: ~50% light, 15–25% deep, 20–25% REM. Garmin reference: 17–35% deep sleep for restoration. **At altitude**, sleep is physiologically disrupted (periodic breathing, more arousals, reduced deep sleep, lower SpO2) — the watch will reflect this with more wake/light classifications, though staging accuracy is further compromised by hypoxia-induced autonomic changes.

**Failure modes.** Light sleep ↔ wake confusion is the most common error. REM frequently misclassified as light. Reading/watching in bed can trigger false sleep onset. Sleep disorders dramatically degrade accuracy (worst performer in Garmin's study: 49.9% accuracy, κ = 0.18). Cold extremities degrade PPG quality. Unusual sleeping positions (alpine huts, bivouacs, sitting in harness) may not be properly detected.

---

### Sleep score

**❓ PROPRIETARY/UNVALIDATED** — Composite of partially validated inputs with proprietary weighting.

Three components: Sleep Duration (vs AASM age-adjusted recommendation), Sleep Quality (stage balance, restlessness, continuity), Sleep Restoration (HRV-derived overnight recovery). Scale 0–100. Global Garmin average (2024): **72** (Fair). Only 5% of users average 90–100 (Excellent). **Best used as a weekly trend indicator, not a precise daily measure.** The most common cause of a low score is the HRV recovery component — alcohol, late exercise, illness, and elevated ambient temperature all suppress overnight parasympathetic activity.

---

### Sleep coach and sleep needs

**❓ PROPRIETARY/UNVALIDATED** — Based on sound principles (AASM guidelines + training load awareness) but specific algorithms unvalidated.

Calculates personalized sleep need from recent sleep history, training load, HRV trends, and nap data. Recommends bedtime/wake windows. **Largely irrelevant for mountain athletes during alpine starts (1–3 AM) or bivouac schedules.** May provide useful data post-expedition for re-establishing normal sleep patterns.

---

### Nap detection

**❓ PROPRIETARY/UNVALIDATED** — No peer-reviewed studies. Inconsistent auto-detection in testing.

Any sleep period <3 hours outside usual sleep hours is classified as a nap. Auto-detection uses same movement + HR criteria as nighttime sleep. For mountain athletes, **manual sleep mode activation is recommended** over auto-detection, which is unreliable in unusual positions (sitting against a rock, bivouac harness). Nap data adjusts Body Battery and sleep coach recommendations.

---

### Body Battery

**❓ PROPRIETARY/UNVALIDATED** — The existing KB's demotion is fully supported. Masks underlying inputs behind a proprietary composite.

**Algorithm.** Energy-in: HRV-derived recovery during rest/sleep. Energy-out: stress (HRV-based) + activity (EPOC-based). Scale 5–100. Higher fitness → slower drain, faster recovery. The composite score itself has **zero independent peer-reviewed validation**. The underlying Firstbeat stress/recovery method has some validation, but the weighting scheme combining components is proprietary.

**Why to decompose, not use.** A low Body Battery could mean poor sleep, high psychological stress, heavy training, altitude exposure, or alcohol — impossible to distinguish from the single number. **Better to examine raw HRV status, sleep score, and stress data separately.** An active training day will show greater depletion than a sedentary day, even when the training was beneficial. At altitude, Body Battery will show suppressed overnight charging (real physiology but unhelpful abstraction).

---

### Stress score (all-day, 0–100)

**⚠️ PARTIALLY VALIDATED** — Correlates with physiological arousal (HR: r = 0.74–0.85, RMSSD: r = −0.41 to −0.63); weakly associated with subjective psychological stress (β = −0.023, p = 0.053, not significant).

**Algorithm.** Based on Firstbeat's 24-hour HRV analysis. Measures HRV **during inactivity only** — during exercise, the widget shows "too active to measure" (gray bars). Classifies each moment as Stress (sympathetic dominant), Recovery (parasympathetic dominant), Physical Activity, or Unrecognized. Scale: 0–25 resting, 26–50 low, 51–75 medium, 76–100 high.

**Critical interpretation.** The stress score measures **autonomic arousal**, not perceived psychological stress. Post-exercise sympathetic activation elevates the score for 1–3 hours (normal physiology). Altitude and cold chronically elevate scores via sympathetic activation — real physiology but reduces discriminatory power. Caffeine, alcohol, and dehydration all elevate scores. **A sedentary day may paradoxically show lower "stress" than an active training day.**

---

## V. BODY AND WELLNESS

### Wrist skin temperature

**⚠️ PARTIALLY VALIDATED** — Useful for multi-night trends; heavily confounded by ambient conditions.

Thermistor in the Elevate Gen 5 sensor measures wrist skin temperature **overnight during sleep only**. Reports **deviation from a 20-day rolling baseline** (±°C), not absolute temperature. Requires 3 consecutive nights before any readings appear. Meaningful change: sustained deviation >0.3°C over multiple nights. Single-night spikes are noise. **Mountain athlete critical limitation: cold-weather camping, variable sleeping bags, and bivouacking create ambient artifacts that easily exceed physiological signals, making this metric unreliable in alpine settings.**

### Respiration rate

**⚠️ PARTIALLY VALIDATED** — Excellent at rest/sleep (r > 0.92 vs PSG); degrades significantly during high-intensity exercise (≥4 brpm divergence above LT).

Derived from respiratory sinus arrhythmia (RSA) analysis of PPG-derived HRV signal. Healthy adult at rest: 12–20 brpm. A sustained increase of **2+ brpm over several nights** signals incomplete recovery, fatigue, or early illness. **At altitude, respiration rate naturally elevates 2–4 brpm** due to hypoxic ventilatory response — a true physiological signal, not measurement error.

### Hydration tracking

**N/A** — Purely manual logging feature, no sensor involvement. Simple fluid intake tracking against customizable daily goal. Useful as a behavioral nudge only.

### Body composition (Garmin Index S2 scale)

**⚠️ PARTIALLY VALIDATED** (for trends) — BIA body fat shows **3–5% absolute error vs DEXA**; within-device precision much better than accuracy.

Foot-to-foot bioelectrical impedance analysis. Weight is highly accurate (±0.1 kg). Body fat %, muscle mass, and body water are noisy day-to-day (1–3% fluctuation from hydration, meals, exercise). **Use 4-week+ trends measured under identical conditions** (morning, fasted, barefoot). Individual readings are estimates only.

### Intensity minutes

**⚠️ PARTIALLY VALIDATED** — HR-zone approach aligned with WHO/ACSM guidelines; accuracy dependent on HR measurement quality.

Moderate: ~64–76% max HR; Vigorous: ~77–93% max HR. Vigorous counts double (1 min = 2 intensity minutes). Minimum 10 consecutive minutes required. Weekly target: 150+ (per WHO). Strength training often inflates vigorous minutes (muscle tension elevates wrist HR).

### Steps

**⚠️ PARTIALLY VALIDATED** — ±1–5% at normal walking speed; degrades at slow speeds and during non-walking activities.

3-axis accelerometer with 10-step minimum filter. Generally accurate for brisk walking. Systematically undercounts slow walking (<3 km/h), treadmill with handrails, pushing carts. **Mountain athlete: scrambling, via ferrata, ski touring with fixed arms, and pole-dependent hiking will all significantly undercount.** Lawn mowing and road vibration cause overcounting.

### Floors climbed

**⚠️ PARTIALLY VALIDATED** — 1 floor = ~3 m elevation gain. Requires both barometric pressure change AND walking motion.

Weather fronts can cause **50–100 m+ altitude drift** — the walking-motion requirement filters most phantom floors but doesn't eliminate them entirely. Riding elevators/driving uphill doesn't count (no walking motion). Technical scrambling with minimal arm swing may undercount.

### Calories (active, resting, total)

**⚠️ PARTIALLY VALIDATED** — MAPE 15–32% for steady cardio; up to 40–50% underestimation for strength training.

Firstbeat's energy expenditure model estimates VO2 from HR dynamics, incorporating HRV, user anthropometrics, and VO2max estimate. This is more sophisticated than simple MET-based approaches but still shows significant error. Garmin Fenix 6 vs indirect calorimetry: **MAPE 32.0%** during walking. Strength training: **40–50% underestimation**. **Mountain athlete: load carriage (pack weight) and altitude metabolic cost increases (10–20% above 3,000 m) are NOT modeled.** Treat calorie figures as directional estimates with ±30% uncertainty.

### Move IQ

**❓ PROPRIETARY/UNVALIDATED** — Pattern recognition on accelerometer data classifying sustained movement (>10 min) into activity types. No peer-reviewed validation. Useful as a safety net for forgotten activity starts but does not generate detailed metrics.

### Fitness age

**⚠️ PARTIALLY VALIDATED** — Based on the NTNU/HUNT Study concept (well-validated in population studies); Garmin's specific implementation is proprietary.

Multi-factor model: VO2max, RHR, BMI/body fat%, vigorous activity. Related to the validated HUNT Fitness Calculator. Trend more reliable than absolute number. **High BMI from muscle mass artificially inflates Fitness Age** — body fat % from Index S2 partially corrects this. Maximum discount: ~9–11 years below chronological age.

---

## VI. ACTIVITY-SPECIFIC METRICS

### GPS accuracy and multi-band GNSS

**⚠️ PARTIALLY VALIDATED** — Extensive empirical testing shows excellent performance; no peer-reviewed mountain terrain studies for this specific chipset.

**Hardware.** Synaptics SYN4778 multi-band GNSS chipset (7 nm process, upgraded from Airoha in Fenix 7). Dual-frequency L1 + L5 across GPS, GLONASS, Galileo, BeiDou, QZSS. All Fenix 8 models include multi-band (previously Sapphire-only).

**SatIQ algorithm.** Dynamically toggles between multi-band and single-band based on signal confidence assessment — analyzes discrepancy between L1 and L5 distance readings. When bands agree, drops to single-band to save battery. Post-activity GPS correction introduced: cloud-based track reprocessing using internal sensor data (accelerometer, compass, gyroscope) for pedestrian activities and open-water swimming.

DC Rainmaker describes Fenix 8 GPS as **"industry-leading accuracy across every sport tested"** including dense urban environments and mountainous terrain. OutdoorGearLab: 2.74 miles on a 2.80-mile reference course (2.1% error).

**Mountain athlete recommendations.** Use **All Systems + Multi-Band** for critical navigation in steep valleys and heavy tree cover. **SatIQ** for most long days (good battery-accuracy trade-off). Deep valleys, cliff-face reflections, and narrow V-shaped valleys remain challenging even with dual-frequency.

### Barometric altimeter

**⚠️ PARTIALLY VALIDATED** — Well-understood physics; proprietary filtering algorithms vary between firmware versions.

MEMS barometric pressure sensor with new physical sensor guard protecting the port from sweat, ice, and debris (Fenix 8 improvement). ±3–5 m accuracy when pressure is stable. **Primary elevation source during activities** (GPS altitude error is ±15–30 m). Auto-calibrates via GPS or at known points.

**Critical mountain failure mode: weather-induced drift.** A 1 hPa pressure change ≈ 8.4 m altitude error. Mountain weather can shift 5–10 hPa over hours, causing **50–100 m+ of cumulative altitude error** on long activities. This is the single largest error source for mountain athletes. **Mitigation: manually calibrate at known elevation points throughout the day.** Use Altimeter Only mode during mountain activities. Enable Auto Cal for GPS-based periodic recalibration.

### 3D speed and 3D distance

**⚠️ PARTIALLY VALIDATED** — Correct in principle; dependent on barometer accuracy.

Combines barometric altitude change with horizontal GPS displacement: 3D_distance = √(horizontal² + vertical²). Essential for steep terrain where true travel distance far exceeds map distance. **Enable for all ski touring, splitboarding, and steep mountain activities.** If barometric sensor is drifting (weather change), 3D calculations will incorporate erroneous vertical component.

### ClimbPro

**⚠️ PARTIALLY VALIDATED** — Accuracy depends on course elevation data quality.

When navigating a pre-loaded course: uses DEM elevation data to identify and segment climbs (minimum 500 m length, minimum 3% average gradient). Shows remaining distance, remaining ascent, gradient, and position on elevation profile. "Always" mode (no course) uses real-time barometric + GPS but can only show current climb data. **Extremely useful for ski touring and hike-and-fly** — pre-load touring routes for remaining ascent to col/summit. Pair with Auto Climb for automatic screen switching.

### PacePro

**❓ PROPRIETARY/UNVALIDATED** — No published validation. Grade-adjustment model is proprietary.

Creates grade-adjusted pace bands from pre-loaded course elevation profiles. Requires pre-loaded course (routes created on-watch don't work). **Best for trail running/hike-and-fly approaches with target times.** Less useful for ski touring with variable conditions.

### Ski and snowboard metrics

**⚠️ PARTIALLY VALIDATED** (resort downhill) / **🐛 KNOWN BUGGY** (backcountry auto-detection)

**Resort downhill:** Auto-run detection using accelerometer + barometer works well with clear chairlift + run patterns. Metrics: run count, vertical descent, 3D speed/distance, max speed.

**Backcountry ski touring — CRITICAL BUG:** Multiple Garmin forum reports confirm the Fenix 8's automatic ascent/descent detection in backcountry ski mode is **severely broken**. Users report: "The watch only records the entire activity as one long ascent, completely missing descent phases." The algorithm is fooled by fast skin-to-ski transitions (typical in ski mountaineering). **USE MANUAL MODE (LAP button to switch climb/descend) until Garmin fixes automatic detection.** This is a critical deficiency for the primary user's sport.

### Swim metrics (SWOLF, stroke detection)

**⚠️ PARTIALLY VALIDATED** — SWOLF is a widely used composite; stroke detection reliable for freestyle, weaker for breaststroke/butterfly.

SWOLF = time for one pool length (seconds) + stroke count. Lower = more efficient. Pool swimming: set accurate pool length. Open-water distance relies on GPS. Useful for cross-training pool sessions.

### Jump count

**❓ PROPRIETARY/UNVALIDATED** — Accelerometer-based aerial time detection. Fun metric; not reliable for serious training.

---

## VII. ENVIRONMENTAL AND ACCLIMATIZATION

### Heat acclimation

**❓ PROPRIETARY/UNVALIDATED** — 4-day "full acclimation" timeline is faster than the scientific consensus of 10–14 days.

Requires connected smartphone for weather data (ambient temperature, not wrist sensor). Activates above **22°C**. Tracks training sessions in heat, monitoring HR response relative to pace. Scale 0–100%. Claims full acclimation in minimum 4 training days — scientific consensus says 10–14 days for meaningful physiological acclimation (plasma volume expansion, sweat rate adaptation). **Does not account for humidity, individual variation, or hydration status.** Indoor heat training doesn't count. Adjusts VO2max estimates to prevent false fitness depression in hot conditions.

### Altitude acclimation

**⚠️ PARTIALLY VALIDATED** — Based on sound physiological principles (sleeping altitude drives EPO response); significant simplifications and limitations.

Uses barometric altimeter (continuous altitude tracking) + SpO2 + sleeping altitude (midnight check). Activates above **800 m**. Reports meters of altitude fully acclimated to (range 800–4,000 m). Full acclimation timeline: **~21 days** (aligns with red blood cell mass increase timelines in literature). Decay: returns to baseline after 21–28 days at low altitude.

**Critical failure modes for mountain athletes.** **Sleep altitude loophole:** If you train at 3,000 m daily but sleep at 700 m, the algorithm records zero acclimation. Individual variation is enormous (genetics, prior exposure). Prior altitude exposure history is not tracked — a climber returning to altitude after a week at sea level is treated as unacclimated despite retained hemoglobin mass. Does not assess AMS risk. Does not account for LHTH/LTHL strategies.

### Ambient temperature

**✅ VALIDATED** (connected weather data) / **Poor** (wrist sensor for ambient) — The wrist sensor reads ~body temperature, not ambient. For physiological features, connected weather data is always used. Ensure phone is connected for heat acclimation tracking.

---

## VIII. OTHER METRICS

### Personal records — Automatically tracks fastest times at standard distances (1K, 1mi, 5K, 10K, half marathon, marathon), longest activities, and highest weights for strength movements. PRs within longer activities are auto-calculated.

### Fall/incident detection — Uses accelerometer + gyroscope to detect sudden impacts during outdoor GPS activities. 15-second countdown, then sends automated message with GPS location to emergency contacts via paired phone. Fenix 8 Pro with inReach can send SOS via satellite. Generally reliable for genuine crashes; occasional false triggers from hard impacts.

### Jet lag adviser — Plans circadian rhythm adjustment during travel. Recommends light exposure timing, sleep timing, and activity suggestions. Requires trip planning in Garmin Connect app. Useful for mountain athletes traveling to distant ranges.

### Adaptive step/calorie goals — Auto-adjusts daily targets based on recent activity levels.

---

## IX. DATA ECOSYSTEM AND EXPORT

### Raw data access for the Ascent coaching system

**FIT file export** provides the most complete data: per-second GPS, HR, cadence, power, altitude, temperature, vertical oscillation, GCT, GCT balance, stride length, running power, respiration rate, and critically, **beat-to-beat RR intervals** in `hrv` messages. Raw overnight RR intervals are stored in monitor FIT files on the watch's file system and can be extracted via USB.

**Garmin Health API** provides programmatic access to: daily summaries, activity FIT files, sleep data, HRV summaries (5-min epoch values), SpO2, skin temperature, respiration, body composition, and user metrics (VO2max, training load). Available to approved partners/developers.

**Third-party integrations:** Strava (auto-sync), TrainingPeaks (auto-sync), **Intervals.icu** (recommended direct Garmin Connect connection for richest data including HRV, respiration, and Garmin-specific metrics that Strava strips). Python libraries (`fitparse`, `garmindb`) enable full FIT file parsing including RR interval extraction.

---

## Mountain athlete metric hierarchy: what deserves decision-making weight

The following ranking applies specifically to a mountain athlete doing ski touring, splitboarding, hike-and-fly paragliding, and gym strength training, based on the validation evidence and mountain-specific reliability assessed above.

### PRIMARY decision-making metrics (validated, reliable, actionable)

These metrics have sufficient validation and practical utility to directly inform training and recovery decisions:

- **Overnight HRV 7-day trend (RMSSD)** — The single most actionable recovery metric. CCC = 0.87 vs ECG. Use the 7-day rolling average; sustained decline >1 SD below baseline for 3+ days triggers action. Establish altitude-specific baselines.
- **Resting heart rate 7-day trend** — Validated, robust. Sustained shift >3 bpm in 7-day average is meaningful. Simple, hard to misinterpret.
- **Lactate threshold HR** — Directly applicable for pacing sustained climbs across all mountain modalities. Use guided test with chest strap. MAPE ~5–7%.
- **Barometric altitude and ClimbPro** — Well-understood physics. Critical for mountain planning and execution. Manually calibrate at known points.
- **GPS (All Systems + Multi-Band / SatIQ)** — Industry-leading accuracy on Fenix 8. Primary navigation and performance tracking tool.
- **GCT balance (L/R, requires chest strap)** — Strongest evidence linking any running dynamic to economy/injury risk (R = 0.808). Investigate imbalances >2%.

### SUPPORTING context metrics (partially validated, useful with interpretation)

These provide useful context but should not be sole drivers of decisions:

- **VO2max trend** — Track direction over weeks, ignore absolute value. Expect 3–5 point drops on trail runs and at altitude.
- **Real-time stamina** — Excellent pacing tool for mountain days >2 hours despite being unvalidated. Ensure HRmax is correct.
- **Training load (EPOC-based acute/chronic)** — Sound physiological basis. Useful for periodization awareness. Ignore ACWR as injury predictor.
- **Recovery time** — Useful relative indicator of session demand. Supplement with subjective assessment after eccentric-dominant days (descents, strength).
- **Sleep staging trends** — 69.7% accuracy limits single-night utility. Multi-night patterns (declining deep sleep %, increasing wake %) are more meaningful.
- **Stress score** — Measures autonomic arousal, not perceived stress. Useful for detecting sustained sympathetic activation.
- **Respiration rate trends** — Excellent at rest (r > 0.92 vs PSG). Sustained overnight elevation signals recovery issues or early illness.
- **Cadence** — Validated (ICC 0.931). Useful for running form monitoring; corrupted by trekking poles.
- **Running power (for trail pacing)** — Unvalidated but practically useful for even-effort pacing on variable terrain. Never compare across platforms.
- **Load focus distribution** — Validated concept (polarized training monitoring). Ensure LTHR is accurate.
- **Hill score** — Most mountain-relevant metric but completely unvalidated. Directional trend indicator only.
- **Altitude acclimation** — Physiologically grounded but oversimplified. Useful directional guide for expeditions.
- **Calories** — ±30% accuracy. Use as directional estimate for nutrition planning, never precise.

### DEMOTED or IGNORED metrics (proprietary composites, discredited, or unreliable for mountain use)

These should be visually demoted in the coaching system or decomposed into their validated inputs:

- **Body Battery** — Proprietary composite masking inputs. Decompose into HRV + sleep + stress data. Already demoted by existing KB.
- **Training Readiness** — Black box composite with proprietary weighting and no validation. Decompose into raw HRV, sleep score, and training load separately. Already demoted by existing KB.
- **Training Status** — Proprietary categorical label that flip-flops with minor VO2max fluctuations. Misleading for multi-sport mountain athletes (ski touring generates no VO2max updates → false "Detraining").
- **ACWR / Load Ratio** — Discredited as injury predictor by Impellizzeri, Lolli, Wang. Useful only as periodization awareness (am I training more or less than baseline?). Already demoted by existing KB.
- **Race Predictor** — Flat road only. Useless for trail/mountain predictions.
- **SpO2 above 3,000 m** — >50% error rate, systematically overestimates, dangerous. Carry a fingertip oximeter.
- **Endurance Score** — Unvalidated, known bugs, no actionable feedback.
- **Performance Condition** — Confounded by terrain, altitude, heat. Useful as a rough readiness signal only.
- **Skin temperature in alpine environments** — Ambient artifacts from sleeping bags, cold tents, and bivouacs overwhelm physiological signals.
- **Heat acclimation** — 4-day "full" timeline is optimistic vs 10–14 day scientific consensus. Does not account for humidity.
- **Fitness Age** — Motivational tool only. Not actionable for training decisions.
- **Abnormal HR alerts** — Simple threshold alarm, no clinical utility.

---

## Conclusion

The Fenix 8's sensor suite is comprehensive and its Firstbeat algorithms represent the most physiologically sophisticated consumer wearable engine available, but **the gap between marketing claims and independent validation remains wide** for most composite metrics. The validated core — overnight HRV trends, resting heart rate, lactate threshold, and barometric elevation — provides genuinely useful physiological signal for a mountain athlete. The key principle for the Ascent coaching system is to **prioritize raw, validated signals over proprietary composites**: RMSSD over Body Battery, sleep HRV over Training Readiness, EPOC-based load trends over Training Status labels.

For mountain-specific use, the Fenix 8 has three notable weaknesses. First, **ski touring activities do not update VO2max**, causing cascading staleness in Training Status and Race Predictor. Second, the **backcountry ski auto-detection is currently broken**, requiring manual lap-button transitions. Third, **SpO2 accuracy at altitude is dangerously poor**, requiring a separate fingertip oximeter for any safety-critical altitude monitoring. The coaching system should flag these limitations explicitly and route around them — using LTHR for cross-modal intensity guidance, manual sport tracking for ski touring, and external SpO2 devices above 3,000 m.

The most underappreciated metric in the suite is **GCT balance** (R = 0.808 with running economy) — the only running dynamic with strong evidence linking it to performance outcomes. The most overmarketed is **Training Status**, which combines a partially validated signal (VO2max trend) with proprietary logic to produce categorical labels that frequently mislead mountain athletes whose activities don't cleanly fit the running/cycling paradigm Firstbeat was designed for.