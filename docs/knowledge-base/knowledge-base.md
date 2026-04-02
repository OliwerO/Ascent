# Ascent Scientific Knowledge Base — Unified Reference for AI Coaching

**Version:** 1.2 — April 2026
**Scope:** Strength training, mountain endurance (ski touring/splitboarding, hike-and-fly paragliding), concurrent training, recovery, periodization, and biomarker integration for a recreational mountain athlete based in Innsbruck, Austria.
**Purpose:** Machine-readable decision reference for the Ascent AI coaching system. Every number, threshold, and protocol detail is preserved from source research. When sources conflict, all positions are presented with relative evidence strength.
**Assumptions:** All volume prescriptions assume "hard working sets" (0–4 RIR, 5–30 reps, 30–85% 1RM). All recommendations assume adequate protein intake (1.6–2.2 g/kg/day) and sufficient sleep (7–9 hours) unless otherwise specified.
**Changelog v1.2:** Added Domain 7 (Metric Hierarchy & Signal Quality) and Domain 8 (Dashboard & Communication Design Principles). Updated §1.1 with double progression decision logic, §1.3 with 2025 SUCRA autoregulation rankings, §1.5 with autoregulated deload triggers and natural deload concept, §3.1 with fatigue-driven interference mechanism clarification and progression expectations, §3.1 application rule with session displacement strategy, §3.4 with e1RM tracking rules, §4.1 with Le Meur et al. (2013) HRV caveat, §4.3 with subjective wellness questionnaire specification and Nummela et al. (2024) finding.

**Changelog v1.1:** Added Integration Rules #21–24 (schedule disruptions, illness, multi-day touring, caloric deficit). Corrected Schoenfeld 10+ sets claim to reflect non-significant trend (p=0.074). Updated §1.3 with Robinson et al. (2024) proximity-to-failure dose-response distinction. Corrected Roberts snowboarding HR data (§2.5c) to distinguish session average from active riding. Added §2.7 (multi-day touring protocol), §4.6 (training during illness), §4.7 (caloric deficit interaction), §5.6 (schedule disruption management). Updated §5.1 with 2025 ACSM Position Stand context. Updated §6.4 with creatine cognitive benefits. Added missing landmark sources throughout.

-----

# INTEGRATION SUMMARY: Critical Cross-Domain Decision Rules

The following 24 rules represent the highest-priority cross-domain interactions the AI coach must enforce. Violating any of these creates contradictory programming.

**1. Never schedule heavy lower-body strength within 8 hours after a long/hard mountain day.** Running economy and mountain performance decrease within this window (Doma et al., 2017). The interference effect on lower-body power is significant when sessions are <6 hours apart (Robineau et al., 2016: same-session concurrent training produced the worst outcomes). Place strength on the preceding or following day, with ≥24 hours separation preferred. → Cross-ref: Concurrent Training §2, Periodization §3.

**2. Strength-before-endurance ordering when same-day training is unavoidable.** Two independent meta-analyses (Eddens et al., 2018; Murlasits et al., 2018) confirm a ~7% advantage for lower-body dynamic strength. Endurance gains are unaffected by either order. Minimum 6-hour gap required; 3-hour gap acceptable only for low-intensity endurance. → Cross-ref: Concurrent Training §2, Periodization §3.

**3. Intensity is the non-negotiable variable during maintenance phases — volume and frequency are expendable.** Strength can be maintained for up to 32 weeks with 1 session/week and as few as 1 set per exercise (89% volume reduction), but only if load stays ≥70–85% 1RM (Bickel et al., 2011; Spiering et al., 2021). Endurance can be maintained with 2 sessions/week if at least 1 includes intervals at ≥80% HRmax (Spiering et al., 2021; Slettaløkken & Rønnestad, 2014). → Cross-ref: Concurrent Training §4, Periodization §1, Strength §5.

**4. Deload both modalities simultaneously.** Deloading only strength while pushing endurance (or vice versa) negates the recovery benefit. Both streams generate fatigue that accumulates on the same body. Reduce strength volume 40–50% and endurance volume 40–60% in the same week. → Cross-ref: Recovery §5, Strength §5, Periodization §2.

**5. Altitude compresses HR zones and inflates perceived training intensity.** At 2,000 m, VO2max is reduced ~9–10% acutely; at 3,000 m, ~15–17%. Reduce HR zone boundaries by 5 bpm for 1,500–2,500 m and by 8–10 bpm for 2,500–3,000 m. When RPE and HR disagree at altitude, trust RPE. → Cross-ref: Endurance §4, Recovery §2, Recovery §4 (nutrition).

**6. A "casual" mountain day can be a maximal workout.** Walking at 5 km/h on a 20% grade demands ~91% VO2max for a recreational athlete with VO2max of 45 ml/kg/min (Minetti et al., 2002). Add altitude, pack weight, and cold — and an "easy tour" can exceed the athlete's aerobic ceiling. The AI must calculate effective intensity from GPS speed, grade, altitude, and pack weight. → Cross-ref: Endurance §3, Concurrent Training §1.

**7. Prevent gray-zone drift — the single most impactful coaching intervention.** The polarized model requires ~80% of sessions below VT1 (Zone 1). Flag any session where average HR falls in the 78–88% HRmax range as potential gray-zone violation. Mountain sessions naturally drift into moderate intensity due to steep terrain, altitude, and competitive instinct. → Cross-ref: Endurance §1, Periodization §1.

**8. Account for the ~1 rep RPE underprediction error.** Halperin et al. (2022): trainees underpredict RIR by ~0.95 reps on average (note: I² = 97.9%, high heterogeneity — accuracy improves closer to failure, with heavier loads, and in later sets). Program most hypertrophy volume at RPE 7–8 (the trainee is likely actually at RPE 8–9). Accuracy improves closer to failure and with lower-rep sets (≤12 reps). → Cross-ref: Strength §3.

**9. Resort snowboarding = moderate-intensity intermittent activity, not high-intensity training.** Whole-session average HR is 64 ± 9% HRmax (Roberts, 2020), but during active riding HR averages 76 ± 10% HRmax (142 ± 20 bpm) — a substantially higher demand than the session average suggests. Only 33% of session time is active riding. Do not count snowboarding toward high-intensity quotas, but do not underestimate the eccentric quad loading. A 4-hour resort session ≈ 60–90 minutes of moderate continuous exercise. Requires 24+ hours before lower-body strength work. Note: Roberts (2020) is a master's thesis (Cal State San Marcos), not a peer-reviewed journal article. → Cross-ref: Endurance §5c, Periodization §3.

**10. Never exceed 3 consecutive weeks without heavy strength training during in-season.** Rønnestad et al. (2010, 2015, 2022) established this as the critical threshold: 1 heavy session every 7–10 days maintains strength; 1x/2 weeks is insufficient. After 3–4 weeks without strength training, losses begin that take ~half the detraining duration to regain. → Cross-ref: Concurrent Training §4, Periodization §1.

**11. Iron status gates altitude training readiness.** Ferritin must be ≥40 ng/mL before altitude exposure to support erythropoiesis (Sim et al., 2019). Screen 8–10 weeks before planned altitude camps. Altitude drives a 3–5-fold increase in erythropoiesis, depleting iron stores rapidly in deficient athletes. → Cross-ref: Biomarkers §1A, Endurance §4, Recovery §4.

**12. Sleep <6 hours = red alert for next-day programming.** Reduce training volume by ≥50%, eliminate high-intensity work. Compound movements (squats, deadlifts) are more vulnerable than isolation exercises. After 2+ nights of restriction, reliable strength decrements emerge (~3% maximal strength, ~10% strength endurance, ~21% skill-based). → Cross-ref: Recovery §2, Periodization §5.

**13. Multi-signal convergence for readiness decisions — never use a single metric.** When ≥3 indicators are simultaneously degraded (HRV suppressed, sleep poor, subjective fatigue elevated, RPE inflated), intervene with load reduction regardless of programmed plan. Subjective measures are more sensitive daily; HRV detects maladaptation weeks before conscious perception. → Cross-ref: Recovery §1, §3, Periodization §5.

**14. Carbohydrate needs scale dramatically with mountain day duration.** Light days: 3–5 g/kg/day. Moderate: 5–7 g/kg. Long touring days (3–6 hours): 7–10 g/kg. All-day mountain objectives: 8–12 g/kg. Altitude preferentially increases CHO oxidation. Underfueling at altitude is the primary driver of low T3 syndrome and RED-S in mountain athletes. → Cross-ref: Recovery §4, Biomarkers §1E, Endurance §5a.

**15. Low-intensity endurance causes minimal molecular interference with strength.** AMPK returns to baseline within 1–3 hours; moderate cycling at 70% VO2max 6 hours before resistance exercise does not inhibit mTOR (Lundberg et al., 2012). Mountain touring at conversational pace is not a meaningful interference risk. High-intensity endurance and glycogen-depleted states cause the greatest AMPK activation. → Cross-ref: Concurrent Training §1, Periodization §3.

**16. Cardiac drift invalidates HR-based zone classification after ~60 minutes.** Typical drift: 10–20 bpm over 30–60 minutes, ~3–5 bpm per 30 minutes. Base zone classification on first-hour HR data. For every hour beyond the first, subtract 3–5 bpm from recorded HR before classification. Uphill Athlete test: <3.5% drift over 60 min = below aerobic threshold; >5% = above. → Cross-ref: Endurance §2.4, Endurance §1.3.

**17. Track vertical gain as an independent load metric with ACWR.** 100 m vertical gain ≈ 1.0–1.5 km flat running in energy cost. Keep weekly vertical within 0.8–1.3× the 4-week rolling average. Never allow a single session to exceed 1.5× the average of the previous 4 similar sessions. → Cross-ref: Endurance §3.5, §6.2, Periodization §5.

**18. Residual training effects enable block periodization confidence.** Aerobic endurance persists ~30 ± 5 days; maximal strength ~30 ± 5 days; anaerobic glycolytic endurance ~18 ± 4 days; strength endurance ~15 ± 5 days; maximal speed only ~5 ± 3 days (Issurin, 2010). A 2-week taper or endurance-focus block will not meaningfully erode aerobic or strength fitness. → Cross-ref: Periodization §1, §2, §4, Concurrent Training §3.

**19. Exercise selection should be driven by SFR during hypertrophy phases and specificity during strength phases.** High-SFR exercises (hack squat, chest-supported row, cable lateral raise, leg extension) allow more productive weekly volume because they don't deplete recovery budgets. Reserve low-SFR compounds (conventional deadlift, heavy back squat, bent-over row) for strength blocks. → Cross-ref: Strength §6, §7, Periodization §2.

**20. Ferritin and Vitamin D are the highest-yield biomarker screens for mountain athletes.** Iron status directly limits aerobic capacity; vitamin D deficiency affects 33–90% of athletes at northern latitudes in winter. Both are modifiable with supplementation and both interact with altitude exposure, training volume, and seasonal light restriction. Screen at minimum twice yearly (autumn and spring). → Cross-ref: Biomarkers §1A, §1D, Recovery §4.

**21. When life disrupts the plan — shift, don't skip.** Schedule disruptions are inevitable. The AI must consolidate key training elements into available sessions rather than attempting to replicate missed sessions. Prioritize the highest-value session for the current phase (strength session during strength block, long endurance during endurance block). A single well-executed compound session preserves more fitness than two rushed, fatigued catch-up sessions. Detraining is negligible for 1 week, minimal for 2 weeks, and only begins to meaningfully erode strength after 3–4 weeks (Bosquet et al., 2013). See §5.6 for full protocol. → Cross-ref: Periodization §5, §5.6, Concurrent Training §4.

**22. Training during illness requires the conservative rule: if in doubt, rest.** The traditional "neck check" (above-neck symptoms = train light, below-neck = rest) lacks supporting evidence and may be hazardous because cardiogenic viruses can present with upper respiratory symptoms only (Harju et al., 2022). For mountain athletes, the safety margin is thinner: even mild illness at altitude compounds immune stress and impairs judgment in avalanche terrain and during paraglider launches. Any fever >38°C or systemic symptoms = complete rest. No mountain-specific activity until 2–3 days symptom-free. See §4.6 for full protocol. → Cross-ref: Recovery §4.6, Periodization §5.

**23. Multi-day back-to-back touring requires deliberate load management.** 16–20 hours between consecutive ski touring days is insufficient for full quadriceps recovery (Koller et al., 2018). Cumulative fatigue compounds exponentially, not linearly — day 3 impairment exceeds the sum of day 1 and day 2 impairment. Postural control impairment peaks on day 3 of consecutive hiking, creating direct fall risk. Plan rest days every 3rd day, front-load easier stages, and increase carbohydrate intake to 50–70 g/hour during activity. See §2.7 for full protocol. → Cross-ref: Endurance §2.7, Recovery §4, Integration Rule #14.

**24. Energy deficit impairs lean mass gains but not strength gains — protect intensity, increase protein.** Murphy & Koehler (2022): deficits >~500 kcal/day prevented lean mass gains entirely during resistance training, but strength gains were preserved regardless of deficit size. Protein intake of 2.0–2.4 g/kg/day significantly improves lean mass retention during deficit. Cap weight loss at ~0.5–0.7% bodyweight per week. Never schedule deficit phases during peak training or competition periods. See §4.7 for full protocol. → Cross-ref: Recovery §4.7, Biomarkers §1E, Periodization §1.


-----

# DOMAIN 1: STRENGTH TRAINING PROGRAMMING

## 1.1 Progressive overload models

### Core principle

Progressive overload — systematically increasing training demands over time — is the single most fundamental driver of adaptation. The optimal overload model depends on training age: novices respond to simple linear load increases every session, intermediates benefit from double progression or undulating schemes, and advanced trainees require block periodization with autoregulated loading. No periodization model is dramatically superior to another when volume is equated; the primary evidence is that any structured periodization outperforms non-periodized training (effect size 0.43–0.84). The 2025 ACSM Position Stand (Currier, McLeod, Phillips et al.) confirmed across 137 systematic reviews that periodization was not significantly superior to non-periodized programs when progressive overload was consistently applied — reinforcing that progressive overload is the true driver, with periodization serving as its organizational framework.

### Evidence summary

**Linear progression** works via session-to-session load increases of **2.5–5 lbs (upper body) and 5–10 lbs (lower body)** for novices. The ACSM Position Stand (2009) recommends a 2–10% load increase when the trainee can perform 1–2 reps beyond the target RM. Linear progression typically stalls after **3–6 months** of consistent training as neural adaptations plateau.

**Double progression** increases reps within a fixed range before increasing load. A standard protocol: train at a weight until all sets hit the top of the range (e.g., 3×12), then increase load by the smallest available increment and resume at the bottom of the range (e.g., 3×8). Tighter rep ranges (2-rep gaps like 4–6) suit barbell compounds; wider ranges (4–6-rep gaps like 8–15) suit isolation and machine exercises where percentage jumps are smaller. **Decision logic for automated double progression:** when all sets hit the top of the prescribed rep range with ≥ 2 RIR, increase weight by the minimum increment (2.5 kg compounds, 1–2 kg isolation) and reset reps to the bottom of the range. If reps decrease from the previous session at the same weight, flag for fatigue assessment and cross-reference the mountain activity log. When load stalls for 3+ consecutive attempts, add one set per exercise (up to a per-session maximum) for 3–4 weeks, then retry load progression.

**Undulating periodization (DUP)** varies intensity/volume within each week. A typical structure: Day 1 heavy (4–6 sets × 3–5 reps @ 85–90% 1RM), Day 2 moderate (3–4 sets × 8–12 reps @ 65–80%), Day 3 light (3–4 sets × 12–15 reps @ 50–65%). Zourdos et al. (2016) found DUP configurations produce significant 1RM gains in trained powerlifters over 6 weeks, with some weekly orderings slightly outperforming others. The Moesgaard et al. (2022) meta-analysis found DUP favored over linear periodization for 1RM strength in trained participants **(ES = 0.61, p = 0.04)** but showed no difference for hypertrophy. The Williams et al. (2017) meta-analysis confirmed periodized > non-periodized (ES = 0.43), with undulating models slightly more favorable. Stronger By Science re-analysis estimated undulating periodization produced strength gains **~28% faster** than linear (weekly gains: 2.19–2.24% vs. 1.57–1.58%).

**Block periodization** sequences mesocycles with concentrated training emphases: Accumulation (hypertrophy, 50–70% 1RM, high volume, 2–6 weeks) → Transmutation (strength, 75–90% 1RM, moderate volume, 2–4 weeks) → Realization (peaking, 90%+ 1RM, low volume, 1–3 weeks). The rationale relies on residual training effects — hypertrophy adaptations persist ~30 days, enabling them to carry over into subsequent strength and peaking phases. Issurin (2008, 2016) demonstrated that block periodization of strength and endurance training induces superior adaptations compared to traditional mixed programming. García-Pallarés et al. (2010) demonstrated that BP achieved similar or better aerobic improvements to traditional periodization with **half the endurance training volume** in world-class kayakers.

**Meta-analytic comparisons of periodization models:** Harries et al. (2015) and Grgic et al. (2017) show **no significant difference** between linear, undulating, and block periodization for strength or hypertrophy when volume is equated (pooled Cohen's d = −0.02 for hypertrophy). DUP is useful for maintaining multiple qualities during in-season phases. The 2025 ACSM Position Stand (Currier et al.) synthesized 137 systematic reviews and reaffirmed that the choice of periodization model matters less than whether progressive overload is systematically applied.

**Currier et al. (2023, BJSM) Bayesian network meta-analysis** — the largest network meta-analysis on RT prescription to date — ranked optimal combinations of load, sets, and frequency for both strength and hypertrophy, concluding that higher loads (>60% 1RM) and moderate-to-high volumes consistently outperformed other combinations, but no single periodization scheme was reliably superior.

**Progression rates by training level:**

| Level | Training age | Progression rate | Frequency |
|---|---|---|---|
| Novice | 0–6 months | 5–10 lbs/session lower, 2.5–5 lbs upper | Every session |
| Late novice | 6–12 months | 5 lbs/session → weekly | Weekly |
| Intermediate | 1–3 years | 5–10 lbs/month on major lifts | Every 1–3 weeks |
| Advanced | 3+ years | 2.5–5 lbs/month or per mesocycle | Monthly or per cycle |

### Application rule

- IF training age < 6 months → linear progression with session-to-session load increases (2.5–5 lbs upper, 5–10 lbs lower).
- IF trainee fails to progress for 2 consecutive sessions at the same load → transition to double progression.
- IF training age 6–12 months → double progression with weekly load increments; use tighter rep ranges (4–6) for barbell compounds, wider ranges (8–15) for isolation.
- IF training age 1–3 years → implement DUP or weekly undulating periodization with RPE-based autoregulation; expect weekly-to-biweekly load progression.
- IF training age > 3 years → block periodization with mesocycles of 3–6 weeks, progressing volume within each block and load across blocks.
- IF repeated failure to hit prescribed reps or excessive RPE drift for ≥2 weeks → automatically switch from current model to next-complexity model (linear → DUP → block).
- ALWAYS cap weekly load/volume increases at **≤10%**.
- REMEMBER: Periodization is the organizational framework — progressive overload is the driver. Missing a mesocycle transition point is not a crisis; failing to progressively overload is.

### Key sources

- Rhea MR, Alderman BL. "A meta-analysis of periodized versus nonperiodized strength and power training programs." *Research Quarterly for Exercise and Sport*, 2004; 75(4): 413–422.
- Harries SK, Lubans DR, Callister R. "Systematic review and meta-analysis of linear and undulating periodised resistance training programmes on muscular strength." *JSCR*, 2015; 29(4): 1113–1125.
- Williams TD et al. "The effect of periodized resistance training on strength." *Sports Medicine*, 2017; 47: 2083–2100.
- Moesgaard L et al. "Undulating vs. linear periodization for strength: a meta-analysis." 2022. PMID: 35044672.
- ACSM Position Stand. "Progression models in resistance training for healthy adults." *Medicine & Science in Sports & Exercise*, 2009. PMID: 19204579.
- Rhea MR et al. "A meta-analysis to determine the dose response for strength development." *Medicine & Science in Sports & Exercise*, 2003; 35(3): 456–464.
- Zourdos MC et al. "Modified daily undulating periodization model produces greater performance than a traditional configuration in powerlifters." *J Strength Cond Res*, 2016.
- Issurin VB. "Block periodization versus traditional training theory: a review." *J Sports Med Phys Fitness*, 2008; 48(1): 65–75.
- Issurin VB. "Benefits and limitations of block periodized training approaches to athletes' preparation: a review." *Sports Med*, 2016.
- Currier BS, McLeod JC, Phillips SM et al. "ACSM Position Stand: Resistance Training Prescription for Muscle Function, Hypertrophy, and Physical Performance in Healthy Adults: An Overview of Reviews." *Medicine & Science in Sports & Exercise*, 2025.
- Currier BS et al. "Resistance training prescription for muscle strength and hypertrophy in healthy adults: a systematic review and Bayesian network meta-analysis." *BJSM*, 2023. DOI: 10.1136/bjsports-2023-106807.

### Cross-references

- → Periodization §2 (mesocycle design uses these models as building blocks)
- → Concurrent Training §3 (block periodization is the preferred annual structure for mountain athletes)
- → Strength §3 (RPE autoregulation modifies all progression models for intermediates+)


-----

## 1.2 Volume landmarks per muscle group

### Core principle

Training volume — measured in hard working sets per muscle group per week — follows a dose-response curve with **diminishing returns**. Three landmarks define the actionable range: **MEV** (Minimum Effective Volume, the floor for measurable growth), **MAV** (Maximum Adaptive Volume, the zone of best returns), and **MRV** (Maximum Recoverable Volume, the ceiling beyond which recovery fails). A mesocycle should start near MEV and progressively ramp toward MRV over 4–6 weeks, then deload. These landmarks shift upward with training experience as muscles become harder to stimulate but work capacity increases.

### Evidence summary

**Dose-response relationship from meta-analyses:**

The Schoenfeld, Ogborn & Krieger (2017) meta-analysis established the dose-response: each additional weekly set produced an effect size increase of **0.023, corresponding to +0.37% muscle size gain** (continuous dose-response significant at p = 0.002). The categorical analysis showed a non-significant trend favoring **10+ sets/week** (p = 0.074) — this was a directional finding, not a confirmed threshold. The AI should treat the continuous dose-response as the validated finding, not 10 sets as a hard minimum. Krieger (2010) found multiple sets produced **40% greater hypertrophy effect sizes** than single sets, with a dose-response pattern: ES of 0.24 (1 set), 0.34 (2–3 sets), 0.44 (4–6 sets per exercise). Baz-Valle et al. (2022) found **12–20 weekly sets per muscle group** to be the optimal range, with 20+ sets only benefiting certain muscles (triceps, ES = −0.50).

The most comprehensive analysis — Pelland et al. (2025, *Sports Medicine*, 67 studies, 2,058 participants) — found the volume-hypertrophy relationship best fit by a **square root model** (diminishing returns with no clear ceiling), with substantial diminishing returns beyond ~12–20 sets. This study introduced a novel "fractional" set counting method, weighting indirect (compound) volume at 0.5× direct (isolation) volume — the AI should consider this when calculating effective weekly volume for muscles that receive substantial compound stimulation.

Schoenfeld's 2017 dose-response meta-analysis categorical breakdown: <5 sets/muscle/week produced a 5.4% gain, 5–9 sets produced 6.6%, and 10+ sets produced 9.8% — but note the categorical comparison was non-significant (p = 0.074).

**Israetel/Renaissance Periodization volume landmarks (intermediate-level estimates, direct sets per week):**

| Muscle group | MV | MEV | MAV range | MRV | Frequency |
|---|---|---|---|---|---|
| Quads | 6 | 8 | 12–18 | 20+ | 1.5–3×/wk |
| Hamstrings | 4 | 6 | 10–16 | 20+ | 2–3×/wk |
| Glutes | 0 | 0 | 4–12 | 16+ | 2–3×/wk |
| Chest | 8 | 10 | 12–20 | 22+ | 1.5–3×/wk |
| Back | 8 | 10 | 14–22 | 25+ | 2–4×/wk |
| Side/rear delts | 0 | 8 | 16–22 | 26+ | 2–6×/wk |
| Front delts | 0 | 0 | 6–8 | 12+ | 1–2×/wk |
| Biceps | 5 | 8 | 14–20 | 26+ | 2–6×/wk |
| Triceps | 4 | 6 | 10–14 | 18+ | 2–4×/wk |
| Calves | 6 | 8 | 12–16 | 20+ | 2–4×/wk |
| Abs | 0 | 0 | 16–20 | 25+ | 3–5×/wk |
| Traps | 0 | 0 | 12–20 | 26+ | 2–6×/wk |

MV/MEV of 0 means the muscle receives sufficient indirect stimulation from compound work to maintain or even grow without dedicated isolation.

**Landmarks by training level:** Beginners need ~6–10 sets/muscle/week within MAV and can sustain accumulation for up to 12 weeks. Advanced trainees may require 15–25+ sets/week and reach MRV within 3–4 weeks. The Perplexity research corroborates these ranges, noting MEV ~8–12, MAV ~14–20, MRV ~20–28 sets per muscle per week for many trained lifters.

**For maintenance (not growth):** 4–8 sets per major muscle group per week represents a comfortable floor. Bickel et al. (2011) demonstrated that even 3 sets total for legs (1 set per exercise) maintained strength — establishing the true floor at approximately **2–4 sets per muscle group per week**.

Individual variation is substantial (±30–50% based on genetics, sleep, stress, nutrition), so treat all numbers as starting estimates requiring personalized adjustment.

### Application rule

- IF beginner → initialize volume at ~8–10 sets/muscle/week (low end of MEV).
- IF intermediate → initialize at MEV for each muscle group from the RP landmarks table, adjusted upward based on prior cycle data.
- IF advanced → initialize at upper MEV or lower MAV; may require 15–22+ sets for priority muscle groups.
- WITHIN each mesocycle → progress by adding **1–3 sets per muscle group per week**.
- IF soreness resolves before next session AND performance improves → add 2–3 sets next week.
- IF performance stagnates → hold volume steady.
- IF performance declines for 2+ sessions → initiate deload to MV (~4–8 sets/muscle).
- IF per-session volume exceeds ~10 sets for a single muscle group → increase training frequency rather than session volume.
- IF in maintenance phase (endurance priority) → reduce to MV: 4–8 sets/muscle/week.
- Non-priority muscles during any phase → stay at MEV or MV.
- WHEN counting volume → consider Pelland's fractional method: compound sets that indirectly train a muscle count as ~0.5 direct sets for volume tracking.

### Key sources

- Schoenfeld BJ, Ogborn D, Krieger JW. "Dose-response relationship between weekly resistance training volume and increases in muscle mass." *Journal of Sports Sciences*, 2017; 35(11): 1073–1082. DOI: 10.1080/02640414.2016.1210197.
- Krieger JW. "Single vs. multiple sets of resistance exercise for muscle hypertrophy: a meta-analysis." *JSCR*, 2010; 24(4): 1150–1159.
- Baz-Valle S et al. "A systematic review of the effects of different resistance training volumes on muscle hypertrophy." *Journal of Human Kinetics*, 2022; 81: 199–210.
- Pelland JC, Remmert JF, Robinson ZP, Hinson QR, Zourdos MC. "The resistance training dose response: meta-regressions exploring the effects of weekly volume and frequency." *Sports Medicine*, 2025; 56(2): 481–505. DOI: 10.1007/s40279-025-02344-w.
- Israetel M, Hoffmann J, Smith CW. *Scientific Principles of Hypertrophy Training*. Renaissance Periodization.
- Schoenfeld BJ, Grgic J. "Evidence-based guidelines for resistance training volume to maximize muscle hypertrophy." *Strength & Conditioning Journal*, 2018; 40(4): 107–112.

### Cross-references

- → Strength §5 (deload protocols reset volume to MV)
- → Concurrent Training §4 (maintenance volume during endurance phases: 4–8 sets/muscle/week)
- → Periodization §2 (mesocycle volume progression within blocks)
- → Recovery §5 (deload volume reduction percentages)

-----

## 1.3 Intensity programming and RPE autoregulation

### Core principle

Intensity can be prescribed via fixed percentages of 1RM or autoregulated via RPE/RIR (Rate of Perceived Exertion / Reps in Reserve). Percentage-based training provides structure but cannot account for daily readiness fluctuations. RPE-based autoregulation naturally adjusts load to the trainee's current capacity, producing **comparable or slightly superior strength outcomes**. The hybrid approach — using percentages for planning and RPE for daily adjustment — is the practical optimum for intermediates and advanced trainees. Critically, the dose-response relationship between proximity to failure and adaptation differs for hypertrophy versus strength: hypertrophy increases nonlinearly as sets approach failure (favoring 1–3 RIR), while strength gains are similar across a wide RIR range (Robinson et al., 2024).

### Evidence summary

**The RIR-based RPE scale** (Zourdos et al., 2016; popularized by Mike Tuchscherer): RPE 10 = 0 RIR (failure), RPE 9 = 1 RIR, RPE 8 = 2 RIR, RPE 7 = 3 RIR.

**RPE accuracy research:**
- Halperin et al. (2022) meta-analyzed 13 publications (414 participants): trainees underpredict RIR by **~0.95 repetitions** on average. However, heterogeneity was extreme (I² = 97.9%) and the authors explicitly labeled this an "exploratory" meta-analysis. Accuracy improves closer to failure, with heavier loads, and in later sets — meaning the 0.95-rep average masks meaningful variation. Training status did **not** significantly predict accuracy in this meta-analysis.
- Zourdos et al. (2016): experienced squatters reported more accurate RPE at 1RM (9.80 ± 0.18 vs. 8.96 ± 0.43 for novices, p = 0.023).
- Refalo et al. (2023): trained individuals were within **0.40 (±0.68) reps of a 1-RIR target** and 0.90 (±0.81) reps of a 3-RIR target.

**Autoregulation vs. fixed loading outcomes:**
- **2025 network meta-analysis** ranked load prescription methods for squat 1RM improvement by SUCRA: **APRE 93.0% > RPE 66.8% > VBT 27.0% > percentage-based 13.2%**. This confirms autoregulation is superior to fixed loading, with RPE-based methods the most practical for automated implementation (requires no special equipment unlike VBT).
- Helms et al. (2018): RPE-based vs. percentage 1RM loading in periodized programs matched for sets and repetitions. Both groups significantly increased 1RM and muscle thickness, with non-significant but small effect size advantages favoring the RPE group.
- Mann et al. (2010): APRE significantly outperformed linear periodization in bench press 1RM (+93.4 N vs. −0.40 N, p = 0.02) and squat 1RM (+192.7 N vs. +37.2 N, p = 0.05) over 6 weeks.
- Graham & Cleather (2021): autoregulated training produced significantly greater strength gains than fixed loading: front squat **+11.7% vs. +8.3%** (p = 0.004), back squat **+10.8% vs. +7.1%** (p = 0.006) over 12 weeks.
- Zhang et al. (2021 meta-analysis): confirmed autoregulation is superior to fixed loading for maximal strength across multiple studies.

**Proximity to failure: different dose-response for hypertrophy vs. strength (Robinson et al., 2024, *Sports Medicine*):**

This is the first continuous dose-response meta-regression for proximity to failure. Key findings:
- **Hypertrophy** improves nonlinearly as sets approach failure. Training at 0–2 RIR produces meaningfully greater hypertrophy than training at 3–5 RIR.
- **Strength** gains are similar across a wide RIR range. Training at 2–4 RIR produces comparable strength gains to training at 0–1 RIR.
- **Practical implication:** During hypertrophy phases, the AI should push closer to failure (1–2 RIR). During strength phases, the AI can prescribe more conservative RIR (2–4) without sacrificing strength gains, thereby preserving recovery budget for concurrent endurance training.

Refalo et al. (2023): failure not superior to non-failure for hypertrophy (ES = 0.12, p = 0.343) — but the Robinson meta-regression clarifies that while failure itself isn't required, proximity to failure matters on a continuous scale. Refalo et al. (2024, *Journal of Sports Sciences*): within-subject RCT confirming **1–2 RIR produces comparable hypertrophy to failure** with less accumulated fatigue.

**RPE/RIR targets by goal (updated with Robinson et al. 2024 dose-response):**

| Goal | Optimal RPE | Optimal RIR | Evidence basis |
|---|---|---|---|
| Hypertrophy | 8–9 | 1–2 | Robinson et al. (2024): nonlinear dose-response favoring proximity to failure |
| Strength | 7–9 | 2–4 | Robinson et al. (2024): strength gains similar across wide RIR range |
| Most training volume (fatigue management) | 7–8 | 2–3 | Minimizes fatigue accumulation; preserves recovery for concurrent endurance |
| Peaking/testing | 9.5–10 | 0–1 | Reserved for competition or 1RM attempts |
| In-season maintenance | 8–9 | 1–2 | Maximize stimulus per set to compensate for reduced volume |

**Velocity-based readiness assessment (Weakley et al., 2021; González-Badillo et al., 2017):** Within-set velocity loss of **≤20%** provides the best balance of stimulus and recovery. Between-session readiness: first-rep velocity at standardized load vs. 30-day rolling average: **>95% = green** (train as planned), **90–95% = amber** (reduce volume), **<90% = red** (recovery session).

### Application rule

- IF training age < 1 year → use fixed percentages or double progression; RPE accuracy is insufficient.
- IF training age 6–12 months → introduce RPE tracking alongside percentage-based work for familiarization (2–3 week period).
- IF training age > 1 year → prescribe working sets with target RPE ranges (e.g., "4×6 @ RPE 8") and allow the trainee to self-select load.
- FOR structured peaking cycles → use hybrid: plan loads as percentages, adjust ±5% based on daily RPE.
- FOR hypertrophy volume → program at RPE 8–9 (1–2 RIR) to leverage the nonlinear proximity-to-failure dose-response. Account for ~1 rep underprediction: a prescribed RPE 8 is likely RPE 9 in reality, which is close to the hypertrophy sweet spot.
- FOR strength volume → program at RPE 7–8 (2–4 RIR). Strength gains do not require proximity to failure, so preserving recovery is the priority, especially during concurrent training phases.
- FOR in-season maintenance → push closer to failure (RPE 8–9) on the limited sets available, since volume is low and each set must carry maximum stimulus.
- IF RPE consistently overshoots target by >1 RPE for ≥2 weeks → flag as potential fatigue accumulation; reduce loads 2.5–5%.
- IF velocity data available → use first-rep velocity vs. 30-day average as readiness check before heavy sessions.
- TRACK estimated e1RM from recent sets to adjust percentage tables over time.

### Key sources

- Zourdos MC et al. "Novel resistance training-specific rating of perceived exertion scale." *JSCR*, 2016; 30(1): 267–275.
- Helms ER et al. "Application of the repetitions in reserve-based rating of perceived exertion scale for resistance training." *Strength & Conditioning Journal*, 2016; 38(4): 42–49.
- Helms ER et al. "RPE vs. percentage 1RM loading in periodized programs matched for sets and repetitions." *Frontiers in Physiology*, 2018.
- Halperin I et al. "Accuracy in predicting repetitions to task failure in resistance exercise: a scoping review and exploratory meta-analysis." *Sports Medicine*, 2022; 52(2): 377–390. DOI: 10.1007/s40279-021-01559-x.
- Mann JB et al. "The effect of autoregulatory progressive resistance exercise vs. linear periodization on strength improvement." *JSCR*, 2010; 24(7): 1718–1723.
- Graham T, Cleather DJ. "Autoregulation by 'repetitions in reserve' leads to greater improvements in strength." *JSCR*, 2021; 35(9): 2451–2456.
- Robinson ZP et al. "Exploring the dose-response relationship between estimated resistance training proximity to failure, strength gain, and muscle hypertrophy: a series of meta-regressions." *Sports Medicine*, 2024; 54(2): 303–321. DOI: 10.1007/s40279-024-02069-2.
- Refalo MC et al. "Influence of resistance training proximity-to-failure on skeletal muscle hypertrophy: a systematic review with meta-analysis." *Sports Medicine*, 2023; 53(3): 649–665. DOI: 10.1007/s40279-022-01784-y.
- Refalo MC et al. "Similar muscle hypertrophy following eight weeks of resistance training to momentary muscular failure or with repetitions-in-reserve in resistance-trained individuals." *Journal of Sports Sciences*, 2024. DOI: 10.1080/02640414.2024.2321021.
- Weakley J et al. "Velocity-based training: from theory to application." *Strength Cond J*, 2021.

### Cross-references

- → Periodization §5 (autoregulation at plan level uses RPE as a key signal)
- → Recovery §3 (subjective readiness interacts with RPE-based daily adjustments)
- → Integration Rule #8 (the ~1 rep underprediction error)
- → Concurrent Training §3 (RPE targets differ by phase to manage interference)


-----

## 1.4 Training frequency as a volume distribution tool

### Core principle

Training frequency per muscle group primarily matters as a **vehicle for distributing weekly volume**, not as an independent growth variable. When total weekly volume is equated, training a muscle 2×/week vs. 3×/week produces nearly identical hypertrophy. However, higher frequency may benefit **strength** through improved motor learning on compound lifts. The practical minimum is **2×/week per muscle group** for hypertrophy; the practical maximum is determined by how many sessions are needed to distribute the target weekly volume without exceeding ~10 sets per muscle per session.

### Evidence summary

**Hypertrophy:** Schoenfeld, Ogborn & Krieger (2016, 10 studies) found **2×/week promotes superior hypertrophy to 1×/week** (significant effect when pooling all measures). The updated Schoenfeld, Grgic & Krieger (2019, 25 studies) found **no significant difference** between higher and lower frequencies on a volume-equated basis (p > 0.05 for all subanalyses). Conclusion: "Individuals can choose weekly frequency per muscle group based on personal preference."

**Strength:** Grgic et al. (2018) found a significant overall effect of frequency (p = 0.003), with effect sizes rising from 0.74 (1×/wk) to 0.82 (2×/wk) to 0.93 (3×/wk) to 1.08 (4+×/wk). However, **when volume was equated, the effect disappeared** (p = 0.421) — indicating the strength benefit is mediated primarily through additional volume, with a possible secondary motor-learning component for multi-joint exercises (significant for compounds, p < 0.001; not for isolation, p = 0.324).

**Pelland et al. (2025)** meta-regression confirmed: frequency has a **negligible independent effect on hypertrophy** but a **consistently identifiable positive effect on strength**.

**MPS data:** Damas et al. (2015) shows MPS elevation lasts only **~24–48 hours** in trained individuals (shorter than in untrained), theoretically supporting 2–4×/week to maximize cumulative anabolic signaling — though the practical literature shows this doesn't translate to meaningful hypertrophy differences beyond 2×/week.

### Application rule

- DEFAULT to **2×/week** per muscle group as the base frequency.
- IF weekly volume exceeds ~12–14 sets for a muscle group AND per-session quality degrades → increase to 3×/week.
- FOR small, recovery-resilient muscles (side delts, biceps, calves, abs) → 3–6×/week is viable for distributing high MRV volumes.
- FOR large, fatiguing muscle groups (quads, back) → cap at 2–3×/week with ≥48 hours between sessions.
- FOR strength-focused compound lifts → consider 3–4×/week on the target lift for motor learning benefits.
- MATCH split type to available training days:
  - 3 days/week → Full body (each muscle 3×/wk)
  - 4 days/week → Upper/Lower (each muscle 2×/wk)
  - 5–6 days/week → Push/Pull/Legs (each muscle 2×/wk)
- FOR time-constrained users → permit 1×/week if total weekly sets fall in target volume range, but flag as suboptimal for most.

### Key sources

- Schoenfeld BJ, Ogborn D, Krieger JW. "Effects of resistance training frequency on measures of muscle hypertrophy." *Sports Medicine*, 2016; 46(11): 1689–1697.
- Schoenfeld BJ, Grgic J, Krieger JW. "How many times per week should a muscle be trained to maximize muscle hypertrophy?" *Journal of Sports Sciences*, 2019; 37(11): 1286–1295.
- Grgic J et al. "Effect of resistance training frequency on gains in muscular strength." *Sports Medicine*, 2018; 48(5): 1207–1220.
- Ralston GW et al. "Weekly training frequency effects on strength gain: a meta-analysis." *Sports Medicine — Open*, 2018; 4(1): 36.
- Pelland JC et al. "The resistance training dose response." *Sports Medicine*, 2025; 56(2): 481–505.
- Damas F et al. "A review of resistance training-induced changes in skeletal muscle protein synthesis." *Sports Medicine*, 2015; 45: 801–807.

### Cross-references

- → Strength §1.2 (volume landmarks determine when frequency must increase)
- → Periodization §3 (microcycle templates implement these frequency rules)
- → Concurrent Training §3 (weekly template selection depends on available training days)

-----

## 1.5 Deload protocols and supercompensation

### Core principle

A deload is a planned period of **reduced training stress (typically 5–7 days) designed to dissipate accumulated fatigue while preserving fitness**. The preferred method is a volume reduction deload — cutting weekly sets by 40–60% while maintaining load — because this preserves neural adaptations and technical proficiency. Deloads should be planned proactively every 4–6 weeks for intermediates and every 3–4 weeks for advanced trainees, with reactive triggers available to override the schedule when fatigue markers deteriorate sooner.

### Evidence summary

**Expert consensus and survey data:**
- Bell et al. (2023), international Delphi consensus: deloads should reduce volume through fewer sets, fewer reps, or reduced frequency, while intensity either stays the same or decreases by **~10% 1RM**.
- Rogerson et al. (2024), cross-sectional survey of 246 competitive athletes: average deload every **5.6 ± 2.3 weeks**, lasting **6.4 ± 1.7 days**. Athletes commonly reduced both reps per set and total weekly sets.
- Bell et al. (2024): 47% of athletes use pre-planned deloads, 13% purely autoregulated, ~39% combination. The combined approach is recommended.

**Complete rest vs. active deload:** Coleman et al. (2024) tested 1-week complete training cessation mid-program and found it **negatively impacted lower body strength** (~6% lower improvement) but had **no effect on hypertrophy, power, or muscular endurance** — confirming that active deloads are preferable to full rest for strength maintenance. Notably, Coleman et al. also found that **continuous training slightly outperformed a mid-program deload for 1RM gains**, suggesting deloads should not be reflexive calendar events but rather triggered by actual need.

**Schoenfeld et al. (2024)** confirmed that a 1-week deload after 4 weeks of high-volume training resulted in no loss of strength or muscle size.

**Theoretical basis — Fitness-Fatigue Model (Banister; Zatsiorsky):** Performance = fitness − fatigue. The fatigue after-effect has a short time constant (**τ₂ ≈ 7–11 days**) while the fitness after-effect persists much longer (**τ₁ ≈ 20–50 days**). During a deload, fatigue dissipates rapidly while fitness persists, producing a performance "supercompensation" effect. Tapering research shows **~2–8% improvement in maximal strength** from an effective taper.

**Deload prescription summary:**

| Parameter | Recommendation |
|---|---|
| Duration | 5–7 days (1 week) |
| Volume reduction | 40–60% fewer total sets |
| Intensity/load | Maintain or reduce ≤10% |
| Frequency | Maintain or slightly reduce |
| RPE target | 5–7 (3–5 RIR) |
| Exercise selection | Keep primary movement patterns; swap accessories freely |

**Volume reduction by recovery need:**

| Recovery need | Volume reduction | Intensity |
|---|---|---|
| Low (routine deload) | 25–45% | Maintain |
| Moderate (accumulated fatigue) | 40–60% | Maintain or slight decrease |
| High (overreaching signs) | 60–90% | Decrease |

**Deload frequency by training level:**

| Level | Frequency | Mesocycle ratio |
|---|---|---|
| Beginner (<1 year) | Every 8–12 weeks | 5:1–7:1 |
| Intermediate (1–3 years) | Every 4–6 weeks | 4:1 (most common) |
| Advanced (3+ years) | Every 3–4 weeks | 3:1 |
| Concurrent strength + endurance | Every 3–4 weeks | 3:1 |
| Athlete in caloric deficit | Subtract 2 weeks from standard | — |
| Athlete >40 years old | Default to 2:1 (2 hard, 1 recovery) | 2:1 |

### Application rule

- PREFER autoregulated deloads over calendar-fixed: Coleman et al. (2024) found continuous training slightly outperformed mid-program deloads, suggesting deloads should be need-driven, not reflexive.
- SCHEDULE proactive deloads: default every 4th week for concurrent training athletes (3:1 ratio), but allow autoregulation to override.
- ALLOW autoregulation to override: extend to week 5 if readiness markers remain strong; pull forward to week 3 if markers deteriorate.
- NEVER go beyond 6 weeks without a deload during progressive loading phases.
- RECOGNIZE "natural deloads": weeks with 3+ mountain days and only 1 gym session already function as partial deloads — the system should recognize these and not schedule a separate deload week immediately after.
- AUTOREGULATED DELOAD TRIGGERS (any of the following):
  - IF e1RM trends downward for ≥ 3 consecutive sessions
  - IF average session RPE exceeds target by ≥ 1.5 for 2+ weeks
  - IF trailing 2-week mountain volume exceeds 150% of baseline
  - IF subjective fatigue scores remain below threshold for 5+ days
- REACTIVE OVERRIDE TRIGGERS (trigger immediate deload regardless of schedule position):
  - IF RPE creeps >1 point at the same load for 2+ sessions
  - IF wellness scores decline for 2+ consecutive weeks
  - IF HRV mean drops >1 SD from baseline for 1+ week
  - IF morning resting HR elevated >5 bpm above baseline for 3+ days
  - IF ≥3 readiness indicators simultaneously degraded (see Recovery §3)
- DEFAULT to volume-reduction deload (cut sets by 40–50%, maintain load, maintain frequency).
- IF joint pain is elevated → combined reduction: cut load 10% AND sets 50%.
- AFTER deload → restart next mesocycle at MEV with potentially new exercise selections. Resume at pre-deload intensity but ~90% of pre-deload volume in first week back.

### Key sources

- Bell L et al. "Integrating deloading into strength and physique sports training programmes: an international Delphi consensus approach." *Sports Medicine — Open*, 2023; 9:87.
- Bell L et al. "A practical approach to deloading." *Strength & Conditioning Journal*, 2025.
- Bell L et al. "Deloading practices in strength and physique sports: a cross-sectional survey." *Sports Medicine — Open*, 2024.
- Coleman M et al. "Gaining more from doing less? The effects of a one-week deload period during supervised resistance training." *PeerJ*, 2024; 12:e16777.
- Rogerson D et al. "Deloading practices in strength and physique sports." *Sports Medicine — Open*, 2024.
- Schoenfeld BJ et al. Deload study confirming no loss after 4-week high-volume training, 2024.
- Chiu LZF, Barnes JL. "The fitness-fatigue model revisited." *Strength & Conditioning Journal*, 2003; 25(6).
- Bosquet L et al. "Effects of tapering on performance: a meta-analysis." *Med Sci Sports Exerc*, 2007; 39(8): 1358–1365.

### Cross-references

- → Recovery §5 (deload and recovery weeks — extended treatment with concurrent training considerations)
- → Periodization §2 (mesocycle design includes deload scheduling)
- → Periodization §5 (autoregulation triggers for reactive deloads)
- → Integration Rule #4 (deload both modalities simultaneously)


-----

## 1.6 Fatigue management and the stimulus-to-fatigue ratio

### Core principle

Fatigue in resistance training exists on two axes: **systemic** (CNS, hormonal, metabolic) and **local** (muscle damage, joint stress, connective tissue). These recover at different rates — acute neuromuscular fatigue resolves in 48–72 hours, while joint and connective tissue stress accumulates over weeks and requires a full deload to dissipate. The **Stimulus-to-Fatigue Ratio (SFR)** — how much adaptive stimulus an exercise provides relative to the fatigue it generates — should guide exercise selection, especially during high-volume hypertrophy phases. True overtraining syndrome from resistance training alone is **extremely rare**.

### Evidence summary

**Fatigue recovery timelines:**

| Type | Peak | Resolution |
|---|---|---|
| Acute neuromuscular | 0–24 hours | 48–72 hours |
| Muscle damage (DOMS) | 24–72 hours | 3–7 days |
| CNS voluntary activation | 0–24 hours | 24–48 hours |
| Joint/connective tissue | Gradual accumulation over weeks | Requires deload week(s) |
| Hormonal disruption | Days to weeks | 1–4 weeks with reduced load |

**SFR classification (Israetel/RP):**
- **High-SFR exercises** (preferred for hypertrophy volume): machine hack squat, chest-supported row, cable lateral raise, leg extension, leg press, seated cable row. Provide strong target-muscle stimulus with low systemic fatigue.
- **Low-SFR exercises** (reserved for strength blocks): conventional deadlift, heavy barbell back squat, bent-over row. Generate massive systemic fatigue relative to single-muscle stimulus.

**Overreaching classification (Meeusen et al., 2013 ECSS/ACSM Joint Consensus):**
- Functional overreaching (FOR): performance decrements lasting days to ~2 weeks that rebound with supercompensation.
- Non-functional overreaching (NFOR): decrements lasting weeks to months with no subsequent supercompensation.
- Overtraining syndrome (OTS): decrements lasting months to years.

**Bell et al. (2020)** found minimal evidence that true OTS has ever occurred from resistance training alone. Rogerson et al. (2024) found that **92.5% of training maladaptation cases** were accompanied by additional non-training stressors.

**Le Meur et al. (2014):** Acutely fatigued athletes who were NOT overreached showed **greater supercompensation (2.6%)** than those classified as functionally overreached — challenging the assumption that deliberate overreaching is necessary for recreational athletes.

**Fatigue detection markers:** RPE drift (same weights feeling harder week-to-week), performance decrements at matched RPE, grip strength decreases, HRV drops (daily morning RMSSD declining >1 SD from personal baseline), declining motivation, increased joint discomfort, disrupted sleep.

**HRV-specific fatigue detection:** Hypertrophic loading (5 × 10 at 70% 1RM) acutely suppresses rMSSD by **~64%**; maximal strength loading (15 × 1 at 100% 1RM) suppresses it by **~29%**. Recovery to baseline takes **24–72 hours** after heavy resistance training versus hours to 24 hours after sub-threshold aerobic work.

### Application rule

- ANCHOR hypertrophy programs around **high-SFR exercises** (machines, cables, chest-supported variations) for volume accumulation.
- RESERVE low-SFR compounds (barbell squat, deadlift, bent-over row) for strength blocks where total-body loading is the goal.
- WITHIN each session → order exercises from highest to lowest neural demand.
- TRACK fatigue via composite score: RPE creep at matched loads, session wellness ratings (sleep, motivation, joint pain on 1–5 scales), and HRV.
- TRIGGER fatigue interventions when ≥2 markers deteriorate simultaneously for 2+ consecutive weeks.
- FOR intentional functional overreaching blocks (1–2 weeks at ~150% normal volume) → ensure immediate deload follows; monitor closely for NFOR warning signs.
- AFTER heavy resistance training → expect HRV suppression 24–72 hours; do NOT flag unless suppression persists beyond 72 hours.
- SWAP or downgrade low-SFR exercises when chronic fatigue markers accumulate.
- AVOID stacking multiple very high-stress days; position heaviest/most fatiguing sessions after rest or low-stress days.

### Key sources

- Meeusen R et al. "Prevention, diagnosis, and treatment of the overtraining syndrome: joint consensus statement of ECSS and ACSM." *Medicine & Science in Sports & Exercise*, 2013; 45(1): 186–205.
- Bell L et al. "Overreaching and overtraining in strength sports and resistance training: a scoping review." *Journal of Sports Sciences*, 2020; 38(16): 1897+.
- Halson SL, Jeukendrup AE. "Does overtraining exist? An analysis of overreaching and overtraining research." *Sports Medicine*, 2004; 34: 967–981.
- Thomas K et al. "Neuromuscular fatigue and recovery after heavy resistance, jump, and sprint training." *Medicine & Science in Sports & Exercise*, 2018.
- Wan JJ et al. "Central and peripheral fatigue during resistance exercise — a critical review." *Journal of Exercise Science & Fitness*. PMC4723165.
- Israetel M, Hoffmann J, Smith CW. *Scientific Principles of Hypertrophy Training*. Renaissance Periodization.
- Le Meur Y et al. "Functional overreaching: the key to peak performance during the taper?" *Med Sci Sports Exerc*, 2014.

### Cross-references

- → Strength §1.7 (exercise selection hierarchies based on SFR)
- → Recovery §1 (HRV as fatigue detection tool)
- → Periodization §5 (three-tier autoregulation framework)
- → Integration Rule #19 (SFR drives exercise selection by phase)

-----

## 1.7 Exercise selection for compound lifts

### Core principle

Compound lift selection should be driven by the intersection of **training goal** (hypertrophy vs. strength), **stimulus-to-fatigue ratio**, and **individual biomechanics/injury history**. For hypertrophy, high-SFR variations that maximally load the target muscle with minimal systemic fatigue are preferable. For strength, specificity to the competition or target movement pattern takes priority. Every movement pattern should include primary, secondary, and tertiary exercise selections, with primaries carrying the bulk of volume and progression.

### Evidence summary by movement pattern

**Squat variations:**
- Front squats produce the **highest rectus femoris and vastus medialis activation** of barbell squat variations (Yavuz et al. 2015, ES = 0.62 for VM; Coratella et al. 2021, 24% greater RF, ES = 1.21) while generating less knee compressive force than back squats (Gullett et al. 2009).
- Low bar back squats produce the highest glute and hamstring activation due to greater hip moment.
- Bulgarian split squats at 50% RM match back squat glute/quad EMG at 85% RM (DeForest et al. 2014) with far less spinal loading.
- Hack squats and leg presses show the **highest SFR** — maximal quad overload with minimal spinal fatigue.

**Deadlift variations:**
- Conventional deadlifts produce the highest overall posterior chain activation but have the **lowest SFR** due to massive systemic fatigue.
- Sumo deadlifts show 8% reduced spinal shear (Cholewicki et al. 1991) with greater quad involvement (Escamilla et al. 2002: VL 48% vs. 40% MVIC).
- Trap bar deadlifts allow **5–10% heavier loads** with higher quad activation and reduced spinal flexion moment (Swinton et al. 2011: hip:knee moment ratio 1.78:1 vs. 3.68:1 for conventional).
- Romanian deadlifts provide **constant hamstring tension** at submaximal loads — the best SFR for hamstring hypertrophy.

**Bench press variations:**
- The **30° incline** is optimal for upper pec activation (Rodríguez-Ridao et al. 2020; Lauver et al. 2016: 122.5% MVIC at 30° vs. 98.2% at flat). Beyond 45°, anterior deltoid dominates.
- Grip width has **minimal effect** on pec activation (Saeterbakken et al. 2021); close-grip slightly increases triceps contribution.
- Flat bench press maximizes sternal pec activation and total load. Decline offers no advantage over flat.

**Overhead press variations:**
- Standing dumbbell press produces the **highest overall deltoid EMG** — 15% greater anterior delt than standing barbell (Saeterbakken & Fimland 2013, p < 0.001), 15% greater medial delt (p = 0.008 vs. seated) — but allows 7–10% lower 1RM than barbell.
- Standing barbell press produces **39% greater triceps activation** than standing dumbbell (p < 0.001).
- Behind-neck press uniquely targets medial and posterior deltoid (Coratella et al. 2022, ES: 4.56 medial, 8.65 posterior).

**Row variations:**
- Chest-supported rows produce **greater latissimus dorsi and rhomboid activation** than free-standing bent-over rows (Fry et al. 2003) while eliminating erector spinae fatigue — the highest SFR in the category.
- Bent-over barbell rows produce the **highest overall erector spinae activation** but have the worst SFR.
- Elbow path determines target emphasis: elbows tight = lats; elbows flared = rear delts/rhomboids.
- Grip type has minimal effect on lat activation specifically (Lehman 2004; Retos 2024).

**Exercise hierarchies:**

**For hypertrophy (prioritize SFR):**

| Pattern | Primary | Secondary | Tertiary |
|---|---|---|---|
| Squat | Hack squat / Leg press | Front squat / High bar back squat | Bulgarian split squat |
| Hinge | Romanian deadlift | Trap bar deadlift | Conventional deadlift |
| Horizontal press | 30° incline DB press | Flat barbell bench | Close-grip bench / Dips |
| Vertical press | Seated DB press | Standing DB press | Machine shoulder press |
| Horizontal pull | Chest-supported row | Seated cable row | One-arm DB row |

**For strength (prioritize specificity and loading):**

| Pattern | Primary | Secondary | Tertiary |
|---|---|---|---|
| Squat | Low bar back squat | High bar back squat | Front squat |
| Hinge | Conventional deadlift | Sumo deadlift | Trap bar deadlift |
| Horizontal press | Flat barbell bench | Close-grip bench | 30° incline barbell |
| Vertical press | Standing barbell OHP | Seated barbell OHP | Push press |
| Horizontal pull | Bent-over barbell row | Pendlay row | Chest-supported row |

### Application rule

- DURING hypertrophy blocks (high volume, moderate intensity) → bias toward high-SFR variations.
- DURING strength blocks (lower volume, high intensity) → shift to competition-style lifts for specificity.
- WHEN programming deadlift and row in the same session/week → pair **chest-supported rows with conventional deadlifts** to avoid cumulative spinal fatigue.
- ROTATE exercise variations every 1–2 mesocycles for connective tissue management and overuse prevention.
- FOR injury history → substitute lower-stress alternatives:
  - Knee concerns → front squat or leg press instead of back squat
  - Lower back concerns → trap bar or sumo deadlift instead of conventional
  - Shoulder concerns → dumbbell bench instead of barbell
- ANCHOR each main lift to 1–2 primary variants; add 1–3 secondary movements per session.
- REPLACE exercises that repeatedly produce pain, poor technique, or disproportionate fatigue with higher-SFR alternatives.

### Key sources

- Yavuz HU et al. "Kinematic and EMG activities during front and back squat variations." *Journal of Sports Sciences*, 2015.
- Gullett JC et al. "A biomechanical comparison of back and front squats." *JSCR*, 2009.
- Coratella G et al. "An electromyographic analysis of front, full, and parallel back squat variations." *IJERPH*, 2021.
- Escamilla RF et al. "An electromyographic analysis of sumo and conventional style deadlifts." *Medicine & Science in Sports & Exercise*, 2002.
- Swinton PA et al. "A biomechanical analysis of straight and hexagonal barbell deadlifts." *JSCR*, 2011.
- Lauver JD, Cayot TE, Scheuermann BW. "Influence of bench angle on upper extremity muscular activation." *European Journal of Sport Science*, 2016.
- Rodríguez-Ridao D et al. "Effect of five bench inclinations on EMG activity." *IJERPH*, 2020.
- Saeterbakken AH, Fimland MS. "Effects of body position and loading modality on muscle activity in shoulder presses." *JSCR*, 2013.
- Contreras B et al. "A comparison of gluteus maximus, biceps femoris, and vastus lateralis EMG activity in the back squat and barbell hip thrust." *Journal of Applied Biomechanics*, 2016.
- Fry AC et al. Row EMG study, 2003.

### Cross-references

- → Strength §1.6 (SFR classification drives selection)
- → Periodization §2 (phase determines hypertrophy vs. strength hierarchy)
- → Concurrent Training §3 (pairing chest-supported rows with deadlifts for concurrent athletes)



-----

# DOMAIN 2: ENDURANCE TRAINING FOR MOUNTAIN SPORTS

## 2.1 Polarized training model

### 2.1.1 The 80/20 intensity distribution

#### Core principle

The polarized model distributes training as ~75–80% below the first ventilatory threshold (VT1, blood lactate <2 mmol/L), ~0–5% between VT1 and VT2, and ~15–20% above VT2 (>4 mmol/L lactate). The critical insight from Stephen Seiler's work is that elite endurance athletes across sports converge on this pattern and spend remarkably little time at moderate/"threshold" intensity. The 80/20 ratio was originally described by **session count** (80% of sessions are easy); measured by time-in-zone, the split is closer to **90/5/5** because high-intensity intervals occupy only minutes within a session.

#### Evidence summary

- **Stöggl & Sperlich (2014):** 48 well-trained endurance athletes (VO2peak 62.6 ± 7.1 ml/kg/min), 9-week RCT comparing polarized (POL), threshold (THR), high-volume (HVT), and HIIT groups. POL produced **+11.7% VO2peak, +17.4% time to exhaustion, +8.1% power at 4 mmol/L lactate, +5.1% peak power**. THR and HVT showed no significant improvements. Note: this impressive single-RCT result has not been replicated at the same magnitude in subsequent meta-analyses.
- **Neal et al. (2013):** 12 trained cyclists, 6-week crossover. POL outperformed THR on peak power (+8% vs +3%), lactate threshold power (+9% vs +2%), and high-intensity capacity (+85% vs +37%) — despite lower total training volume.
- **Muñoz, Seiler et al. (2014):** 30 recreational runners, 10 weeks. POL improved 10K time by 5.0% vs THR 3.6%. Sub-analysis of most adherent athletes: POL **+7.0%** vs THR **+1.6%** (Cohen's d = 1.29, p = 0.038).
- **Rosenblat et al. (2019) meta-analysis:** Moderate effect favoring POL over THR for time-trial performance (ES = −0.66).
- **Rosenblat, Seiler et al. (2025) IPD network meta-analysis (13 studies, 348 athletes):** **No difference between POL and pyramidal (PYR) for VO2max or time-trial in recreational athletes.** Competitive athletes may benefit more from POL. This is the most recent and methodologically strongest evidence.
- **Silva Oliveira et al. (2024) meta-analysis:** POL superior to other distributions for VO2peak with small effect size (SMD = 0.46, p = 0.01) but only for highly trained/national-level athletes and interventions <12 weeks.
- **A 2025 study of 120 recreational marathon runners:** POL produced 11.3 ± 3.2 min improvement vs PYR's 8.7 ± 2.8 min, but individual response clustering showed only 31.5% were "polarized responders" — 31.9% responded better to pyramidal training.
- **Seiler's hierarchy:** Total training volume is the single most important factor, followed by intensity distribution, then periodization details.

#### Application rule

- DEFAULT to polarized distribution: ~80% of sessions below VT1, ~20% genuinely hard (above VT2).
- THE MOST IMPORTANT RULE → avoid the gray zone. Do not let easy sessions drift into moderate intensity.
- FOR recreational mountain athletes → both POL and PYR produce equivalent outcomes; do not be dogmatic about the exact split.
- KEY PRINCIPLES: (1) keep easy truly easy, (2) make hard sessions genuinely hard, (3) accumulate sufficient volume, (4) limit threshold-zone work to ≤5% of total time.
- IF weekly volume < 5 hours → ensure at least 1 dedicated high-intensity session.
- IF weekly volume < 3 hours → a single weekly interval session may suffice for the high-intensity component.
- IF average HR for any session falls in 78–88% HRmax range → flag as potential gray-zone violation.
- Two high-intensity sessions per week typically suffice for recreational athletes.

#### Key sources

- Seiler S. "What is best practice for training intensity and duration distribution in endurance athletes?" *Int J Sports Physiol Perform*, 2010; 5(3): 276–291.
- Stöggl T, Sperlich B. "Polarized training has greater impact on key endurance variables." *Frontiers in Physiology*, 2014; 5:33. DOI: 10.3389/fphys.2014.00033.
- Neal CM et al. "Six weeks of a polarized training-intensity distribution leads to greater physiological and performance adaptations." *J Appl Physiol*, 2013; 114(4): 461–471.
- Muñoz I, Seiler S et al. "Does polarized training improve performance in recreational runners?" *Int J Sports Physiol Perform*, 2014; 9(2): 265–272.
- Rosenblat MA, Seiler S et al. "Which training intensity distribution will produce the greatest improvements in VO2max and TT performance?" *Sports Medicine*, 2025; 55(3): 655–673. DOI: 10.1007/s40279-024-02149-3.
- Silva Oliveira AL et al. meta-analysis on polarized training, 2024.

### 2.1.2 Application to recreational mountain athletes

#### Core principle

For non-competitive mountain athletes training 5–10 hours per week, the specific ratio of polarized vs pyramidal matters less than three fundamentals: keeping most training below VT1, making hard sessions genuinely hard, and accumulating sufficient total volume. Mountain sports are naturally suited to polarized training because long days of ski touring or hiking at conversational pace perfectly match Zone 1 prescription.

#### Evidence summary

- The 2025 IPD meta-analysis (Rosenblat and Seiler) found no performance difference between POL and PYR for recreational athletes (SMD = −0.06 for VO2max, p = 0.68; SMD = −0.05 for time-trial, p = 0.34).
- Uphill Athlete (Steve House, Scott Johnston, *Training for the New Alpinism*) recommends 80–95% aerobic base training for mountain athletes, with initial 8–12 weeks of zero high-intensity work. Broadly consistent with polarized philosophy.

#### Application rule

- FOR new users or those returning from a break → prescribe 8–12 weeks of pure aerobic base training (all sessions below VT1) before introducing high-intensity intervals.
- AFTER base phase → add 1–2 weekly high-intensity sessions: hill intervals of 3–5 × 4–8 minutes at >90% HRmax, or steep uphill repeats with loaded pack.
- FLAG the classic recreational error: every mountain session becomes moderate-hard at 80–85% HRmax.
- In base periods → skew to 85–90% low intensity with minimal high intensity.

### 2.1.3 Translating polarized training to mountain touring

#### Core principle

In mountain sports, the sport itself is the base training — a long ski tour at comfortable pace is Zone 1 work. The challenge is preventing steep terrain, altitude, pack weight, and competitive instinct from pushing every session above VT1. Dedicated high-intensity sessions should be sport-specific: steep skinning intervals, loaded uphill repeats, or VO2max hill efforts.

#### Evidence summary

- Elite ski mountaineers: VO2max is the strongest performance predictor (Lasshofer et al., 2021: elite 71.2 ± 6.8 ml/kg/min vs sub-elite 62.5 ± 4.7 ml/kg/min, p = 0.003).
- Schenk et al. (2011): Experienced ski mountaineers (VO2max 68.2 ± 6.1) had VT1 at 70.5% VO2max and VT2 at 90.9% VO2max. Competition was sustained near VT2.
- Norwegian Olympic coaching: 85–95% aerobic training volume with 2–3 high-intensity sessions per week for cross-country skiers.

#### Application rule

- CLASSIFY mountain sessions by HR data:
  - IF average HR for uphill portion < 77% HRmax → Zone 1.
  - IF 77–88% → flag as potential gray zone; advise slower pace on subsequent easy tours.
- FOR high-intensity mountain sessions → prescribe sport-specific intervals: 4 × 4 min at 90–95% HRmax on steep terrain (>15% grade) with descent recovery.
- "Muscular endurance" sessions (heavy pack, steep terrain, near-threshold intensity) → count as Zone 3 time.


-----

## 2.2 Zone-based training

### 2.2.1 Three-zone and five-zone models

#### Core principle

The 3-zone model (Seiler) anchors to two physiological thresholds: Zone 1 below VT1/LT1 (<2 mmol/L lactate), Zone 2 between VT1 and VT2 (2–4 mmol/L), Zone 3 above VT2/LT2 (>4 mmol/L). The 5-zone model subdivides further for more granular prescription. Both are physiologically valid; the 3-zone model is simpler and aligns directly with polarized philosophy.

#### Evidence summary

| Zone (3-zone) | Zone (5-zone) | %HRmax | %HRR | Blood Lactate | RPE (Borg 6–20) |
|---|---|---|---|---|---|
| Zone 1 | Zones 1–2 | <77–82% | <60–75% | <2.0 mmol/L | 6–12 |
| Zone 2 | Zones 3–4 | 82–88% | 75–88% | 2.0–4.0 mmol/L | 12–16 |
| Zone 3 | Zone 5 | >88–92% | >88% | >4.0 mmol/L | 16–20 |

- Individual variability is substantial: a 2025 study found CVs of **6–29%** across different Zone 2 markers, with fixed %HRmax ranges poorly representing individual metabolic responses.
- The 5-zone Norwegian model: Z1 (60–72% HRmax, recovery), Z2 (72–82%, moderate aerobic), Z3 (82–87%, tempo), Z4 (88–92%, threshold), Z5 (93–100%, VO2max).

#### Application rule

- USE the **3-zone model** as primary framework for session classification and polarized distribution tracking.
- USE the 5-zone model for prescribing specific workout intensities (e.g., "Z4 intervals" for threshold work).
- COMMUNICATE to user in simple terms: Zone 1 = "conversational," Zone 2 = "comfortably hard," Zone 3 = "race effort or harder."
- SET initial zone boundaries from %HRmax (Tanaka formula), then refine with field test data when available.

### 2.2.2 Setting zones without power meters

#### Core principle

For mountain sports without power meters, heart rate reserve (%HRR via Karvonen method) is more accurate than %HRmax for prescribing intensity because %HRR maps to %VO2 reserve (r = 0.990, Swain et al.). The Tanaka formula (208 − 0.7 × age) provides a better HRmax estimate than the Fox formula (220 − age), particularly for athletes over 40, but all formulas have a standard error of **~10 bpm**.

#### Evidence summary

- Karvonen formula: THR = HRrest + (HRmax − HRrest) × %intensity. Swain and Leutholtz (1997): %HRR ≈ %VO2R (slope 1.00 ± 0.01, intercept −0.1 ± 0.6) but NOT %VO2max.
- Tanaka et al. (2001) meta-analysis (351 studies, 18,712 subjects): HRmax = 208 − 0.7 × age, SEE ~10 bpm. No gender or activity-level differences.
- Fox formula (220 − age): SEE of ~12 bpm. Overestimates HRmax in young adults by ~7 bpm, underestimates in older adults.
- HERITAGE Family Study (762 subjects): Fox SEE = 12.4 bpm, Tanaka SEE = 11.4 bpm.
- **Field test recommendation:** 3 × 3-min all-out hill repeats; peak HR on final repeat provides a practical HRmax estimate far more accurate than any formula.

#### Application rule

- ON FIRST USE → set zones using Tanaka formula (208 − 0.7 × age) and resting HR via Karvonen.
- FLAG that formula-based zones are approximations (±10 bpm error cascades into zone error).
- PROMPT user to complete a field test within first 2 weeks: steep hill repeats protocol (warm up 15 min, then 3 × 3-min maximal efforts on steep terrain with 3-min jog recovery, record peak HR on third effort).
- IF user provides lab-tested LTHR → use as primary anchor and derive all zones from LTHR.

### 2.2.3 RPE mapping to HR zones

#### Core principle

Rating of perceived exertion correlates with heart rate (r = 0.74) and more strongly with blood lactate (r = 0.83), making RPE a reliable complementary tool when HR data is unreliable — during variable mountain terrain, extreme cold, or at altitude. RPE is independent of age, gender, and fitness level for identifying metabolic thresholds.

#### Evidence summary

- Scherr et al. (2013), n = 2,560: RPE at LT1 = **10.8 ± 1.8** (Borg 6–20); RPE at LT2 = **13.6 ± 1.8**; RPE at 4 mmol/L lactate = **14.1 ± 2.0**.
- Seiler and Kjerland (2006): Session RPE distribution matched HR-based distribution within 1–3%.

| Zone (3-zone) | Borg RPE (6–20) | Borg CR-10 | Simple Cue |
|---|---|---|---|
| Zone 1 (<VT1) | 6–12 | 0–3 | "Can talk easily" |
| Zone 2 (VT1–VT2) | 12–16 | 4–6 | "Can speak in short phrases" |
| Zone 3 (>VT2) | 16–20 | 7–10 | "Can only say a few words" |

#### Application rule

- COLLECT session RPE (1–10 scale / Borg CR-10) after every session.
- USE RPE as cross-check against HR data.
- WHEN HR data is suspect (altitude, cold, variable terrain) → weight RPE more heavily for session classification.
- IF session RPE ≤3 (CR-10) AND HR shows Zone 2 → HR likely inflated by cardiac drift/altitude/heat; classify as Zone 1.
- IF RPE ≥7 AND HR shows Zone 1–2 → suspect optical sensor error.

### 2.2.4 Cardiac drift during long uphill efforts

#### Core principle

During sustained exercise, heart rate drifts upward at constant workload due to rising core temperature, plasma volume loss, and reduced stroke volume. During multi-hour mountain days, cardiac drift is unavoidable and can shift HR by a full training zone, making raw HR data unreliable for zone classification in the second half of long efforts.

#### Evidence summary

- Typical magnitude: **10–20 bpm over 30–60 minutes** of sustained moderate exercise. Rate: approximately **3–5 bpm per 30 minutes** in temperate conditions, accelerating with heat and dehydration.
- A drift of up to **15% of initial HR** documented (e.g., 117 → 135 bpm = one full zone shift).
- Onset: typically after ~10–12 minutes of continuous exercise (Colakoglu et al., 2018).
- Uphill Athlete aerobic drift test: <3.5% HR drift over 60 min = below aerobic threshold; **3.5–5% = aerobic threshold**; >5% = above aerobic threshold.

#### Application rule

- BASE zone classification on **first-hour HR data** for long mountain sessions.
- FOR sessions >2 hours → accept 5–10 bpm drift as normal; do not reclassify unless RPE also increases.
- IMPLEMENT drift-adjusted zone calculation: for every hour beyond the first, subtract 3–5 bpm from recorded HR before zone classification.
- WHEN prescribing long easy sessions → tell user to target lower end of Zone 1 HR at start, allowing room for drift.

### 2.2.5 Altitude effects on HR zones

#### Core principle

Altitude compresses the usable heart rate range: resting HR rises while HRmax may decrease, narrowing the gap between easy and maximal effort. At moderate altitude (1,500–3,000 m), VO2max declines **6–7% per 1,000 m**, meaning the same absolute workload represents a higher percentage of maximum capacity.

#### Evidence summary

- VO2max decline: **6.3% per 1,000 m** (Wehrlin and Hallén, 2006; 8 endurance athletes, 300–2,800 m). At 3,000 m: ~19–20% reduction for fit athletes.
- Fulco et al. meta-analysis (146 studies): Well-conditioned athletes (VO2max >63 ml/kg/min) lose ~7% per 1,000 m; less-conditioned lose ~4–5% per 1,000 m.
- Resting HR increases **4–5 bpm at 1,500–2,000 m**, scaling to **20–30 bpm above 3,000 m**.
- HRmax may decrease **~5 bpm at moderate altitude** (Lundby, 2012), debated below 2,500 m.
- Submaximal HR rises for the same absolute workload.
- Acclimatization recovers **29–36% of the initial VO2max deficit** over 2 weeks (Wehrlin et al.).
- Li et al. (2025, *Life*) meta-analysis: altitude training significantly increased hemoglobin and hemoglobin mass but had **no significant effect on VO2max**. "Live high, train high" for >3 weeks showed the strongest hematological response.

#### Application rule

- WHEN GPS data shows elevation > 1,500 m → apply altitude adjustment:
  - **Adjusted zone boundary = Standard boundary − (altitude_above_1500m / 1000 × 5 bpm)**
  - Example: standard Zone 1 ceiling of 145 bpm, at 2,500 m → adjusted ceiling = 140 bpm.
- IF user trains regularly at altitude (≥2×/week at 2,000–3,000 m) → track average weekly altitude exposure; progressively reduce correction factor over 2–3 weeks of consistent exposure.
- ON first exposure to new altitude → increase prescribed recovery time by 20–30%.
- ALWAYS cross-reference with RPE. When RPE and HR disagree at altitude, trust RPE.
- NEVER prescribe VO2max intervals above 2,500 m unless user has ≥2 weeks of consistent exposure at that altitude.
- REDUCE planned training volume (especially high-intensity) by 20–30% for first 5–7 days at new altitude.

#### Cross-references

- → Recovery §4 (altitude nutrition: increased carbohydrate, fluid, iron demands)
- → Biomarkers §1A (ferritin gates altitude training readiness)
- → Integration Rule #5 (altitude compresses HR zones)


-----

## 2.3 Vertical-specific conditioning

### 2.3.1 Oxygen cost at incline

#### Core principle

The metabolic cost of uphill walking increases nonlinearly with gradient, reaching nearly **5× flat-ground cost at 20% grade** and **~9× at 40% grade**. For recreational athletes, walking at moderate speeds on steep terrain (>15% grade) can approach or exceed VO2max, making gradient the single most powerful variable for manipulating exercise intensity in mountain training.

#### Evidence summary (Minetti et al., 2002 — the definitive study, 10 elite mountain runners)

| Grade | Walking Cost (J/kg/m) | Multiple of Flat |
|---|---|---|
| 0% (flat) | 1.64 | 1.0× |
| +10% | 4.68 | 2.9× |
| +15% | ~6.4 | ~3.9× |
| +20% | 8.07 | 4.9× |
| +25% | ~9.7 | ~5.9× |
| +30% | 11.29 | 6.9× |
| +45% | 17.33 | 10.6× |

- ACSM metabolic equation for walking: VO2 (ml/kg/min) = 0.1 × speed(m/min) + 1.8 × speed × fractional grade + 3.5.
- At 5 km/h on 15% grade: ~34 ml/kg/min (~9.7 METs). At 20% grade: ~41 ml/kg/min (~11.8 METs).
- For a recreational athlete with VO2max of 45 ml/kg/min, **walking at 5 km/h on a 20% grade demands ~91% of VO2max** — essentially maximal effort.
- Mechanical efficiency above 15% grade stabilizes at ~0.243 (walking), matching pure concentric contraction efficiency (~25%).
- Optimal path gradient for minimizing energy cost per vertical meter: **20–30%** (Minetti, 1995).
- Equivalence: **100 m vertical gain ≈ 1.0–1.5 km of flat running** in terms of energy cost and training stress.

#### Application rule

- USE the ACSM equation (or Minetti polynomial) to estimate session intensity from GPS speed and grade data.
- WHEN prescribing uphill workouts → use grade as the primary intensity lever:
  - Zone 1 training → 10–15% grades at moderate speed
  - Zone 3 intervals → >20% grades
- FLAG sessions where speed-grade combination demands >85% estimated VO2max as high-intensity, even if user perceives the pace as "slow."

### 2.3.2 Lactate threshold at incline vs flat

#### Core principle

The lactate threshold occurs at a lower absolute speed on an incline but at a **similar relative intensity (%VO2max)**. Incline exercise may elicit a higher true VO2max due to greater muscle mass recruitment.

#### Evidence summary

- Langsetmo et al. (2002): Lactate threshold at 47.9 ± 2.1% VO2max on 10% incline vs 43.9 ± 4.5% VO2max on flat — not significantly different as percentage. Absolute VO2 at LT was higher on incline (37.3 vs 26.9 L/min).
- Padulo et al.: VO2 increases ~18.7% between 0% and 7% incline at same running speed.
- Incline treadmill protocols can produce VO2max values ~10% higher than flat protocols.

#### Application rule

- FOR threshold workouts → steep terrain (10–15% grade) is a low-impact alternative to flat tempo runs.
- SET target as HR-based threshold zone (88–92% HRmax) rather than pace target, since pace will be dramatically slower on inclines.
- PARTICULARLY valuable for athletes with joint issues or returning from injury.

### 2.3.3 Muscular demands of sustained climbing

#### Core principle

Uphill exercise dramatically increases activation of the vastus group (quadriceps) and soleus compared to flat walking, while redistributing work away from the rectus femoris. A model using just soleus and vastus lateralis EMG explains **96% of the variance** in metabolic cost of incline walking.

#### Evidence summary (Sloniger et al., 1997 — MRI study, uphill vs horizontal running at 10% grade)

| Muscle | Flat Activation | Uphill Activation | Change |
|---|---|---|---|
| Vastus group | 53% | **75%** | **+22 percentage points** |
| Soleus | 41% | **55%** | **+14 pp** |
| Gluteals | 71% | **79%** | +8 pp |
| Gastrocnemius | 71% | **76%** | +5 pp |

- Total lower extremity muscle volume activated: 67% flat vs **73% uphill** (p < 0.05).
- Franz and Kram (2012): Hip, knee, and ankle extensor EMG all progressively increase with steeper grades.
- Quadriceps activation increases ~40% at 10° incline vs flat.

#### Application rule

- PRESCRIBE targeted strength work for primary uphill muscles:
  - (1) Single-leg squats and step-ups for vastus group and gluteals
  - (2) Single-leg calf raises (eccentric emphasis) for soleus and gastrocnemius
  - (3) Weighted lunges for integrated uphill gait pattern
- DURING base phases → 2–3 strength sessions/week targeting these muscle groups.
- DURING peak season → reduce to 1–2 sessions for maintenance.
- ALWAYS include hip flexor mobility work (tightened iliopsoas from prolonged uphill effort is common).

### 2.3.4 Load carriage physiology

#### Core principle

Carrying a 10–15 kg pack increases metabolic cost by approximately **15–25%** compared to unloaded walking. The relationship is **nonlinear** — heavier loads incur disproportionately greater costs. Military research provides the strongest evidence base.

#### Evidence summary

- Pandolf equation: M = 1.5W + 2.0(W+L)(L/W)² + η(W+L)[1.5V² + 0.35VG], where W = body mass, L = load, V = speed, G = grade, η = terrain factor.
- A 15 kg pack on 75 kg person (20% body mass) increases energy expenditure by ~20–25% at any given speed and grade.
- Military: sustain ≤**45–47% VO2max** during prolonged loaded marches to delay fatigue.
- Pandolf equation under-predicts by **12–33%** for contemporary loads (Drain et al., 2017).
- 75 kg person hiking at 4.5 km/h on 15% grade: unloaded ~550–600 kcal/hr; with 15 kg pack ~700–750 kcal/hr.
- Walking with 20 kg backpack increases VO2 by **~4.45 ml/kg/min** vs unloaded (MDPI 2025, special forces).

#### Application rule

- WHEN user reports carrying >8 kg → apply metabolic adjustment: multiply estimated energy expenditure by **(1 + 0.015 × load_kg)**.
- FOR training progression → introduce pack weight gradually: start at 10% body weight, increase by ~1–2 kg/week until target carry weight.
- NEVER increase pack weight and session duration simultaneously — change one variable at a time.
- CLASSIFY hikes with >600–800 m vertical AND >10 kg pack as high-stress sessions.

### 2.3.5 Progressive overload of vertical gain

#### Core principle

Vertical gain should be tracked as an independent load metric alongside duration and HR-based intensity. Safe progression follows general endurance volume principles, but the high muscular demands of uphill work warrant more conservative progression than flat terrain training.

#### Evidence summary

- From Minetti's data: 100 m vertical gain costs approximately **4.9× the energy** of 500 m flat walking at 20% grade.
- Elite ski mountaineers regularly train 4,000–8,000 m vertical per week.
- Suggested progression: Beginner 400–1,200 m/week → Building 1,000–2,000 m/week → Peak 2,000–4,000 m/week for serious recreational athletes.

#### Application rule

- TRACK weekly vertical meters as a primary volume metric.
- APPLY ACWR to vertical gain: keep weekly vertical within **0.8–1.3× the 4-week rolling average**.
- WHEN increasing both duration and vertical simultaneously → limit each to 5% increase.
- DELOAD weeks → reduce vertical by 40–60%.
- FLAG any week where vertical exceeds 1.5× the 4-week average as a spike risk.

#### Cross-references

- → Endurance §6 (10% rule, ACWR details)
- → Integration Rule #17 (vertical gain as independent ACWR metric)

-----

## 2.4 Altitude considerations

### 2.4.1 Training at 1,500–3,000 m elevation

#### Core principle

VO2max declines approximately **6–7% per 1,000 m** above sea level for well-conditioned athletes, meaning a summit day at 3,000 m costs roughly 15–20% of aerobic capacity compared to valley level. The performance impact on time to exhaustion is even steeper, declining **~14.5% per 1,000 m**.

#### Evidence summary

- Wehrlin and Hallén (2006): VO2max declined linearly from 66 ± 1.6 to 55 ± 1.6 ml/kg/min between 300 m and 2,800 m, yielding **6.3% per 1,000 m** (range 4.6–7.5%).
- Fulco et al. meta-analysis (146 studies): Well-conditioned athletes (VO2max >63) lose ~7% per 1,000 m; less-conditioned ~4–5%.
- Schuler et al. (2007): 8 elite cyclists at 2,340 m — Day 1 VO2max declined **12.8%** and time to exhaustion **25.8%**. Recovery rate: ~4% VO2max per week, ~6% TTE per week.
- Pühringer et al. (2022): Acclimatized Austrian mountain guides with lower baseline VO2max showed better preservation at altitude.
- Li et al. (2025, *Life*) meta-analysis: altitude training significantly increased hemoglobin and hemoglobin mass but had **no significant effect on VO2max**, with "live high, train high" for >3 weeks showing the strongest hematological response.

#### Application rule

- FOR Innsbruck-based user (valley ~570 m) training at 1,500–3,000 m:
  - At 2,000 m → VO2max reduced ~9–10% acutely
  - At 3,000 m → ~15–17%
- DURING first 2–3 exposures to new altitude tier → prescribe only Zone 1 work.
- IF user consistently trains above 2,000 m (≥2×/week for ≥2 weeks) → track acclimatization status; progressively relax altitude adjustments.

### 2.4.2 Acclimatization patterns and timelines

#### Core principle

Acclimatization follows a predictable timeline: acute performance loss (days 1–3), early responses (days 3–7), substantial aerobic recovery (days 7–14), and near-complete adaptation (days 14–21+). Full hematological adaptation requires approximately **11.4 days per 1,000 m** of altitude.

#### Evidence summary

- **Days 1–3:** Immediate VO2max decline, resting HR increase (+4–5 bpm), hyperventilation, sleep disturbances (doubled), HRV suppression, AMS symptoms may appear at 12–24 hours.
- **Days 3–7:** Ventilatory acclimatization begins, EPO release starts (requires ≥1,800 m), HRV begins normalizing (~day 5–8), sleep improving. Six days at 2,200 m substantially decreases AMS and improves work performance (Fulco et al.).
- **Days 7–14:** Red blood cell production increasing, VO2max recovery at ~4% per week, resting HR returning toward baseline.
- **Days 14–21+:** Recovery of **29–36% of initial VO2max deficit** (Wehrlin et al.). Full hematological adaptation to 3,000 m: ~34 days (Zubieta-Calleja, 2007).
- WHOOP case study: After 6 weeks at altitude (1,655 m), resting HR fell below baseline and HRV exceeded baseline.

#### Application rule

- FOR Innsbruck users doing day trips to 2,000–3,000 m → each trip = acute exposure without overnight acclimatization. Do not expect meaningful acclimatization from day trips alone.
- HOWEVER → frequent exposure (3+ times/week) provides cumulative benefit.
- FOR multi-day mountain trips → prescribe first day as easy (Zone 1 only), allow normal training from day 3+.
- TRACK user's altitude exposure history (total hours above 2,000 m per week) to modulate HR adjustments.

### 2.4.3 Recovery at altitude

#### Core principle

Altitude impairs recovery through disrupted sleep architecture, sympathetic activation, reduced oxygen delivery, and dehydration. Recovery times should be extended by 20–30% for sessions above 2,000 m.

#### Evidence summary

- Sleep at 1,800 m: total sleep time decreased 9 min, light sleep decreased 12 min, slow-wave sleep increased 7.8 min, respiratory rate increased (Sleep Health Journal, 33 elite athletes).
- Periodic breathing (hyperventilation/apnea cycles) begins at >2,000 m during sleep.
- HRV: acute suppression of RMSSD and HF power; LF/HF ratio increases (sympathetic predominance).
- Hydration needs: ≥3–4 liters/day at altitude.
- High-carbohydrate diet (>70% calories from CHO) recommended for altitude performance.
- The AI should assume a **20–30% reduction in effective sleep quality** for any night above 2,500 m.

#### Application rule

- AFTER sessions above 2,000 m → prescribe 20–30% more recovery time than equivalent valley sessions.
- IF HRV (RMSSD) drops >15% below 7-day average on morning after altitude session → prescribe Zone 1 or rest next day.
- DURING frequent altitude exposure → increase easy day prescriptions by one per week.
- REMIND users to increase fluid and carbohydrate intake on altitude days.

#### Cross-references

- → Recovery §2 (sleep at altitude disruption data)
- → Recovery §4 (altitude nutrition: +200–600 kcal/day, 3–5 L fluid, iron requirements)
- → Biomarkers §1A (ferritin ≥40 ng/mL pre-altitude)
- → Integration Rules #5, #11


-----

## 2.5 Sport-specific demands

### 2.5a Splitboarding and ski touring

#### Core principle

Ski touring is one of the most demanding endurance sports, requiring sustained sub-threshold uphill effort for 2–4+ hours while carrying equipment in cold conditions at altitude. The primary performance determinant is **VO2max**, followed by economy and velocity at VT2.

#### Evidence summary

- Elite SKIMO athletes: VO2max **71.2 ± 6.8 ml/kg/min** (Lasshofer et al., 2021). Sub-elite: **62.5 ± 4.7 ml/kg/min**.
- Mean HR during SKIMO racing: **92–93% HRmax** (Duc et al., 2011; Gaston et al., 2019; Lasshofer et al., 2021).
- Race intensity distribution: 7% Zone 1, 51% Zone 2, 42% Zone 3 (Duc et al., 2011).
- Energy expenditure: Recreational touring ~**400–700 kcal/hour**; racing up to **1,000+ kcal/hour**.
- Per 1,000 m vertical: approximately **500–600 kcal** at moderate pace for 80 kg person with gear.
- Total race energy: 19–23 MJ (4,600–5,400 kcal) for competitive multi-hour races (Praz et al.).
- Vertical climbing rate: Elite ~1,173 m/hr; sub-elite ~985 m/hr (Lasshofer et al., 2021).
- Cold exposure: Even 0.5°C core temperature drop measurably lowers self-paced endurance output. >50% of elite XC skiers experience exercise-induced bronchoconstriction. Optimal performance range: 4–20°C.
- During descents: HR stays ~85% HRmax due to psycho-emotional and physical demands.

#### Application rule

- CLASSIFY ski touring sessions: estimate uphill time from GPS track, classify uphill portions by HR zone, add ~100–200 kcal/hr to flat-equivalent energy estimates for cold/equipment.
- WINTER PERIODIZATION:
  - Base (Oct–Nov): High-volume Z1, 4–5 sessions/wk. 2–3 strength sessions. Hiking with pack. Build to 6–8 hrs/wk.
  - Build (Dec–Jan): Add 1–2 weekly interval sessions (steep skinning repeats, 4 × 4 min at >90% HRmax). Sport-specific touring begins. Reduce strength to 2 sessions.
  - Peak (Feb–Mar): Highest specificity — long tours, race simulations. Maintain 1 interval session. Strength to 1–2 maintenance. Target peak weekly vertical.
  - Maintain (Apr): Reduce volume 20%, maintain intensity. Spring conditions allow longer days.
- COLD MANAGEMENT: advise layering for uphill warmth without overheating; flag rest periods and lift rides as thermoregulatory vulnerability; recommend fueling every 45–60 min during cold sessions.

### 2.5b Hike-and-fly paragliding

#### Core principle

Hike-and-fly combines fast uphill hiking under load (10–15 kg paraglider kit) with time pressure, transforming leisure hiking into Zone 3–4 racing effort. Critical demands: aerobic capacity for fast loaded ascent, core/shoulder endurance for launch and active flying, and ability to control a paraglider safely while physiologically fatigued.

#### Evidence summary

- Paraglider gear weight: standard kits **12–22 kg**; ultralight kits <5 kg.
- Speed hiking with 12–15 kg load at 5–6 km/h uphill: estimated **8–12 METs**, or **600–900+ kcal/hour** depending on gradient and altitude.
- Leisure hiking: Zone 1–2 (60–70% HRmax). Speed hiking / race mode: Zone 3–4 (75–90% HRmax).
- Flying phase: minimal energy (~2–3 METs), isometric core engagement, forearm endurance for brake toggles.
- X-Alps-style events require elite endurance fitness.

#### Application rule

- TREAT hike-and-fly training as loaded-uphill-specific work.
- KEY PRESCRIPTIONS:
  - (1) Build aerobic base with standard Zone 1 hiking.
  - (2) Add loaded speed hikes (10–15 kg, fast pace, 80–85% HRmax) 1–2×/week.
  - (3) Include grip/forearm endurance (dead hangs, farmer's carries) and core stability (planks, anti-rotation).
- FOR race preparation → include "fatigued launch" practice: complete a hard hike then immediately practice wing inflation and ground handling.
- WHEN logging sessions → classify uphill by HR/RPE zone; add flying portion as active recovery (Zone 1 equivalent).

### 2.5c Resort snowboarding

#### Core principle

Resort snowboarding is an **intermittent sport** with short bursts of moderate-to-vigorous effort (downhill runs) separated by forced low-intensity recovery (chair lifts). Structurally similar to HIIT but with unstructured work intervals and passive rest. Primary physical demands are eccentric quadriceps control, hip/knee stability, and sustained isometric force — not VO2max.

#### Evidence summary

- Roberts (2020, master's thesis, Cal State San Marcos, n = 25): Entire session average HR: **64 ± 9% HRmax** (121 ± 19 bpm) over ~6 hours. **During active riding only: 76 ± 10% HRmax (142 ± 20 bpm).** The whole-session average is misleadingly low because it includes lift-line waiting, rest breaks, and transitions — the AI must distinguish between session average and active riding intensity.
- Time in zones: 26% moderate, 21% vigorous. Only **33% of session time is active riding** (Stöggl et al., 2016); 56% low-intensity lift/rest.
- Ainsworth Compendium: Snowboarding = **5.3 METs (moderate)** up to **8.0 METs (vigorous/racing)**.
- Energy expenditure: Active riding ~380–500 kcal/hr; session average including lifts ~**250–350 kcal/hr**.
- Deep powder increases demands by **20–40%** vs packed snow.
- Vernillo (2018, Austrian team): **Isometric quadriceps strength** is a stronger performance predictor than VO2max (r = −0.93 to −0.97). Leg stiffness and force maintenance (r = −0.85 to −0.89). Explosive strength was NOT a strong correlate.
- ~2.5 hours of alpine skiing matches energy expenditure of 1 hour cross-country skiing.

#### Application rule

- CLASSIFY resort snowboarding as **moderate-intensity intermittent activity** for training load calculations.
- LOAD ESTIMATE: multiply active riding time (session × 0.33) by moderate-intensity TRIMP at 76% HRmax; remaining time by recovery TRIMP. A 4-hour resort session ≈ **60–90 minutes of moderate continuous exercise**.
- DO NOT count toward high-intensity training quotas — insufficient and unstructured for targeted cardiovascular stimulus.
- COUNT as active recovery or light aerobic work in weekly plan.
- FOR users who snowboard 3+ days/week → note high eccentric quad loading; prescribe adequate recovery and complementary hamstring/glute work for balance.
- REDUCE or omit separate lower-body strength within next 24 hours after heavy resort days.
- ACKNOWLEDGE that active riding intensity (76% HRmax) is meaningfully higher than session average (64% HRmax) — the eccentric quad demand combined with moderate cardiovascular load makes resort days more taxing than the session-average HR alone suggests.

#### Cross-references

- → Integration Rule #9 (resort snowboarding classification)
- → Concurrent Training §3 (weekly template integration)

-----

## 2.6 Endurance progression

### 2.6.1 The 10% rule: what evidence actually says

#### Core principle

The 10% rule (increase weekly volume by no more than 10%) is a **convention, not an evidence-based threshold**. The only major RCT to test it directly found no difference in injury rates. Actual injury risk is driven more by spikes in single-session load (acute:chronic workload ratio) than by weekly volume progression rate.

#### Evidence summary

- The 10% rule originated from Dr. Joan Ullyot (1980) as advice for novice runners — never derived from controlled research.
- **Buist et al. (2008):** RCT with 532 novice runners. 10% graded group: **20.8% injury rate**; standard group: **20.3%**. No significant difference.
- **Nielsen et al. (2014):** Increasing weekly volume >30% increased injury risk. Increases up to ~24% were no riskier than 10%.
- **Nielsen et al. (2025, BJSM):** 5,200+ runners, 18 months. The 10% rule applied more to **single run distance** than weekly volume.
- **Pollock et al.:** Novice runners in 15, 30, and 45-minute groups showed injury rates of 22%, 24%, and 54%.
- **Jack Daniels "Equilibrium" approach:** Increase by 20–30%, then hold steady for 3–4 weeks.

#### Application rule (tiered progression)

| Training Level | Weekly Volume Increase | Build:Recover Ratio |
|---|---|---|
| Beginner (<6 months) | 10–20%, with equilibrium holds | 2:1 |
| Intermediate (6 mo–3 yr) | 5–15% | 3:1 |
| Advanced (>3 years) | 3–10% | 3:1 or 4:1 |

- THE MORE IMPORTANT CONSTRAINT: prevent spikes. Never allow a single session to exceed 1.5× the average of the previous 4 similar sessions.
- FLAG any week where total load exceeds 1.3× the 4-week rolling average.
- ALLOW up to 15–20% temporary increases for highly conditioned athletes if recovery markers remain solid, but reduce the following week (step-loading).

### 2.6.2 Acute:chronic workload ratio

#### Core principle

The ACWR (acute workload ÷ chronic 4-week average workload) is the most validated framework for managing training load progression. The injury risk "sweet spot" is **ACWR 0.8–1.3**; risk spikes dramatically above 1.5. High chronic workload is protective when paired with moderate ACWR.

#### Evidence summary

- Gabbett (2016): training-injury prevention paradox based on Banister's fitness-fatigue model.
- Hulin, Gabbett et al. (2016): 53 elite rugby players, 2 seasons. Sweet spot: **0.8–1.3** (lowest injury risk). ACWR ≥2.11: **16.7% injury risk** in current week. High chronic + very high ACWR (≥1.54): **28.6% injury risk**. High chronic + moderate ACWR: **RR 0.3–0.7** (protective).
- Maupin et al. (2020), 27 studies: ACWR >2.0 with high-speed running: RR = 4.66 vs moderate ACWR.
- EWMA method is more sensitive than simple rolling average for detecting injury-associated spikes.
- **Limitation:** Most ACWR research is in team sports; direct validation for endurance/mountain athletes is limited. IOC (2016) endorses the approach.
- **Criticism (Wang et al., 2020):** Mathematical coupling problem weakens validity. Use ACWR as heuristic flag, not hard threshold.

#### Application rule

- CALCULATE ACWR weekly for each load metric (duration, vertical gain, TRIMP).
- USE EWMA method for greater sensitivity.
- TARGET ACWR **0.8–1.3** for all metrics.
- IF ACWR exceeds 1.3 for any metric → flag and suggest reducing upcoming week.
- IF ACWR drops below 0.8 (detraining risk) → suggest modest increase.
- PRIORITIZE consistency (high chronic load) over acute spikes.

### 2.6.3 Mountain-specific load monitoring

#### Core principle

Mountain athletes need a composite load metric because no single variable captures full stress. Combine HR-based TRIMP, vertical gain, and session RPE × duration.

#### Evidence summary

- TRIMP (Banister, 1975): Duration × HR intensity × weighting factor. Zone-based TRIMP (Edwards): 5 HR zones with multipliers 1–5.
- Session RPE × duration (Foster method): simplest and most robust for mountain sports. RPE 1–10 × session duration in minutes = session load in arbitrary units.
- Grade-adjusted pace (NGP): NOT validated for complex mountainous terrain.

#### Application rule

- TRACK three load metrics weekly: (1) total session RPE × duration (primary), (2) total vertical gain in meters (secondary), (3) total duration in hours.
- APPLY ACWR to all three.
- WHEN metrics disagree → use the highest ACWR value for risk assessment.
- DISPLAY simple weekly load summary: current vs 4-week average for each metric.

### 2.6.4 Detection and prevention of overtraining

#### Core principle

No single biomarker diagnoses overtraining — it is a diagnosis of exclusion. Most reliable early warnings: increased RPE at given workload, persistent fatigue not resolving with 2–3 days rest, mood disturbances, sleep disruption. HRV-guided training is **superior to pre-planned training** for aerobic performance.

#### Evidence summary

- ECSS/ACSM Joint Consensus (Meeusen et al., 2013): spectrum from acute fatigue → FOR → NFOR → OTS, defined by recovery time.
- Early warning signs (>70% of NFOR/OTS athletes self-report): irritability, loss of motivation, recurrent illness, sleep disruption.
- HRV monitoring: daily morning RMSSD using weekly averages and CV. Both persistent decreases AND paradoxical increases can signal overtraining (Le Meur et al.).
- Kiviniemi et al.: HRV-guided training produced superior aerobic gains vs pre-planned.
- Profile of Mood States (POMS): Reducing training in response to mood disturbances decreased swimmer burnout from 10% to zero.
- Training monotony (mean daily load / SD) exceeding **2.0** is a risk factor: Foster's data showed **89% of illnesses and injuries** preceded by strain spikes in prior 10 days.

#### Application rule

- IMPLEMENT multi-signal fatigue monitoring:
  - (1) Session RPE: flag if RPE increases >1.5 points at same workload over 5+ sessions.
  - (2) Resting HR: flag if >5 bpm above 14-day average for 3+ days.
  - (3) HRV: flag if RMSSD weekly average drops >10% or CV exceeds 10%.
  - (4) Weekly wellness: sleep quality, motivation, muscle soreness on 1–5 scales.
- WHEN 2+ flags trigger simultaneously → override plan; prescribe 3–5 days Zone 1 or complete rest.
- RESUME only when markers return to baseline ranges.

#### Cross-references

- → Recovery §1 (HRV monitoring protocol details)
- → Recovery §3 (subjective readiness marker details)
- → Periodization §5 (three-tier autoregulation framework)

-----

## 2.7 Multi-day touring protocol

### Core principle

Multi-day hut-to-hut traverses (3–5+ consecutive days of ski touring, splitboarding, or hiking) create cumulative fatigue that compounds exponentially, not linearly. 16–20 hours between consecutive touring days is **insufficient for full neuromuscular recovery**, and postural control — critical for fall prevention on technical terrain — deteriorates progressively, peaking around day 3. The AI must provide specific guidance for planning and managing multi-day objectives, including pre-trip preparation, in-trip load management, and post-trip recovery.

### Evidence summary

- **Koller et al. (2018, *Frontiers in Physiology*):** Studied cumulative muscle fatigue across consecutive ski mountaineering days. Significant decreases in both concentric and eccentric quadriceps and hamstring strength that did not fully recover between days. The eccentric strength deficit is particularly concerning because eccentric quad control is the primary mechanism for descent safety.
- **Postural control impairment study:** Four consecutive days of mountain hiking produced progressive postural control deterioration, with impairment peaking on **day 3** — creating direct fall risk on exposed terrain. Balance recovered partially with overnight rest but never returned to baseline during the traverse.
- **Glycogen depletion cascade:** Multi-day touring at moderate intensity depletes muscle glycogen progressively. Without aggressive carbohydrate replenishment (**50–70 g/hour during activity, 8–12 g/kg/day total**), glycogen stores are further depleted each day, accelerating both muscular and cognitive fatigue.
- **Cognitive fatigue:** Sustained multi-day endurance effort impairs decision-making quality — critical for avalanche terrain assessment, route-finding, and paragliding launch decisions. No specific mountain-sport study quantifies this, but military research on sustained operations shows reliable cognitive decline after 3+ days of high physical output (see Gaps §8).
- **Cold and altitude compound the effect:** Multi-day tours typically involve sustained altitude exposure (sleeping at 2,000–3,000 m in huts), poor sleep quality due to altitude and shared dormitories, and cold-related caloric expenditure increases of 200–600+ kcal/day. Each of these independently impairs recovery.

### Application rule

**Pre-trip preparation (4–8 weeks before):**
- BUILD eccentric leg strength with heavy negative-emphasis exercises: Bulgarian split squat eccentrics, walking lunges with slow descent, Nordic hamstring curls.
- INCLUDE multi-hour Zone 1–2 back-to-back training days (e.g., Saturday + Sunday touring) at least 2–3 times during preparation to stress cumulative fatigue systems.
- TAPER strength training in the final week before a multi-day trip — one light session early in the week, then rest.
- VERIFY nutritional preparedness: glycogen-load in the 2 days preceding departure (8–10 g CHO/kg/day).

**In-trip load management:**
- PLAN rest days every **3rd day** during multi-day traverses. If itinerary doesn't allow a full rest day, plan the shortest/easiest stage as day 3.
- FRONT-LOAD easier stages (shorter distance, less vertical) in the first 1–2 days to allow progressive adaptation.
- TARGET an in-trip intensity of **60–75% HRmax** for sustainable touring. Avoid competitive pacing with partners.
- NUTRITION during activity: **50–70 g carbohydrate per hour**, combining liquid and solid sources. Begin fueling within the first 30 minutes — do not wait until hungry.
- HYDRATION: **500–750 mL/hour**, increasing at altitude. Add electrolytes (sodium 300–600 mg/L, potassium, magnesium).
- DAILY CALORIC INTAKE: aim for **8–12 g CHO/kg/day** during multi-day touring. Protein ≥1.6 g/kg/day. Underfueling is the primary preventable risk factor for progressive fatigue.
- USE trekking poles on all descent sections to reduce eccentric quad loading by **~25%**.
- PERFORM 5–10 minutes of gentle stretching and foam rolling each evening at the hut.

**Post-trip recovery:**
- PRESCRIBE **2–3 full rest days** after completing a multi-day traverse (3–5 day trip).
- FOR longer traverses (6+ days) → **4–5 rest days** before returning to structured training.
- FIRST session back should be light Zone 1 aerobic (30–45 min, flat terrain).
- DO NOT schedule lower-body strength training for **at least 72 hours** after the final day of a multi-day trip.
- MONITOR HRV daily during post-trip recovery. Do not resume high-intensity training until HRV returns to within SWC of baseline.
- EXTEND post-trip recovery by an additional 24–48 hours if the traverse included nights above 2,500 m.
- EXPECT DOMS to peak 48–72 hours after the final day; do not interpret this as injury.

**Load classification for weekly planning:**
- EACH day of multi-day touring should be classified as a high-stress endurance session, regardless of pace.
- A 4-day traverse represents approximately **4 high-stress sessions** — the AI should reduce the following week's planned volume by 60–80% and eliminate all high-intensity work for the subsequent 7–10 days.
- ACWR calculations should account for the massive acute load spike that multi-day trips create. Pre-build chronic load in the 4 weeks preceding a planned traverse to keep ACWR within 0.8–1.5.

### Key sources

- Koller A et al. "Effects of recreational ski mountaineering on cumulative muscle fatigue — a longitudinal trial." *Frontiers in Physiology*, 2018. DOI: 10.3389/fphys.2018.01687.
- Postural control study during consecutive hiking days. *Gait & Posture*, 2015.
- Burke LM, van Loon LJC, Hawley JA. "Postexercise muscle glycogen resynthesis." *J Appl Physiol*, 2017.
- Stellingwerff T et al. "Nutrition and altitude." *Sports Medicine*, 2019.
- House S, Johnston S. *Training for the Uphill Athlete*, 2019.

### Cross-references

- → Integration Rule #23 (multi-day touring requires deliberate load management)
- → Integration Rule #14 (carbohydrate needs scale with duration)
- → Recovery §4 (altitude nutrition)
- → Recovery §5 (deload after high-stress periods)



-----

# DOMAIN 3: CONCURRENT STRENGTH + ENDURANCE TRAINING

## 3.1 The interference effect: real but overstated

### Core principle

Concurrent strength and endurance training can attenuate strength, hypertrophy, and especially power gains compared to strength training alone. However, the magnitude is much smaller than originally reported, particularly for recreational athletes. The most robust interference occurs for explosive power; maximal strength and hypertrophy are minimally affected when programming is sensible.

### Evidence summary

**Quantified interference from meta-analyses:**

| Outcome | Wilson et al. 2012 (ES reduction) | Schumann et al. 2022 (between-group SMD) | Practical interpretation |
|---|---|---|---|
| Maximal strength | ~18% lower ES (1.76 → 1.44) | **−0.06** (p = 0.45, not significant) | Minimal to no interference |
| Hypertrophy | ~31% lower ES (1.23 → 0.85) | **−0.01** (p = 0.92, not significant) | Essentially no interference |
| Power/explosive | ~40% lower ES (0.91 → 0.55) | **−0.28** (p = 0.007, significant) | Consistent, meaningful interference |
| Endurance (VO2max) | Not compromised | — | Strength training does not harm and may enhance endurance |

The discrepancy between Wilson 2012 and Schumann 2022 reflects methodological progress: Wilson used within-group effect sizes (which inflate apparent interference) while Schumann's 43-study meta-analysis used between-group standardized mean differences. **The current evidence consensus: maximal strength and muscle size are not significantly compromised by concurrent training — only explosive power is.**

Hickson's foundational 1980 study showed ~43% reduction in strength gains, but used extreme volumes (**11 sessions per week**) unlikely for any recreational athlete.

**Huiberts et al. (2024, *Sports Medicine*):** The first major meta-analysis to stratify concurrent training effects by sex and training status. Key finding: **the interference effect is not sex-neutral**. While this knowledge base is written for a male athlete, this finding is noted for completeness and potential future reference: females showed no significant interference effect, while males showed only small lower-body strength interference. Training status was not a significant moderator.

**Modality matters — running vs. cycling:**
- Wilson et al. (2012): **Running caused significantly more interference** than cycling for both strength and hypertrophy, due to eccentric muscle damage, longer recovery, and higher metabolic cost.
- Sabag et al. (2018): When examining HIIT specifically, cycling HIIT trended toward *more* lower-body strength interference (ES = −0.377) than running HIIT (ES = −0.176) — because high-intensity cycling heavily recruits the same lower-body motor units as squatting.
- Ski touring and hiking are weight-bearing, eccentric-heavy activities (closer to running on the interference spectrum), but their typically low-to-moderate sustained intensity means they do not acutely block anabolic signaling the way high-intensity or high-volume endurance work does.
- **Ski touring and hiking with a pack are concentric-dominant on the ascent** — causing less interference than running, which is a significant advantage for this athlete profile.

**Molecular mechanisms — primarily fatigue-driven, not molecular signaling:**
- The AMPK-mTOR molecular interference is real but overstated in practical terms. Hamilton & Philp (2013) and Coffey & Hawley (2017) demonstrated that the practical interference effect is primarily driven by **residual fatigue and total training volume**, not acute molecular signaling.
- Endurance exercise activates AMPK, which directly inhibits mTOR via TSC2 phosphorylation. This is dose-dependent.
- Coffey et al. (2009): **30 minutes of moderate-intensity cycling did not inhibit mTOR activation**, while **10 × 6-second maximal sprints completely abolished mTOR signaling** when performed before strength work.
- Lundberg et al. (2012): 45 minutes of cycling at 70% VO2max performed 6 hours before resistance exercise caused no inhibition of mTOR.
- AMPK returns to baseline within **1–3 hours** post-endurance; mTOR remains elevated **~18 hours** post-resistance.
- **Practical implication: low-to-moderate intensity endurance — the bread and butter of mountain sport — poses minimal molecular interference risk.**
- For untrained/recreational individuals, any exercise creates a "generic molecular footprint" — true phenotype-specific molecular conflict emerges mainly in highly trained athletes.

**Practical magnitude for concurrent mountain athletes:**
- **Expect ~15–25% slower strength progression** than a dedicated lifter. Lower body gains are most affected; upper body is relatively unaffected by mountain activities.
- Separate strength and endurance sessions by ≥ 6 hours (ideally 24+). After mountain days with > 1,000m elevation gain, reduce expected gym performance by 5–10% and target RPE by 0.5–1.0.

**Practical magnitude for recreational athletes:**
- Schumann et al. (2022): training status was not a significant moderator of interference.
- Murach & Bagley (2016): interference on muscle growth "is not as compelling as previously thought" — concurrent training may even augment hypertrophy.
- Gäbler et al. (2023): recreationally active individuals exhibit similar adaptive responses whether single-mode or concurrent.
- **For a recreational mountain athlete training 3–5 sessions/week total, interference is likely negligible for strength and hypertrophy, and small for power.**

### Application rule

- DO NOT fear concurrent training for recreational mountain athletes. Program both modalities confidently. Interference is primarily fatigue-driven, not molecular (Hamilton & Philp 2013; Coffey & Hawley 2017).
- EXPECT ~15–25% slower strength progression than dedicated lifters; lower body most affected; upper body relatively unaffected by mountain activities.
- IF user has power/explosive goals → separate those sessions from endurance by ≥24 hours.
- KEEP majority of endurance volume at low-to-moderate intensity to minimize AMPK-mediated interference.
- ENSURE adequate protein (≥1.6–2.0 g/kg/day) and positive energy balance — these substantially mitigate interference.
- USE cycling-based or low-impact endurance where possible for cross-training; reserve sport-specific weight-bearing endurance for specificity phases.
- MONITOR strength performance trends during endurance-heavy phases; IF 1RMs or key rep performances drop >5–10% for several weeks → reduce endurance intensity/volume and prioritize recovery.
- SESSION DISPLACEMENT STRATEGY: plan **2 guaranteed + 1 bonus** gym sessions per week. When only 1 gym day remains in a week, switch to a full-body maintenance template with compound lifts at ≥ 85% recent loads — Graves et al. (1988) showed strength maintained at 1×/week for 12 weeks.

### Key sources

- Wilson JM et al. "Concurrent training: A meta-analysis." *J Strength Cond Res*, 2012; 26(8): 2293–2307. DOI: 10.1519/JSC.0b013e31823a3e2d.
- Schumann M et al. "Compatibility of concurrent aerobic and strength training." *Sports Medicine*, 2022; 52(3): 601–612. DOI: 10.1007/s40279-021-01587-7.
- Hickson RC. "Interference of strength development." *Eur J Appl Physiol*, 1980; 45(2-3): 255–263.
- Coffey VG, Hawley JA. "Concurrent exercise training: do opposites distract?" *J Physiol*, 2017; 595(9): 2883–2896.
- Fyfe JJ, Bishop DJ, Stepto NK. "Interference between concurrent resistance and endurance exercise." *Sports Med*, 2014; 44(6): 743–762.
- Murach KA, Bagley JR. "Skeletal muscle hypertrophy with concurrent exercise training." *Sports Med*, 2016; 46(8): 1029–1039.
- Sabag A et al. "Compatibility of HIIT and resistance training." *J Sports Sci*, 2018; 36(21): 2472–2483.
- Gäbler M et al. Systematic review on concurrent training, 2023.
- Baar K. "Using molecular biology to maximize concurrent training." *Sports Med*, 2014; 44(2): 117–125.
- Coffey VG et al. mTOR inhibition by sprints, 2009.
- Lundberg TR et al. mTOR signaling with separated concurrent sessions, 2012.
- Huiberts RCM et al. "Concurrent strength and endurance training: a systematic review and meta-analysis on the impact of sex and training status." *Sports Medicine*, 2024. DOI: 10.1007/s40279-023-01943-9.

### Cross-references

- → Periodization §3 (microcycle templates implement interference mitigation)
- → Integration Rules #1, #2, #15

-----

## 3.2 Scheduling that protects both adaptations

### Core principle

Session spacing is one of the most actionable levers. Separating sessions by **≥24 hours yields the best outcomes**. When same-day is unavoidable, minimum **6-hour gap** protects most adaptations, though explosive power still suffers. When sessions must be closely spaced, **strength before endurance** produces significantly better strength outcomes without compromising endurance.

### Evidence summary

**Time gaps — Robineau et al. (2016), 58 amateur rugby players, 7 weeks:**

| Recovery gap | Strength outcome | Endurance outcome |
|---|---|---|
| 0h (same session) | Worst — lowest gains in bench and half-squat 1RM | Good |
| 6h (twice daily) | Better than 0h but still suboptimal — MVC at 180°/s lower than 24h | Good |
| 24h (separate days) | **Best** — comparable to strength-only; highest VO2peak gains too | **Best** |

- Sporer & Wenger (2003): After endurance training, leg press work capacity remained diminished at both **4 and 8 hours**, recovering fully only at **24 hours**. Interference was **localized to exercised muscles** — upper body unaffected after cycling.
- Baar (2014): AMPK elevated for ~**3 hours** post-endurance, establishing 3 hours as minimum molecular recovery window.

**The "strength first" rule:**
- Eddens, van Someren & Howatson (2018), meta-analysis of 10 studies: resistance before endurance produced **+6.91% in lower-body dynamic strength** (95% CI: 1.96–11.87, p = 0.006).
- Murlasits et al. (2018): strength→endurance order produced **+3.96 kg** in lower body 1RM.
- Neither study found any effect of order on VO2max — **endurance gains are unaffected by sequence**.
- **Important condition:** When sessions are separated by ≥3 hours, order becomes less critical (Fyfe et al. 2020; Schumann et al. 2022).
- Jones et al. (2017): endurance before strength reduces ability to maintain **80% 1RM during subsequent lifting** (p < 0.05).

**Same-day vs. separate-day:**
- Sale et al. (1990): alternating-day training produced better outcomes than same-day over 20 weeks.
- Schumann et al. (2022): explosive strength attenuation significant only with same-session training (p = 0.043), not when separated by ≥3 hours.
- Hierarchy: **separate days > same day with ≥6h gap > same day with 3h gap > same session**.

**Counterintuitive finding:** Fyfe et al. (2020): for power preservation, HIIT→RT order (endurance first, 3h gap) actually preserved countermovement jump performance better than RT→HIIT, possibly due to higher cumulative neuromuscular cost when resistance precedes intervals.

**Session order for different goal priorities:**

| Priority | Recommended order | Minimum gap | Ideal gap |
|---|---|---|---|
| Maximal strength | Strength → Endurance | 6h | 24h (separate days) |
| Hypertrophy | Strength → Endurance | 6h | 24h |
| Explosive power | Separate days only | 24h | 24–48h |
| Endurance performance | Either order works | 3–6h | 24h |

### Application rule

- DEFAULT to separate-day programming — alternate strength and endurance days.
- IF only 4 days/week → pair strength with low-intensity endurance on same day, ≥6h apart, strength first.
- NEVER schedule high-intensity endurance within 6 hours before a strength session.
- FOR power-focused blocks → enforce ≥24-hour separation.
- WHEN mountain sport days are long/demanding → do not schedule strength same day; place on preceding or following day.
- ON weeks with weekend mountain objectives → schedule key strength session Monday or Tuesday.
- NEVER schedule demanding mountain session within 8 hours after lower-body strength (Doma et al., 2017).

### Key sources

- Robineau J et al. "Specific training effects depend on recovery duration." *J Strength Cond Res*, 2016; 30(3): 672–683.
- Sporer BC, Wenger HA. "Effects of aerobic exercise on strength performance." *J Strength Cond Res*, 2003; 17(4): 638–644.
- Eddens L, van Someren K, Howatson G. "Role of intra-session exercise sequence." *Sports Med*, 2018; 48(1): 177–188.
- Murlasits Z, Kneffel Z, Thalib L. "Concurrent strength and endurance training sequence." *J Sports Sci*, 2018; 36(11): 1212–1219.
- Sale DG et al. "Comparison of two regimens of concurrent training." *Med Sci Sports Exerc*, 1990.
- Jones TW et al. *Eur J Sport Sci*, 2017; 17(3): 326–334.
- Fyfe JJ et al. mTORC1 signaling, *PLOS ONE*, 2020.

-----

## 3.3 Periodizing the mountain athlete's year

### Core principle

A mountain endurance athlete's year should be structured into **priority phases** that sequentially emphasize different qualities, leveraging the principle that aerobic fitness and maximal strength have long residual training effects (~30 days each) and can be maintained while another quality is developed. Block periodization produces superior concurrent training adaptations compared to mixing everything simultaneously.

### Evidence summary

**Block periodization superiority:**
- Rønnestad et al. (2019): BP vs. traditional mixed in athletes with equal total volume. BP produced knee extension peak torque **+6.6% vs. −4.2%** and superior VO2max.
- García-Pallarés et al. (2010): BP achieved similar/better aerobic improvements with **half the endurance volume** in world-class kayakers.
- Mølmen, Øfsteng & Rønnestad (2019), meta-analysis of 20 studies: BP of endurance training showed superior VO2max effects (SMD: 0.28; 95% CI = 0.01–0.54).

**Issurin's residual training effects:**

| Fitness component | Residual effect duration | Implication |
|---|---|---|
| Aerobic endurance | **30 ± 5 days** | Can maintain ~4 weeks without direct training |
| Maximum strength | **30 ± 5 days** | Can maintain ~4 weeks without direct training |
| Anaerobic glycolytic endurance | 18 ± 4 days | Needs more frequent stimulus |
| Strength endurance | 15 ± 5 days | Relatively short retention |
| Maximal speed/alactic power | 5 ± 3 days | Decays rapidly |

**Four-phase annual model for mountain athletes:**

**Phase 1 — Off-season strength focus (8–12 weeks):** Rønnestad recommends minimum **8 weeks** for strength development with 2–3 sessions/week. Progression: Weeks 1–4 (anatomical adaptation, 2–3 × 12–15 at 50–70% 1RM) → Weeks 5–8 (max strength, 3 × 6–8 at 75–85%) → Weeks 9–12 (power, 3 × 4–6 at 80–90%, explosive concentric). Maintain 2 endurance sessions/week during this phase — never drop endurance entirely. Volume can be reduced by up to 33% without VO2max losses. **Intensity is the non-negotiable variable** — one HIIT session per week during strength block suffices (Slettaløkken & Rønnestad, 2014).

**Phase 2 — Pre-season concurrent (6–8 weeks):** Strength transitions to strength endurance and sport-specific work. Uphill Athlete methodology: weighted uphill carries at 20%+ bodyweight, 1–2×/week for 6–10 weeks. Endurance volume increases to 4–5 sessions/week with polarized distribution (80/20). Strength drops to 2 sessions/week. Key: **train not to failure** (Izquierdo-Gabarren et al., 2010).

**Phase 3 — In-season sport priority (16–20 weeks):** Sport activity becomes primary stimulus. Strength to maintenance: **1 heavy session every 7–10 days**, never exceeding **3 consecutive weeks without heavy strength training** (Rønnestad et al., 2010, 2015, 2022). Rønnestad et al. (2011): 1×/week maintained all preseason strength and jump gains over 12-week season in soccer; 1×/every 2 weeks was insufficient.

**Phase 4 — Transition/recovery (2–4 weeks):** Active recovery, unstructured activity. Keep short — Mujika & Padilla (2001): time to exhaustion decreased 9–25% after just 2 weeks complete detraining.

**Mesocycle structure within phases:** 3:1 loading:deload ratio most common. Uphill Athlete: no more than 10% volume increase/week with recovery week every 4th week.

### Application rule

- STRUCTURE annual plan around athlete's primary sport season:
  - Winter mountain athlete (ski touring/splitboarding Dec–Apr): Phase 1 = Jun–Sep, Phase 2 = Oct–Nov, Phase 3 = Dec–Apr, Phase 4 = May.
  - Summer hike-and-fly athlete: invert calendar.
- WITHIN each phase → use 3:1 mesocycle structure (3 weeks building, 1 week deload).
- DURING Phase 1 → maintain 2 endurance sessions/week including 1 interval session.
- DURING Phase 3 → ensure ≥1 strength session per 10-day rolling window. ALERT if 3 weeks pass without strength training.
- ENFORCE ≤10% per week progression rule within build weeks.
- IMPLEMENT explicit "priority tags" for blocks (strength, endurance, balanced) and bias prescriptions accordingly.

### Key sources

- Rønnestad BR et al. "Block periodization in ice hockey." *Scand J Med Sci Sports*, 2019; 29(1).
- Rønnestad BR, Hansen EA, Raastad T. "In-season strength maintenance." *Eur J Appl Physiol*, 2010; 110: 1269–1282.
- Rønnestad BR. Case report: multiple seasons HST in cyclists. *Front Sports Active Living*, 2022.
- García-Pallarés J et al. "Performance changes in kayakers." *Eur J Appl Physiol*, 2010; 110(1): 99–107.
- García-Pallarés J, Izquierdo M. "Strategies to optimize concurrent training." *Sports Med*, 2011; 41(4): 329–343.
- Issurin VB. "Block periodization." *J Sports Med Phys Fitness*, 2008; 48(1): 65–75.
- Mølmen KS, Øfsteng SJ, Rønnestad BR. "Block periodization of endurance training." *Open Access J Sports Med*, 2019; 10: 145–160.
- Spiering BA et al. "Maintaining physical performance: minimal dose." *J Strength Cond Res*, 2021; 35(5): 1449–1458.
- House S, Johnston S, Jornet K. *Training for the New Alpinism* and *Training for the Uphill Athlete*.

-----

## 3.4 Holding onto strength with the minimum effective dose

### Core principle

Strength and muscle mass can be maintained on dramatically reduced training — as little as **1 session/week** with **1–3 sets/exercise** — for up to **32 weeks**, provided the single non-negotiable condition is met: **training intensity (load) must stay high**. Volume and frequency are highly reducible; intensity is not.

### Evidence summary

**The landmark maintenance studies:**

Bickel, Cross & Bamman (2011): After 16 weeks full training (3 days/week, 3 exercises, 3 sets each), 70 adults randomized to 32 weeks of either: complete detraining, **one-third dose** (1 day/week, 3 sets × 3 exercises = ~9 weekly sets for legs), or **one-ninth dose** (1 day/week, 1 set × 3 exercises = ~3 weekly sets for legs). In young adults (20–35 years), **both prescriptions fully preserved strength for the entire 32 weeks.** The one-third dose actually produced additional myofiber hypertrophy. Even the one-ninth dose — an **89% volume reduction** — maintained all strength gains. Note: these results were confirmed in young adults; older adults (60–75) did not maintain myofiber hypertrophy on reduced doses, though strength was preserved.

Spiering, Mujika, Sharp & Foulis (2021) synthesis: frequency can drop to **1 session/week**, volume to **1 set/exercise**, strength preserved for up to 32 weeks — but only if relative load stays at previous levels. **Exercise intensity is the key variable.**

**Frequency findings:**

| Frequency | Maintains? | Duration tested | Conditions |
|---|---|---|---|
| **2×/week** | Yes, robustly | 32+ weeks | Preferred for >12-week phases |
| **1×/week** | Yes | Up to 32 weeks | Sufficient if intensity maintained |
| **1×/2 weeks** | Inconsistent | 8–12 weeks | Rønnestad 2011: strength declined in soccer players |
| **0×/week** | No (after ~3–4 weeks) | — | Bosquet 2013: significant force decline from week 3 |

Tavares et al. (2017): both 1× and 2×/week maintained half-squat 1RM and quad CSA over 8 weeks when volume equated.

**Volume reductions possible:** Can reduce by **67–89%** from peak volume. An athlete doing 15–20 sets/muscle/week during strength block can cut to 4–6 sets during endurance phase with no meaningful strength loss.

**Detraining timeline when training stops completely:**

| Timeframe | Strength changes | Muscle size changes |
|---|---|---|
| 0–2 weeks | Minimal/no loss | No measurable (apparent decreases are water/glycogen) |
| 2–4 weeks | Minor losses beginning | Minimal true loss |
| 4–8 weeks | Moderate decline (~5–10%) | Measurable atrophy, especially Type II |
| 8–12 weeks | Significant decline (7–15%) | Moderate atrophy |
| 12–24 weeks | Substantial decline | Significant mass loss |

Bosquet et al. (2013, 103 studies): significant maximal force decline begins at approximately **week 3**. Mujika & Padilla (2001): 0–45% of previously gained strength preserved after 8–12 weeks complete inactivity. Regaining lost strength takes approximately **half the duration** of detraining.

**Minimum effective training dose study:** Androulakis-Korakakis, Fisher & Steele (2020): a single set of 6–12 reps at ~70–85% 1RM, 1–3×/week, is sufficient to produce significant 1RM gains — above pure maintenance dose.

### Application rule

**Tiered maintenance system:**

**Tier 1 — Standard in-season maintenance (1–2×/week, 25–40 min):**

| Exercise | Sets × Reps | Load | RPE |
|---|---|---|---|
| Back squat or front squat | 2–3 × 4–6 | 80–85% 1RM | 8–9 |
| Romanian deadlift or hip thrust | 2–3 × 6–8 | 75–80% 1RM | 7–8 |
| Pull-ups or barbell rows | 2–3 × 6–8 | Loaded/bodyweight | 7–9 |
| Overhead press or bench press | 2 × 6–8 | 75–80% 1RM | 7–8 |
| **Total: ~8–11 sets, 4 exercises, ≤40 minutes** | | | |

**Tier 2 — Peak endurance / expedition maintenance (1×/week, 20–30 min):**
- 3 compound exercises, 2 sets each, at previous training loads. Sustainable for up to 32 weeks.

**Tier 3 — Taper / multi-day objectives (0×/week, max 2–3 weeks):**
- No strength training. Flag if >3 weeks pass; auto-schedule session upon return.

**Three non-negotiables:**
1. Keep intensity ≥70% 1RM — never reduce load to "go easy."
2. Train at least 1×/week during extended endurance phases.
3. Use compound movements exclusively during maintenance — eliminate all isolation work and extended warm-ups.

**What can be aggressively cut:** total sets (by 67–89%), number of exercises (6–8 → 3–4), all isolation work, session duration (60–90 → 20–40 min). **What must be preserved:** relative load, proximity to failure (RPE ≥7), minimum weekly frequency.

**e1RM tracking rules for monitoring progression:**
- Use **Epley formula** (e1RM = weight × (1 + 0.0333 × reps)) for sets of ≤ 6 reps (Reynolds et al., 2006; DiStasio 2014 validated Epley within +2.7 kg from 3RM).
- Use **average of Epley + Brzycki** for 7–10 reps.
- **Flag sets of > 10 reps** as low-confidence for e1RM purposes (Reynolds: prediction from > 10 reps had > 20% error in some exercises).
- Normal session-to-session variability is **± 3–5%** — do not react to single-session fluctuations.
- A genuine plateau requires e1RM trending **flat or declining for ≥ 4 weeks** despite adequate recovery — always cross-reference with mountain activity log before concluding "plateau."
- Track e1RM from the **best set of each session** (not average) to reduce accumulated in-session fatigue noise.

### Key sources

- Bickel CS, Cross JM, Bamman MM. "Exercise dosing to retain resistance training adaptations." *Med Sci Sports Exerc*, 2011; 43(7): 1177–1187. DOI: 10.1249/MSS.0b013e318207c15d.
- Spiering BA, Mujika I, Sharp MA, Foulis SA. "Maintaining physical performance: minimal dose." *J Strength Cond Res*, 2021; 35(5): 1449–1458.
- Rønnestad BR, Nymark BS, Raastad T. "In-season strength maintenance frequency in soccer." *J Strength Cond Res*, 2011; 25(10): 2653–2660.
- Bosquet L et al. "Effect of training cessation on muscular performance." *Scand J Med Sci Sports*, 2013; 23: e140–149.
- Mujika I, Padilla S. "Detraining." *Sports Med*, 2000; 30(2): 79–87 and 30(3): 145–154.
- Androulakis-Korakakis P, Fisher JP, Steele J. "Minimum effective training dose for 1RM." *Sports Med*, 2020; 50(4): 751–765.
- Tavares LD et al. Reduced frequency maintenance. *Eur J Sport Sci*, 2017; 17(6): 665–672.

### Cross-references

- → Integration Rule #3 (intensity is non-negotiable for maintenance)
- → Integration Rule #10 (never exceed 3 weeks without strength)
- → Integration Rule #21 (shift, don't skip — consolidate key elements)
- → Periodization §1 (annual plan phase 3 implements these maintenance doses)
- → Periodization §5.6 (schedule disruption management uses these doses)



-----

# DOMAIN 4: RECOVERY AND READINESS

## 4.1 HRV as a readiness marker

### Core principle

Heart rate variability — specifically the natural log of rMSSD (ln rMSSD) — is the single best objective marker of autonomic recovery status when tracked as a **7-day rolling average against an individual baseline**. Single-day readings are unreliable; weekly trends in both the mean and coefficient of variation (CV) reveal adaptation vs. maladaptation. HRV-guided training produces equal or superior performance outcomes compared to pre-planned training while requiring fewer high-intensity sessions.

### Evidence summary

**HRV-guided vs. pre-planned training:**
- Kiviniemi et al. (2007): HRV group improved VO2peak 56 → 60 mL/kg/min (p = 0.002); predefined group: no significant change.
- Nuuttila et al. (2017): significantly greater Vmax and CMJ improvements in HRV-guided group over 8 weeks.
- Kurtz et al. (2021): HRV-guided HIFT achieved equivalent strength gains (squat +14.2%, deadlift +12.6%) with **significantly fewer high-intensity days** (mean difference: −13.56 days, p < 0.001).
- Manresa-Rocamora et al. (2021) meta-analysis: moderate effect favoring HRV-guided training for cardiac-vagal modulation (SMD = 0.50, 95% CI: 0.09–0.91).
- A 2024 meta-analysis (Plews et al.): HRV-guided athletes achieved **4–7% better endurance outcomes** over ≥6 months with **31% lower risk** of injury/overtraining, and with **reduced training volume** (13 fewer high-intensity days per 30-day block). Benefit greatest in **recreational athletes** balancing sport with work.
- **Addleman et al. (2024, *J Functional Morphology and Kinesiology*):** Published the first practical implementation guidelines for HRV in strength and conditioning contexts, recommending 7-day rolling RMSSD averages with smallest worthwhile change (SWC) thresholds. This is the most directly applicable guideline for the Ascent coaching system's implementation.

**Why rMSSD, not SDNN:**
- rMSSD captures parasympathetic/vagal variability, reliable in recordings as short as **60 seconds** (Esco & Flatt, 2014). ICC of **0.917** vs ~0.57 for SDNN.
- Ln transformation normalizes the positively skewed distribution.

**7-day rolling CV thresholds (Flatt research):**
- CV below 3–4% → stable, well-adapted state.
- CV 4–7% → normal training variation.
- CV above 7–10% paired with declining weekly mean → maladaptation risk.
- Plews et al. (2012): NFOR athlete showed CV declining at −0.65%/week alongside declining ln rMSSD (slope = −0.17 ms/week).
- **Critical red flag:** declining mean HRV with simultaneously declining CV — "parasympathetic saturation" may indicate NFOR.
- **Le Meur et al. (2013) caveat:** Overloaded endurance athletes can show *increasing* HRV alongside declining performance — parasympathetic hyperactivation. **Ascent must never use simple "high = good" logic.** Interpret HRV trends in context of training load and subjective state. An unexplained HRV increase during heavy training blocks should be flagged as potentially concerning, not reassuring.
- HRV-CV is inversely correlated with fitness (r = −0.74, Flatt).

**Individual baselines trump population norms:**
- Plews et al. (2013, 2014): isolated single-day scores cannot detect training responses; weekly averaged data reveals clear patterns.
- Minimum **3 valid data points per week** for meaningful assessment.
- Smallest worthwhile change (SWC) = individual mean ± 0.5 × individual SD (Buchheit, 2014).

**Strength vs. endurance HRV responses:**
- Hypertrophic loading (5 × 10 at 70% 1RM) → rMSSD suppression **~64%**.
- Maximal strength loading (15 × 1 at 100% 1RM) → suppression **~29%**.
- Recovery to baseline: **24–72 hours** after heavy resistance vs hours to 24h after sub-threshold aerobic.
- Training below LT1 tends to increase HRV; above LT2 suppresses for 12–48 hours.

**Morning measurement protocol:**
- Immediately upon waking, consistent seated position, minimum 60 seconds, validated device (chest strap or validated PPG).
- Natural breathing acceptable for rMSSD.
- Discard recordings with >5% ectopic/corrected beats.
- For very low resting HR athletes → seated or standing to avoid parasympathetic saturation artifacts.

### Application rule

**Traffic-light decision framework:**
- **GREEN (train as planned):** daily ln rMSSD within individual SWC, weekly CV < 5–7%, weekly mean stable or rising.
- **YELLOW (modify intensity):** daily ln rMSSD outside SWC for 1–2 days OR weekly CV 7–10%. Prescribe low-intensity endurance or technique work instead of planned high-intensity.
- **RED (recovery priority):** daily ln rMSSD below SWC for ≥3 consecutive days, weekly CV > 10% with declining mean, OR weekly mean declining for ≥2 weeks. Prescribe rest, mobility, or very light Zone 1.
- AFTER heavy resistance training → expect HRV suppression 24–72 hours; do NOT flag unless suppression persists beyond 72 hours.
- ALWAYS combine HRV with subjective wellness — HRV cannot detect muscular soreness or mental fatigue.

### Key sources

- Plews DJ et al. "Heart rate variability in elite triathletes." *Eur J Appl Physiol*, 2012; 112(11): 3729–3741.
- Plews DJ et al. "Training adaptation and heart rate variability." *Sports Med*, 2013; 43(9): 773–781.
- Plews DJ et al. "Heart-rate variability and training-intensity distribution in elite rowers." *Int J Sports Physiol Perform*, 2014; 9(6): 1026–1032.
- Plews DJ et al. "Monitoring training with HRV: how much compliance?" *Int J Sports Physiol Perform*, 2014; 9(5): 783–790.
- Flatt AA, Esco MR. "Evaluating individual training adaptation with smartphone-derived HRV." *J Strength Cond Res*, 2016; 30(2): 378–385.
- Kiviniemi AM et al. "Endurance training guided by daily HRV." *Eur J Appl Physiol*, 2007; 101(6): 743–751.
- Manresa-Rocamora A et al. "HRV-guided training for enhancing performance." *Int J Environ Res Public Health*, 2021; 18(19): 10299.
- Nuuttila OP et al. "HRV-guided vs. predetermined block training." *Int J Sports Med*, 2017; 38: 909–920.
- Kurtz et al. HRV-guided HIFT, 2021.
- Buchheit M. "Monitoring training status with HR measures." *Front Physiol*, 2014.
- Altini M. "Coefficient of variation: what is it and how can you use it?" HRV4Training blog, 2019.
- Addleman RJ et al. "Heart rate variability applications in strength and conditioning: a narrative review." *J Functional Morphology and Kinesiology*, 2024; 9(2): 93. DOI: 10.3390/jfmk9020093.

### Cross-references

- → Periodization §5 (three-tier autoregulation framework uses HRV thresholds)
- → Recovery §3 (subjective readiness must be combined with HRV)
- → Endurance §2.5 (altitude suppresses HRV acutely)
- → Integration Rule #13 (multi-signal convergence)


-----

## 4.2 Sleep and performance

### Core principle

Sleep is the single most powerful recovery modality. Below **7 hours**, measurable decrements emerge across hormonal profiles, muscle protein synthesis, strength endurance, and cognitive function. Athletes should target **8–9 hours** as minimum during training phases. At **2,000–4,000 m**, altitude-induced sleep disruption is an unavoidable recovery cost that must be factored into load management.

### Evidence summary

**Hormonal effects of sleep loss:**
- One week of 5 hours/night reduces testosterone by **10–15%**, equivalent to 10–15 years of aging (Leproult & Van Cauter, 2011).
- Single night total deprivation: testosterone **−24%**, cortisol **+21%**, muscle protein synthesis **−18%** (Lamon et al., 2021).
- Growth hormone: 70–80% of daily secretion occurs during deep/slow-wave sleep.
- 30 hours deprivation reduces pre-exercise muscle glycogen by **~33%** (Skein et al., 2011).

**Strength performance:**
- Craven et al. (2022), meta-analysis of 69 publications: overall decrement **−7.56%** (95% CI: −11.9 to −3.13) from sleep loss ≤6 hours (note: I² = 98.1%, high heterogeneity). Maximal strength ~**−3%**, strength endurance **~−10%**, skill-based **~−21%**.
- Performance degrades ~**0.4% per additional hour awake**.
- Compound movements more vulnerable than isolation.
- Single poor night largely preserves maximal single-effort strength; 2+ nights produce reliable decrements.

**Endurance performance:**
- Time to exhaustion at 80% VO2max drops **11%** after 36 hours without sleep (Martin, 1981).
- Self-paced running distance decreases **~6%** after single night of 4-hour sleep (Temesi et al., 2020).
- RPE consistently elevated, causing voluntary pacing reduction.

**Meta-analysis of acute sleep deprivation in athletes (Gong et al., 2024, *Nature and Science of Sleep*):** Ranked performance domains by vulnerability: high-intensity intermittent exercise ES = **−1.57** (most affected); skill control ES = **−1.06**; speed ES = **−0.67**; aerobic endurance ES = **−0.54**; explosive power ES = **−0.39**. This granular ranking is directly actionable: the AI should prioritize rescheduling high-intensity interval sessions after poor sleep, while moderate steady-state aerobic work is more resilient.

**Napping evidence (Mesas et al., 2023, *BJSM*):** **30–60 minute naps** improve cognitive performance (SMD = 0.69), physical performance (SMD = 0.99), and reduce fatigue (SMD = −0.76). For athletes with compromised nighttime sleep — including hut nights at altitude — a mid-day nap is a high-yield countermeasure.

**Injury risk:**
- Athletes sleeping < 8 hours: **1.7× more likely** to sustain injury (Milewski et al., 2014, n = 112).
- Von Rosen et al. (2017): athletes averaging > 8 hours had **61% lower odds** of new injury.
- Average elite athlete sleeps only 6.5–7 hours by actigraphy (Leeder et al., 2012), with efficiency **80.6%** vs 88.7% controls.

**Sleep quality benchmarks (Knufinke et al., 2018, n = 98 elite athletes):**
- Deep sleep: 21 ± 8%
- REM: 27 ± 7%
- Sleep efficiency: 88 ± 5%
- Functional thresholds: efficiency >85% (good), 80–85% (acceptable), <80% (poor); deep sleep >20% (good), 15–20% (acceptable), <15% (poor); onset latency <15 min (good), >30 min (poor).

**Sleep extension:**
- Mah et al. (2011): Stanford basketball players, 6.7 → 8.5 hours over 5–7 weeks: sprint **−0.7s (4.3%)**, free throw **+9%**, 3-point **+9.2%**, self-rated performance 6.9 → 8.8/10.
- Cunha et al. (2023): extending sleep by **46–113 minutes** in athletes habitually sleeping ~7 hours, supplemented by 20–90 min naps.

**Altitude sleep disruption:**
- Begins above **2,000 m** with periodic breathing onset.
- At 2,500–3,500 m: ~25% develop central sleep apnea, deep sleep markedly reduced, nocturnal hypoxemia significant.
- At 3,500–4,500 m: deep sleep severely reduced, REM may be absent first night, fragmentation near-universal.
- Improves over 2–3 nights with acclimatization, but periodic breathing persists.
- Assume **20–30% reduction in effective sleep quality** for any night above 2,500 m.

### Application rule

- **< 6 hours = RED ALERT:** reduce next-day volume ≥50%, eliminate high-intensity work. Prioritize rescheduling high-intensity intervals and skill-based work (most vulnerable per Gong 2024).
- **6–7 hours = YELLOW:** reduce intensity, favor aerobic base work (least sleep-sensitive per Gong 2024).
- **7–8 hours = GREEN:** adequate for most training.
- **8–9+ hours = OPTIMAL:** encourage during heavy training blocks.
- IF sleep compromised → recommend 30–60 min nap before afternoon/evening training (Mesas 2023: SMD 0.99 for physical performance).
- DURING altitude exposure (hut nights, multi-day tours) → extend next recovery window by 24–48 hours; reduce planned load by 20–30%.
- IF 3+ consecutive nights < 6 hours → recommend unplanned deload regardless of other markers.
- IF deep sleep < 15% for 3+ nights → flag for sleep hygiene, stress, or altitude investigation.
- IF sleep significantly reduced before planned heavy/high-skill day → reclassify to moderate/low intensity or swap with easier day.

### Key sources

- Mah CD et al. "Effects of sleep extension on athletic performance." *Sleep*, 2011; 34(7): 943–950.
- Craven J et al. "Effects of acute sleep loss on physical performance." *Sports Medicine*, 2022; 52(11): 2669–2690.
- Fullagar HHK et al. "Sleep and athletic performance." *Sports Medicine*, 2015; 45: 161–186.
- Milewski MD et al. "Chronic lack of sleep and sports injuries." *J Pediatr Orthop*, 2014; 34(2): 129–133.
- Leproult R, Van Cauter E. "Sleep restriction on testosterone." *JAMA*, 2011; 305(21): 2173–2174.
- Lamon S et al. "Acute sleep deprivation on muscle protein synthesis." *Physiological Reports*, 2021.
- Knufinke M et al. "Sleep in elite athletes." *J Sci Med Sport*, 2018.
- Gong L et al. "Effects of acute sleep deprivation on sporting performance in athletes: a comprehensive systematic review and meta-analysis." *Nature and Science of Sleep*, 2024; 16: 3207–3226. DOI: 10.2147/NSS.S467531.
- Mesas AE et al. "The effect of daytime napping on athletic performance: a systematic review and meta-analysis." *BJSM*, 2023. DOI: 10.1136/bjsports-2022-106355.
- Bloch KE et al. Sleep at high altitude. *Sleep*, 2012.
- Patrician A. "Periodic breathing during sleep at high altitude." *J Physiology*, 2024.

-----

## 4.3 Subjective readiness markers

### Core principle

Subjective wellness measures — fatigue, soreness, sleep quality, stress, mood — are **more sensitive and consistent** than any objective marker for detecting daily training load responses and predicting injury risk. Device-based composite scores (Garmin Body Battery, Training Readiness) provide useful directional data but have no published independent validation and systematically miss muscular soreness and mental fatigue.

### Evidence summary

**Saw et al. (2016), systematic review of 56 studies:** "Subjective self-reported measures trump commonly used objective measures." Nummela et al. (2024) confirmed that subjective markers — readiness to train and leg soreness — were the most sensitive indicators of training load response in recreational runners, with greater magnitude responses in overreached individuals than resting or exercise HR. Critically, psychological symptoms (mood disturbance, motivation loss, sleep disturbance) **precede measurable HRV or performance changes** — making subjective wellness the earliest-available detection system for maladaptation.

**Subjective wellness questionnaire specification:**
Build a 30-second daily questionnaire (Telegram or Slack): sleep quality, fatigue, muscle soreness, motivation, stress — each 1–5 scale. Normalize to individual **Z-scores against a 14–28 day rolling baseline**. Fatigue, muscle soreness, and stress are inverted (high = bad) so use (6 − value) before computing composite. Flag composite Z < −1.0 SD for two consecutive days. The composite should be auto-calculated: `(sleep_quality + (6 − fatigue) + (6 − muscle_soreness) + motivation + (6 − stress)) / 5.0`. This is the **highest-priority unbuilt feature** in the Ascent system — stronger evidence base than any wearable metric for detecting maladaptation.

**Garmin Body Battery:** Firstbeat Analytics engine, 5–100 score based on rMSSD-derived stress/recovery, activity drain, sleep recharge. Zones: 76–100 high, 26–75 moderate, 5–25 depleted. No independent validation published. de Vries et al. (2025, *JMIR mHealth*): did not consistently align with self-reported recovery in Dutch police. Doherty et al. (2025): no manufacturer disclosed algorithmic weights; none validated against clinical outcomes.

**Garmin Training Readiness (0–100):** Combines sleep score, HRV status vs. 60-day baseline, recovery time, acute load, stress history, sleep history. Zones: 60–100 green, 40–59 yellow, <40 red. **Critical blind spot: strength training poorly captured; systematically underestimates neuromuscular fatigue from lifting.**

**The Hooper Index** (Hooper & Mackinnon, 1995): 4 items (sleep quality, stress, fatigue, DOMS), 1–7 each, sum 4–28 (lower = better). Rabbani et al. (2019): lower typical error/SWC ratio (3.1 vs 4.4) and higher signal-to-noise ratio (5.5 vs 1.5) compared to HRV.

**Thorpe et al. (2015, 2017):** Perceived fatigue and soreness "clearly more sensitive than ln rMSSD to daily fluctuations in training load" in elite Premier League players. Very large correlations (r = 0.72–0.89) between wellness changes and load changes.

**When signals disagree:**
- HRV shows recovery but athlete feels fatigued → **trust subjective report** (muscular damage and mental fatigue outside autonomic monitoring).
- HRV suppressed but athlete feels fine → proceed cautiously (chronic suppression may be early warning pre-conscious awareness).
- Psychological symptoms of overtraining (mood, motivation, sleep disruption) typically appear **days to weeks before** physiological markers.

**Injury prediction:**
- Hamlin et al. (2019, 182 athletes, 4 years): decreased mood (OR = 0.89), decreased sleep duration (OR = 0.94), increased academic stress (OR = 0.91) predicted injury.
- Laux et al. (2015): greatest injury risk from simultaneous training load increase and sleep duration decrease.

### Application rule

- IMPLEMENT **4-item daily wellness check** (fatigue, soreness, sleep quality, stress on 1–5 scale) each morning, < 30 seconds.
- NORMALIZE all inputs to individual Z-scores against rolling 7–14-day baselines.
- WEIGHT inputs in three tiers:
  - **Tier 1 (highest):** subjective fatigue, sleep quality + duration, muscle soreness.
  - **Tier 2 (moderate):** HRV status vs baseline, perceived stress.
  - **Tier 3 (contextual):** Garmin Body Battery/Training Readiness, ACWR, days since last high-intensity session, mood/motivation.
- WHEN subjective and objective signals conflict → apply **conservative rule**: default to worse signal for high-intensity decisions.
- FLAG athletes whose rolling 7-day wellness scores decline >1 SD below personal baseline.
- IF subjective fatigue elevated >3 consecutive days → automatically suggest volume/intensity reduction.

-----

## 4.4 Nutrition for recovery

### Core principle

For concurrent strength and mountain endurance athletes, protein intake of **1.6–2.2 g/kg/day** distributed across ≥4 meals at **0.4–0.55 g/kg per meal** maximizes muscle protein synthesis. Carbohydrate needs scale dramatically with training volume. Altitude exposure increases caloric expenditure, fluid losses, iron demands, and preferential carbohydrate utilization.

### Evidence summary

**Protein dosing:**
- Morton et al. (2018, *BJSM*, 49 RCTs, n = 1,863): **1.62 g/kg/day** as inflection point; upper 95% CI = **~2.2 g/kg/day**.
- Schoenfeld & Aragon (2018): per-meal targets: **0.4 g/kg** × 4 meals = 1.6 g/kg minimum; **0.55 g/kg** × 4 = 2.2 g/kg upper.
- For 75 kg athlete: **30–41 g per meal** across 4 daily feedings.
- Leucine threshold for mTOR activation: **~2.5 g** in young adults (Witard et al., 2014), ≈ 20–25 g high-quality protein.
- Pre-sleep bolus: **40 g casein** increases overnight MPS (Res et al., 2012; Snijders et al., 2015).

**MPS refractory period:**
- MPS peaks at ~90–120 min, returns to baseline by ~180 min despite sustained amino acids ("muscle full" effect, Atherton & Smith, 2012).
- Resistance exercise extends sensitivity for **≥24 hours** (Burd et al., 2011).
- Space protein feedings **3–5 hours apart**.
- Areta et al. (2013): 4 × 20 g > 2 × 40 g > 8 × 10 g for MPS over 12 hours.

**Carbohydrate needs by context:**

| Training day | CHO target |
|---|---|
| Light (30 min) | 3–5 g/kg/day |
| Moderate (~1 hr strength or light touring) | 5–7 g/kg/day |
| High-volume (strength + 3–6 hr tour) | 7–10 g/kg/day |
| All-day mountain (>4 hr) | 8–12 g/kg/day |

- At altitude, CHO utilization increases: elite athletes increased from 6.5 to **9.3 g/kg/day** at 2,320 m (Koivisto et al., 2020).

**Glycogen replenishment:**
- Optimal: **1.0–1.2 g/kg/hour** high-GI CHO for first 4 hours post-exercise (Burke, van Loon & Hawley, 2017).
- IF CHO < 0.8 g/kg/hr → add **0.3–0.4 g/kg/hr protein** for enhanced glycogen storage.
- Full replenishment: **24–48 hours** with adequate daily CHO.
- 2% bodyweight dehydration can reduce glycogen storage by **25–30%**.

**Altitude-specific nutrition (2,000–4,000 m):**
- BMR increases during acclimatization. Add **200–600+ kcal/day**.
- Fluid: **3–5 L/day** (thirst unreliable at altitude).
- Iron: altitude drives **3–5-fold increase in erythropoiesis**. Ferritin target **>50 µg/L** (IOC). Athletes <35 µg/L: **210 mg elemental iron/day**; 35–100 µg/L: **105 mg/day** (Govus et al., 2015).
- Energy availability must not drop below **30 kcal/kg FFM/day** (RED-S threshold).

**Key micronutrients:**
- **Vitamin D:** target 25(OH)D > 40 ng/mL. Supplement 2,000–5,000 IU/day depending on status. Deficient (<20 ng/mL): 5,000–7,000 IU/day for 8 weeks.
- **Magnesium:** athletes need 10–20% above RDA (aim 400–420 mg/day men). Supplement 200–400 mg magnesium glycinate before bed (activates GABA, lowers cortisol, promotes SWS).
- **Omega-3:** **2–3 g/day combined EPA + DHA** (ISSN 2025 Position Stand: Jäger et al., DOI: 10.1080/15502783.2024.2441775). Reduces pro-inflammatory markers, attenuates CK/LDH. Omega-3 index target >8%, requiring ~13 weeks at 2 g/day. Effects take ≥2 weeks due to membrane incorporation.

### Application rule

- CALCULATE daily macros dynamically based on planned training:
  - Rest days: protein 1.6 g/kg, CHO 3–5 g/kg.
  - Moderate days: protein 1.8 g/kg, CHO 5–7 g/kg.
  - High-volume mountain days: protein 2.0–2.2 g/kg, CHO 8–10 g/kg.
- DISTRIBUTE protein across ≥4 meals, 3–5 hours apart, with 40 g slow-digesting protein before sleep.
- WHEN altitude > 2,000 m detected → add 200–600 kcal/day, increase fluid to 3–5 L, increase CHO by 1–2 g/kg, flag iron status check if not done within 8 weeks.
- DAILY supplement recommendation: vitamin D 2,000–5,000 IU with fat-containing meal, magnesium glycinate 200–400 mg before bed, omega-3s 2–3 g/day with meals.

### Key sources

- Morton RW et al. "Protein supplementation on resistance training gains." *Br J Sports Med*, 2018; 52: 376–384.
- Schoenfeld BJ, Aragon AA. "How much protein in a single meal?" *JISSN*, 2018; 15: 10.
- Burke LM, van Loon LJC, Hawley JA. "Postexercise muscle glycogen resynthesis." *J Appl Physiol*, 2017; 122: 1055–1067.
- Thomas DT, Erdman KA, Burke LM. "Nutrition and athletic performance." ACSM/AND/DC Joint Position, *Med Sci Sports Exerc*, 2016.
- Stellingwerff T et al. "Nutrition and altitude." *Sports Medicine*, 2019.
- Govus AD et al. "Pre-altitude serum ferritin and iron supplement dose." *PLOS ONE*, 2015.
- Atherton PJ, Smith K. "Muscle protein synthesis in response to nutrition and exercise." *J Physiol*, 2012.
- Areta JL et al. "Timing and distribution of protein ingestion." *J Physiol*, 2013; 591: 2319–2331.
- Jäger R et al. "ISSN Position Stand: Long-chain omega-3 polyunsaturated fatty acids." *JISSN*, 2025. DOI: 10.1080/15502783.2024.2441775.

-----

## 4.5 Deload and recovery weeks

### Core principle

Planned recovery weeks are not optional — they are the mechanism by which fatigue dissipates and supercompensation occurs. For concurrent athletes, deload every **3–4 weeks** with **40–50% volume reduction** while maintaining intensity ≥85% of working loads. Deload both modalities simultaneously.

### Evidence summary

**Supercompensation physiology:** Yakovlev (1949–1959) + Selye's GAS. Zatsiorsky's fitness-fatigue model: readiness = fitness − fatigue. Deloads allow fatigue to dissipate while fitness remains elevated.

**Deload frequency recommendations:**

| Population | Frequency |
|---|---|
| Beginners (<1 year) | Every 8–12 weeks |
| Intermediate (1–3 years) | Every 6–8 weeks |
| Advanced (3+ years) | Every 4–6 weeks |
| Concurrent strength + endurance | Every 3–4 weeks |
| Athletes in caloric deficit | Subtract 2 weeks from standard |

**Deload structure (Bosquet et al., 2007, 27 studies):** volume reduction of **41–60%** without modifying intensity or frequency = largest ES (0.72 ± 0.36, p < 0.001). Bell et al. (2025): maintain intensity ≥85% 1RM during volume reduction.

**Issurin's residual effects:** aerobic endurance **30 ± 5 days**, maximal strength **30 ± 5 days** — 1-week deload poses zero risk to these qualities.

**Concurrent training deloads:**
- Deload BOTH modalities in the same week.
- Strength: maintain exercises and loads, reduce sets 40–50%, increase RIR by 2–3.
- Endurance: reduce volume 40–60%, maintain Z1–2 intensity, eliminate intervals and heavy pack carries.
- Total weekly TRIMP/TSS → ~50% of normal.

**Mountain-specific recovery (Uphill Athlete model):** Recovery weeks every 3–4 weeks, volume ~50%, easy aerobic base maintained. ME workouts eliminated entirely (very high recovery demand). Template: 2 light gym sessions at 50% volume with maintained load, 1–2 easy Z1–2 sessions (30–45 min, flat/gentle, no pack), 1–2 complete rest or mobility days. Total vertical/distance ~40–50% of normal.

**Reactive deload triggers (require ≥3 converging):**
1. HRV below SWC for >3 days
2. Resting HR elevated ≥3–5 bpm above baseline for ≥3 days
3. Sleep efficiency <85% for >3 days
4. Missed reps or RPE elevated ≥1.5 points for >2 sessions
5. Persistent soreness >72 hours
6. Self-reported motivation <3/5 for ≥3 days
7. Elevated life stress
8. ACWR >1.5

### Application rule

- SCHEDULE deload every 4 weeks for concurrent athletes (3:1 ratio); every 6 weeks for strength-only beginners.
- ADJUST: caloric deficit → subtract 2 weeks from standard.
- MAINTAIN running trigger count across 8 indicators; when ≥3 converge → immediate deload.
- DURING deload: reduce strength volume 40–50% at ≥85% load; reduce endurance volume 40–60% at Z1–2 only; eliminate all intervals; deload BOTH modalities; maintain frequency.
- POST-DELOAD: resume at previous intensity but ~90% of pre-deload volume in first week.
- BEFORE major mountain objective → final 1–2 weeks follow taper protocol.

-----

## 4.6 Training during illness and return-to-training protocols

### Core principle

The traditional "neck check" heuristic (above-neck symptoms = train light, below-neck = rest) **lacks supporting scientific evidence and may be hazardous** (Harju et al., 2022) because cardiogenic viruses can present with only upper respiratory symptoms. For mountain athletes, illness carries additional safety risk: even mild illness at altitude compounds immune stress and impairs judgment in avalanche terrain and during paragliding launches. The conservative approach is always appropriate.

### Evidence summary

- **Harju et al. (2022, *Sports Medicine*):** "The neck check lacks supporting scientific evidence, may even be hazardous, and should be abandoned." Proposed instead a symptom-severity and duration-based decision framework.
- **Walsh (2018, *J Sports Sciences*):** Exercise at moderate intensity has minimal effect on respiratory infection severity or duration. However, high-intensity exercise during acute illness is immunosuppressive and may prolong recovery or cause complications.
- **Extreme exercise and infection risk:** Martin et al. (2009): marathon runners have **2–6× higher URI risk** in the 2 weeks post-race. The "open window" of immune suppression lasts **3–72 hours** after exhaustive exercise.
- **Myocarditis risk:** While rare (~1–3% of acute viral infections), exercising during febrile illness increases the risk of viral myocarditis. This is the primary danger of the neck check — athletes may exercise through early myocarditis presenting as mild throat/nasal symptoms.
- **Training during illness accelerates glycogen depletion**, increases cortisol, and impairs sleep quality — all of which slow both illness recovery and training adaptation.

**Post-COVID return to training (2022 ACC Expert Consensus Decision Pathway, Gluckman et al., *JACC*):**
- Asymptomatic infection: **3 days of exercise abstinence**, no cardiac testing required.
- Cardiopulmonary symptoms (chest pain, dyspnea, palpitations, syncope): "triad testing" — ECG, troponin, echocardiogram. Routine cardiac MRI no longer recommended.
- 7-day graduated return protocol:
  - Days 1–2: <70% max HR, low-intensity
  - Days 3–4: moderate intensity
  - Days 5–6: approaching normal training
  - Day 7+: full return if asymptomatic

### Application rule

**During illness:**
- **Any fever >38°C** → complete rest. No training of any kind.
- **Systemic symptoms** (body aches, chills, fatigue, GI disturbance) → complete rest.
- **Below-neck symptoms** (chest congestion, productive cough, wheezing) → complete rest. Do not exercise.
- **Isolated mild nasal congestion only** (no fever, no fatigue, no body aches) → light Zone 1 activity permitted (30 min max, indoor, flat). No mountain activity.
- **NO mountain-specific activity** (ski touring, splitboarding, hike-and-fly, resort snowboarding) during any illness. Impaired judgment + altitude + cold + technical terrain = unacceptable safety risk.
- IF symptoms worsen during light activity → stop immediately, rest for remainder of day + next day.

**Return to training after illness:**
- WAIT until **2–3 days completely symptom-free** before resuming structured training.
- FOR mild URI (nasal congestion, sore throat, no fever, ≤5 days duration):
  - Day 1 back: 50% volume, Zone 1 only, 30–45 min max.
  - Day 2–3: 60–75% volume, add moderate intensity if feeling well.
  - Day 4+: normal training if recovery markers are within baseline.
- FOR moderate illness (fever, 3–7 days duration):
  - Days 1–3 back: Zone 1 only, 30–60 min, 50% normal volume.
  - Days 4–7: gradual ramp to 75% volume, add moderate intensity.
  - Day 8+: normal training if HRV and subjective markers have returned to baseline.
- FOR severe illness or hospitalization (>7 days, significant symptoms):
  - Week 1 back: light activity only, 30 min/day, Zone 1.
  - Week 2: 50% volume, reintroduce strength at 50% load.
  - Week 3+: gradual ramp toward normal. Medical clearance recommended before high-intensity work.
- FOR post-COVID with cardiopulmonary symptoms → follow ACC graduated return protocol: 3 days abstinence, triad testing if symptoms present, 7-day graded return.

**Plan-level adjustments:**
- ILLNESS should NOT trigger a "catch-up" mentality — missed sessions are gone. Resume the plan where it would naturally be, reduced by one tier of volume.
- IF illness occurs during week 3 of a 3:1 mesocycle → treat the illness days as the deload; do not add another deload week.
- IF illness occurs during week 1–2 → resume at week 1 intensity/volume after recovery.
- MONITOR HRV closely for 7–14 days post-illness. Expect suppressed values; do not return to high-intensity training until HRV returns to within SWC of baseline.

### Key sources

- Harju V et al. "Respiratory viral infections in athletes: many unanswered questions." *Sports Medicine*, 2022; 52: 2023–2035. DOI: 10.1007/s40279-022-01660-9.
- Walsh NP. "Recommendations to maintain immune health in athletes." *Eur J Sport Sci*, 2018; 18(6): 820–831.
- Gluckman TJ et al. "2022 ACC Expert Consensus Decision Pathway on Cardiovascular Sequelae of COVID-19 in Adults." *JACC*, 2022; 79(17): 1717–1756.
- Martin SA, Pence BD, Woods JA. "Exercise and respiratory tract viral infections." *Exerc Sport Sci Rev*, 2009; 37(4): 157–164.
- Simpson RJ et al. "Exercise and the regulation of immune functions." *Progress in Molecular Biology and Translational Science*, 2015; 135: 355–380.

### Cross-references

- → Integration Rule #22 (conservative rule for illness)
- → Periodization §5 (autoregulation accommodates illness-related disruptions)
- → Periodization §5.6 (schedule disruption management)
- → Recovery §1 (HRV monitoring post-illness)

-----

## 4.7 Training during caloric deficit

### Core principle

Energy deficit impairs lean mass gains but **not strength gains** during resistance training (Murphy & Koehler, 2022). The critical threshold is approximately **~500 kcal/day** — larger deficits prevented lean mass gains entirely. Protein intake of **2.0–2.4 g/kg/day** is the single most important nutritional lever for preserving muscle during deficit. Weight loss phases should never coincide with peak training or competition periods, and the concurrent training interference effect is amplified in energy deficit.

### Evidence summary

- **Murphy & Koehler (2022, *Scand J Med Sci Sports*):** Meta-analysis and meta-regression: energy deficits impair lean mass gains (SMD = −0.57 vs surplus) but **strength gains are preserved** regardless of energy status (SMD = −0.05, NS). The ~500 kcal/day threshold was the critical inflection — deficits beyond this prevented lean mass gains entirely.
- **Helms et al. (2014) natural bodybuilding review:** Recommended **0.5–1.0% bodyweight loss per week** for lean mass preservation. Slower rates (0.5–0.7%/week) consistently outperformed faster cuts.
- **Mero et al. (2010):** 4-week diet intervention: group losing ~0.7% BW/week lost **21% less lean mass** than group losing ~1.4% BW/week.
- **Protein requirement during deficit:** Increases above eucaloric needs. Jäger et al. (2017, ISSN Position Stand): **1.6–2.2 g/kg/day** for maintenance; **2.3–3.1 g/kg LBM/day** during caloric restriction for athletes.
- **IOC 2023 REDs Consensus (Mountjoy et al.):** Energy availability below **30 kcal/kg FFM/day** = threshold for physiological disruption including thyroid suppression, hormonal disturbance, and impaired bone health. The REDs CAT Version 2 screening tool now explicitly recognizes REDs in males.
- **Concurrent training during deficit:** The interference effect is amplified because glycogen-depleted states enhance AMPK activation, directly inhibiting mTOR. This means the already-small interference effect becomes more relevant during cutting phases. Prioritize strength training and reduce endurance volume/intensity.

### Application rule

- MAXIMUM deficit: **~500 kcal/day** (or ~0.5–0.7% bodyweight loss per week for 75 kg athlete = ~375–525 g/week).
- PROTEIN during deficit: **2.0–2.4 g/kg/day**, distributed across ≥4 meals. This is higher than eucaloric recommendations.
- CARBOHYDRATE: maintain ≥3 g/kg/day minimum even during deficit to support training quality. Reduce fat preferentially.
- NEVER schedule deficit phases during:
  - Peak in-season training (ski touring season, hike-and-fly season)
  - Planned multi-day mountain objectives
  - Planned altitude exposure
  - High-volume endurance blocks
- OPTIMAL timing for deficit: early off-season (May–June for winter athlete) or transition phases.
- TRAINING during deficit:
  - MAINTAIN strength training intensity (≥80% 1RM) — this is the non-negotiable.
  - REDUCE training volume by ~20–30% from normal.
  - REDUCE high-intensity endurance sessions to 1/week maximum.
  - PRIORITIZE strength training over endurance if time-constrained — strength preserves muscle mass during deficit.
  - DELOAD more frequently: subtract 2 weeks from standard deload interval (e.g., 3:1 → 2:1).
- ENERGY AVAILABILITY: ensure ≥30 kcal/kg FFM/day. For 75 kg male at ~12% body fat (~66 kg FFM) = minimum ~1,980 kcal/day. Flag if estimated daily intake drops below this.
- MONITOR: weekly weigh-ins (7-day average), monthly skinfold or waist measurements. IF rate exceeds 1% BW/week → reduce deficit. IF strength declines >5% across 2+ sessions → exit deficit and return to maintenance.
- SUPPLEMENT: creatine monohydrate 3–5 g/day should be maintained during deficit (preserves intracellular water and may attenuate muscle loss).

### Key sources

- Murphy C, Koehler K. "Energy deficiency impairs resistance training gains in lean mass but not strength: a meta-analysis and meta-regression." *Scand J Med Sci Sports*, 2022; 32(1): 125–137. DOI: 10.1111/sms.14075.
- Helms ER et al. "Evidence-based recommendations for natural bodybuilding contest preparation." *JISSN*, 2014; 11: 20.
- Mero AA et al. "Moderate energy restriction with high protein diet results in healthier outcome in women." *J Int Soc Sports Nutr*, 2010; 7: 4.
- Mountjoy M et al. "2023 International Olympic Committee's (IOC) consensus statement on Relative Energy Deficiency in Sport (REDs)." *BJSM*, 2023; 57(17): 1073–1097. DOI: 10.1136/bjsports-2023-106994.
- Jäger R et al. "ISSN Position Stand: protein and exercise." *JISSN*, 2017; 14: 20.

### Cross-references

- → Integration Rule #24 (energy deficit protocol)
- → Biomarkers §1E (fT3 monitoring for RED-S risk during deficit)
- → Strength §1.2 (volume reduction during deficit)
- → Periodization §1 (deficit timing within annual plan)



-----

# DOMAIN 5: PERIODIZATION FOR THE RECREATIONAL MOUNTAIN ATHLETE

## 5.1 Annual planning (macrocycle)

### Core principle

The annual plan follows a **modified bi-cycle model** — two distinct macrocycles (winter/ski touring and summer/hike-and-fly), each containing general preparation, specific preparation, competition/performance, and transition phases. Volume and intensity maintain an inverse relationship across phases. Endurance follows polarized distribution; strength sequences through accumulation → intensification → maintenance across each macrocycle. The 2025 ACSM Position Stand confirmed that periodization is the organizational framework for progressive overload, not a magic structure in itself — missing a phase transition is not catastrophic as long as progressive overload continues.

### Evidence summary

**Classic periodization (Matveyev, 1977; Bompa & Buzzichelli, 2019):** Preparation phase = **60–75%** of macrocycle, competition/performance = **20–30%**, transition = **3–5 weeks**. Within preparation, GPP > 50% of that time, SPP the remainder. Volume decreases ~32 ± 15% from GPP to peaking. Bompa's six strength phases: anatomical adaptation → hypertrophy → maximum strength → sport-specific conversion → maintenance → taper.

**Block periodization (Issurin, 2008, 2010):** Concentrated 2–4 week blocks focusing on minimal fitness qualities sequentially. A-T-R (Accumulation → Transmutation → Realization) forms a "mini annual plan" repeatable multiple times per year. Residual training effects govern sequencing (see §3.3 for full table).

**Polarized model integration:** Optimal ~75–80% Z1, ~5% Z2, ~15–20% Z3 (Seiler, 2010; Stöggl & Sperlich, 2014). Two high-intensity sessions/week suffice for recreational athletes. Seiler's hierarchy: total volume most important, then intensity distribution, then periodization details.

**Undulating periodization:** Harries et al. (2015), Grgic et al. (2017): **no significant difference** between models when volume equated (Cohen's d = −0.02 for hypertrophy). DUP useful for maintaining multiple qualities in-season.

**2025 ACSM Position Stand (Currier et al.):** Synthesized 137 systematic reviews and >30,000 participants. Key findings relevant to periodization: (1) periodization was **not significantly superior** to non-periodized programs when progressive overload was applied; (2) the choice of periodization model matters less than consistent progressive overload; (3) training to momentary failure did not consistently improve outcomes beyond training at 1–3 RIR. This means the AI should treat the periodization structure as a useful organizing framework but not panic when phases are disrupted — the priority is maintaining progressive overload through whatever structure is available.

### Application rule

**Annual calendar for winter mountain athlete:**

| Month | Phase | Strength emphasis | Endurance emphasis |
|---|---|---|---|
| May | Transition (2–3 wk) | Active recovery, mobility, light general | Easy aerobic, unstructured |
| Jun–Jul | Summer GPP (8 wk) | Hypertrophy → max strength (3×/wk) | Aerobic base: high volume Z1–2 hiking/cycling |
| Aug–Sep | Summer SPP (6–8 wk) | Muscular endurance + maintenance (2×/wk) | Threshold work, weighted hikes, hike-and-fly days |
| Oct | Transition (2–3 wk) | Deload → begin ski-specific prep | Brief recovery, begin eccentric leg emphasis |
| Nov–Dec | Winter GPP (8 wk) | Max strength (2–3×/wk), eccentric leg work | Aerobic base via ski touring, Z1–2 |
| Jan–Feb | Winter SPP (6–8 wk) | Maintenance (1–2×/wk) | Peak touring volume, muscular endurance |
| Mar–Apr | Performance + late season | Maintenance (1–2×/wk) | Taper before big objectives, touring IS training |

**Priority-shifting rule:** When endurance is primary (in-season) → reduce strength to **1–2 maintenance sessions/week** at 75–85% 1RM, 2–3 × 3–6 reps. When strength is prioritized (off-season GPP) → limit high-intensity endurance to **2 sessions/week**, keep remaining at Zone 1. Program recovery weeks every 3rd or 4th week, volume ~40–50%. For athletes under high life stress → default to 2:1 loading.

### Key sources

- Matveyev LP. *Fundamentals of Sports Training*, 1977.
- Bompa TO, Buzzichelli C. *Periodization: Theory and Methodology of Training*, 6th ed., 2019.
- Issurin VB. "Block periodization." *J Sports Med Phys Fitness*, 2008.
- Issurin VB. "New horizons for periodization." *Sports Medicine*, 2010.
- Seiler S. "What is best practice for training intensity distribution?" *Int J Sports Physiol Perform*, 2010.
- House S, Johnston S. *Training for the Uphill Athlete*, 2019.
- Currier BS et al. "ACSM Position Stand: Resistance Training Prescription." *MSSE*, 2025.

-----

## 5.2 Mesocycle design

### Core principle

Each mesocycle follows the **A-T-R** sequence. Accumulation builds work capacity through high volume at moderate intensity; intensification converts to sport-specific fitness; realization sheds fatigue for peak performance. Block duration typically **3–6 weeks**, with 3+1 (3 weeks loading, 1 week deload) as the default.

### Evidence summary

**Strength training parameters by phase:**

| Phase | Sets × Reps | Load (%1RM) | Rest | Weekly sets/muscle | Duration |
|---|---|---|---|---|---|
| Anatomical adaptation | 2–3 × 12–15 | 40–60% | 60–90s | 8–12 | 4–6 wk |
| Hypertrophy (accumulation) | 3–5 × 6–12 | 67–85% | 60–120s | 12–20+ | 3–6 wk |
| Max strength (intensification) | 3–5 × 1–6 | 80–95% | 3–5 min | 6–12 | 3–4 wk |
| Power (realization) | 3–5 × 1–5 | 85–100% / 30–60% | 3–5 min | 4–8 | 1–3 wk |
| Muscular endurance | 2–3 × 15–30+ | 30–60% | <90s | Variable | 4–8 wk |
| Maintenance (in-season) | 2–3 × 3–6 | 75–85% | 2–3 min | 4–8 | Duration of season |

**Endurance training parameters by phase:**

| Phase | Duration | Z1–2 volume | HI sessions | Key sessions |
|---|---|---|---|---|
| Base (accumulation) | 8–16 wk | 80–90% | 0–1/wk | Long slow distance, easy touring |
| Threshold/build (intensification) | 4–8 wk | 75–80% | 2–3/wk | 3–4 × 8–15 min threshold, weighted uphill |
| Peak/realization | 1–3 wk | Reduced total | Maintain some | Race-specific intervals |

**Optimal block length:** 4-week mesocycle (3+1) most widely used. Bell et al. (2024): average deload every 5.6 ± 2.3 weeks. Rønnestad et al. (2012, 2014) used 4-week blocks for superior VO2max and power. For recreational concurrent athletes under stress → **shorter 3-week blocks (2+1)** may be preferable.

### Application rule

- DEFAULT to 4-week blocks (3+1).
- IF caloric deficit, high work/life stress, or high concurrent endurance volume → switch to 3-week blocks (2+1).
- USE 5–6 week blocks only for novice trainees in pure strength-focus.
- OFF-SEASON GPP sequencing: anatomical adaptation (4 wk) → hypertrophy (4–6 wk) → max strength (4 wk) → sport-specific conversion (4 wk).
- IN-SEASON: single maintenance block repeating until season ends.
- BASE BUILDING must consume ≥8 weeks before threshold work introduced.
- MAINTAIN 80/20 intensity distribution even during intensification.
- DELOAD DECISION: pre-plan every 4th week, but allow autoregulation to shift ±1 week based on readiness markers.

-----

## 5.3 Microcycle templates

### Core principle

Concurrent strength and endurance creates interference primarily affecting **power and explosive strength** (ES −0.28 to −0.55), with minimal impact on maximal strength/hypertrophy in recreational athletes. Mitigation: separate sessions by ≥6 hours, strength before endurance when same-day, favor cycling/skiing over running.

### Application rule — Microcycle templates

**Template A — 4-day week (minimum effective dose, high stress periods):**

| Day | Session | Details |
|---|---|---|
| Monday | Strength A (full body) | Evening gym: squat, hinge, press, pull, core |
| Tuesday | Endurance 1 (Z1–2) | 60–90 min bike/hike/ski |
| Wednesday | Rest or active recovery | Mobility, easy walk |
| Thursday | Strength B (full body) | Evening gym: deadlift, lunge, OHP, row |
| Friday | Rest | |
| Saturday | Endurance 2 (long) | 2–4 hr ski tour or hike |
| Sunday | Rest | |

**Template B1 — 5-day, strength-priority (off-season):**

| Day | Session | Details |
|---|---|---|
| Monday | Strength A (lower) | Squat, deadlift, lunges, core |
| Tuesday | Endurance 1 (Z2, 60–90 min) | Bike/stair climber/easy hike |
| Wednesday | Strength B (upper) | Press, pull, rows, carries |
| Thursday | Rest | |
| Friday | Strength C (full body power) | Olympic variations, plyometrics |
| Saturday | Endurance 2 (long Z1–2) | 2–4 hr mountain day |
| Sunday | Rest | |

**Template B2 — 5-day, endurance-priority (in-season):**

| Day | Session | Details |
|---|---|---|
| Monday | Strength A (full body maintenance) | 2–3 sets heavy compounds, 45 min |
| Tuesday | Endurance 1 (Z2, 60–90 min) | Easy bike/hike |
| Wednesday | Endurance 2 (intervals/threshold) | Z3–4 work, 45–60 min |
| Thursday | Strength B (full body maintenance) | 2–3 sets, emphasis weak links |
| Friday | Rest | |
| Saturday | Endurance 3 (long mountain day) | Ski tour or hike-and-fly, 3–6 hr |
| Sunday | Rest | |

**Template C — 6-day (advanced, high training capacity):**

| Day | Session | Details |
|---|---|---|
| Monday | Strength A (lower) | Heavy squats, deadlift, step-ups, core |
| Tuesday | Endurance 1 (Z2, 60–90 min) | Bike/stair climber |
| Wednesday | Strength B (upper) | Press, pull, rows, carries |
| Thursday | Endurance 2 (intervals) | Threshold intervals, 45–60 min |
| Friday | Strength C (full body/power) | Power cleans, plyos, sport-specific |
| Saturday | Endurance 3 (long) | 3–5 hr ski tour or mountain day |
| Sunday | Rest | |

**Template D — Weekend mountain day integration (in-season default):**

| Day | Session | Details |
|---|---|---|
| Monday | Strength A (full body) | Allow 48 hr from Saturday |
| Tuesday | Rest or easy active recovery | |
| Wednesday | Strength B (full body) | |
| Thursday | Endurance (moderate, 45–60 min) | Z2–3 bike/stair climber |
| Friday | Rest or very light prep | |
| Saturday | Mountain day | Long tour or hike-and-fly = endurance session |
| Sunday | Rest | |

**Selection rules:**
- DEFAULT to Template B during preparation phases.
- SWITCH to Template D when athlete has weekly mountain objectives.
- USE Template A during deload weeks, high-stress periods, or transition phases.
- USE Template C only for athletes with >2 years training history who demonstrate good recovery markers.
- Mountain days ALWAYS count as endurance sessions — do NOT add gym-based endurance on top.
- AVOID scheduling heavy lower-body strength immediately after long/hard mountain days.
- ENSURE ≥1 full rest or active recovery day weekly.
- ADJUST microcycle intensity dynamically based on HRV, sleep, and soreness.

-----

## 5.4 Tapering for mountain objectives

### Core principle

A taper is a progressive nonlinear reduction of training volume while maintaining intensity and frequency. For mountain athletes, multi-day objectives require a modified taper that preserves glycogen stores, maintains terrain-specific patterns, and prioritizes arriving well-rested.

### Evidence summary

**Landmark taper framework (Mujika & Padilla, 2003):** Mean performance improvement **~3%** (range 0.5–6.0%). Three cardinal rules: **reduce volume up to 60–90%**, **maintain intensity** (most critical variable), **reduce frequency no more than 20%**.

**Bosquet et al. (2007), 27 studies:** **Exponential taper** over **2 weeks** with **41–60% volume reduction**, no intensity change, no frequency change = largest ES (0.72 ± 0.36). Wang et al. (2023, *PLOS One*, 14 studies): **8–14 days** optimal duration (SMD = −1.47).

**Multi-day mountain objective taper vs single-day:**

| Timing | Strength | Endurance | Other |
|---|---|---|---|
| 3–4 weeks out | Normal; optional overreach +10–20% | Normal; include simulation days | Final hard block |
| 2 weeks out | Reduce volume ~40–50%; maintain ≥85% 1RM; drop accessories | Reduce ~60%; maintain interval intensity; back-to-back simulation | Taper begins |
| 1 week out | One brief session early week, then cease | ~30–40% volume; short sessions, maintain terrain specificity | Sleep, nutrition, glycogen loading |
| 2 days out | None | Active recovery only | Final gear check |
| 1 day out | None | Brief opener: 20–30 min easy + 3–4 short intensity bursts | Pre-load CHO |

### Application rule

- TAPER only for "A" objectives (most important goals).
- FOR regular weekend touring → no taper; ensure lighter Friday training.
- FOR "B" objectives → reduce volume ~30% for preceding 5–7 days.
- CLASSIFY objectives as A/B/C based on duration, altitude gain, and athlete-stated importance.

-----

## 5.5 Autoregulation at the plan level

### Core principle

Autoregulation uses HRV trends, subjective indicators, RPE, and performance trends to dynamically adjust training. The strongest signal comes from **triangulating multiple markers**. Implement a three-tier response: micro-adjustments, deload insertion, and plan restructuring.

### Application rule — Three-tier decision framework

**Tier 1 — Micro-adjustment (10–15% volume reduction for 2–3 sessions):**
- TRIGGER: any ONE of:
  - HRV 7-day average dips below SWC for 1–2 days
  - RPE inflated by 1 point for equivalent workload
  - First-rep velocity 90–95% of 30-day average
  - ACWR approaching 1.3
  - Single night poor sleep
- ACTION: reduce working sets by 1–2/exercise, swap high-intensity for moderate, add 10 min mobility.

**Tier 2 — Deload insertion (40–60% volume reduction for 5–7 days):**
- TRIGGER: TWO OR MORE persisting >5–7 days:
  - HRV below SWC for full week
  - HRV-CV trending upward over 2+ weeks
  - RPE inflated ≥2 points consistently
  - Velocity <90% across multiple sessions
  - Performance decrement >3–5% in key lifts
  - Monotony >2.0
  - Persistent soreness, sleep disruption, or motivation loss
- ACTION: reduce volume 40–60%, maintain intensity and frequency, drop accessories, increase RIR by 2–3.

**Tier 3 — Plan restructuring (complete replanning):**
- TRIGGER: multiple red flags persisting >2–3 weeks despite a deload:
  - Declining HRV mean with declining CV (parasympathetic saturation)
  - Performance decrements >5–10% not recovering after deload
  - Persistent RPE elevation despite reduced loads
  - Recurrent illness
  - Sustained motivation loss
- ACTION: 1–2 weeks complete rest or very light active recovery, then rebuild at 40–50% prior volume. Reassess non-training stressors. Consider medical screening.

**Daily readiness scoring algorithm:**

Composite score (0–100): **HRV component (40%)** — morning rMSSD vs. 7-day average and SWC bands, plus CV trend. **Subjective wellness (30%)** — sleep quality, energy, soreness, stress (1–5 scales). **Performance/load component (30%)** — previous session RPE vs. intended, ACWR, velocity if available.

- Score >75 + ACWR <1.3 → GREEN: execute planned session.
- Score 50–75 OR ACWR 1.3–1.5 → AMBER: reduce volume 10–20%, maintain intensity on primary lifts.
- Score <50 OR ACWR >1.5 → RED: replace with recovery session; if red 3+ consecutive days → trigger deload.

**Combined pre-planned + reactive approach:** Pre-schedule deload every 4th week as default. Allow autoregulation to shift forward (week 3 if markers deteriorate) or backward (week 5 if strong). No athlete beyond 6 weeks without deload during progressive loading.

**Recreational athlete considerations:** Non-training stressors (work, family, travel, altitude) often exceed training as recovery-limiting factors. HRV captures total allostatic load — a feature, not a bug. Weight subjective wellness markers more heavily during known high-stress periods.

-----

## 5.6 Schedule disruption management

### Core principle

Schedule disruptions — missed sessions due to work, travel, illness, unexpected mountain weather opportunities, or personal obligations — are the **most common real-world challenge** for recreational athletes. The AI must handle them gracefully. The cardinal rule is **shift, don't skip**: consolidate the highest-value training elements into available sessions rather than attempting to replicate missed sessions, doubling up, or triggering guilt-driven catch-up training. Detraining is negligible for 1 week, minimal for 2 weeks, and only begins to meaningfully erode strength after 3–4 weeks.

### Evidence summary

**Detraining timelines (composite from Bosquet et al. 2013, Mujika & Padilla 2000/2001, Chen et al. 2022):**

| Duration off | Strength impact | Endurance impact | Practical consequence |
|---|---|---|---|
| 1–3 days | None | None | Resume exactly where you left off |
| 4–7 days | None measurable | None measurable | Resume at full intensity, 90% volume |
| 8–14 days | Minimal (~1–3%) | VO2max begins to decline 3–6% | Resume at full intensity, 80% volume |
| 15–21 days | Minor (~3–5%) | VO2max decline 5–10% | Resume at full intensity, 70% volume, rebuild over 2 weeks |
| 22–28 days | Moderate (~5–8%) | VO2max decline 8–15% | Treat as return-to-training; 3-week ramp |
| >4 weeks | Significant (7–15%) | VO2max decline 15–20%+ | Extended rebuild; 4–6 week ramp |

- **Key insight from Bickel et al. (2011):** Even 1/9th of training volume maintained all strength gains for 32 weeks. A single well-executed compound session preserves vastly more than zero sessions.
- **Residual training effects (Issurin, 2010):** Aerobic endurance persists ~30 days and maximal strength ~30 days after last dedicated session. A missed week is physiologically insignificant.
- **Psychological impact:** The greater risk from schedule disruptions is not detraining but motivational damage. Consistency research shows that perceived failure to follow a plan is the strongest predictor of adherence collapse. The AI must frame disruptions as normal, expected, and manageable.

### Application rule

**Single session missed:**
- DO NOT attempt to make it up. The plan continues as if it didn't happen.
- IF the missed session was the highest-priority session for the current phase (e.g., the only heavy strength session of the week during maintenance) → shift it to the nearest available slot, even if it means training on a planned rest day once.
- DO NOT double up sessions on the same day unless they would naturally be paired (e.g., AM strength + PM easy endurance with ≥6h gap).

**2–3 sessions missed (partial week disruption):**
- IDENTIFY the single highest-value session for the current phase and ensure it gets done.
- DURING strength-priority phases → the one non-negotiable is heavy compound strength.
- DURING endurance-priority phases → the one non-negotiable is the long endurance session.
- ELIMINATE all accessory/isolation work first. Keep only compound movements.
- DO NOT add volume to remaining sessions to "compensate." Maintain prescribed volume per session.

**Full week missed (7 days off):**
- Resume at **full intensity, 90% of pre-break volume** in the first week back.
- No fitness has been meaningfully lost. No ramp-up needed.
- Continue the mesocycle from where the plan naturally falls, not from where you left off.
- IF the missed week was scheduled as a deload → it counts as the deload. Resume build phase.
- IF the missed week was a build week → resume at the same week's prescription (don't repeat the previous week).

**2 weeks missed:**
- Resume at **full intensity, 80% volume** in week 1 back, 90% in week 2, full volume in week 3.
- Expect DOMS in the first 2–3 sessions — this is normal and does not indicate injury or excessive loading.
- Schedule a deload at the end of the first 3-week build back (i.e., 3 weeks training → 1 week deload before resuming normal programming).

**3–4 weeks missed:**
- Resume at **full intensity, 70% volume** in week 1.
- Week 2: 80% volume. Week 3: 90% volume. Week 4: deload.
- AFTER the deload → resume normal programming at the beginning of the current phase.
- For endurance, expect VO2max to have declined 5–15%. It will recover faster than it was originally built.
- ENSURE at least 2 weeks of training before scheduling any "A" mountain objectives.

**>4 weeks missed (extended break):**
- Treat as a return-to-training event.
- Week 1: 50% volume, moderate intensity (RPE 6–7 strength, Zone 1–2 endurance only).
- Week 2: 60% volume, increase intensity to RPE 7–8.
- Week 3: 70% volume, normal intensity.
- Week 4: 80% volume. Week 5: 90%. Week 6+: full programming.
- DELOAD after the first 3 build weeks.
- NOTE: "muscle memory" (myonuclear retention) means previously trained muscle regains size faster than naive muscle. Strength regains take approximately **half the detraining duration**.

**Unplanned mountain opportunity (e.g., perfect weather window for a big objective):**
- ALWAYS take the mountain opportunity. Sport-specific training IS training.
- Retrospectively classify the session by HR/RPE/vertical and integrate into the weekly load calculation.
- REDUCE or eliminate the remaining week's planned endurance work — the mountain day replaced it.
- IF the opportunity replaces a planned strength session → schedule a brief (20–30 min) maintenance strength session within the next 3–4 days.
- DO NOT attempt to "make up" the disrupted week's plan. Adjust forward.

**Travel disruptions (business trips, holidays):**
- PRESCRIBE bodyweight or hotel-gym minimum effective dose sessions: push-ups, single-leg squats, pull-ups (door-frame bar), plank. 2–3 sets each, 3×/week, 15–20 minutes.
- IF gym access is available but limited → one full-body compound session preserves all strength for up to 2 weeks.
- MAINTAIN daily Zone 1 aerobic if possible (walking, hotel stairs, easy running). Even 20–30 minutes preserves aerobic base.

### Key sources

- Bosquet L et al. "Effect of training cessation on muscular performance." *Scand J Med Sci Sports*, 2013; 23: e140–149.
- Mujika I, Padilla S. "Detraining." *Sports Med*, 2000; 30(2): 79–87 and 30(3): 145–154.
- Bickel CS, Cross JM, Bamman MM. "Exercise dosing to retain resistance training adaptations." *Med Sci Sports Exerc*, 2011.
- Issurin VB. "New horizons for the methodology of training." *Sports Medicine*, 2010.
- Chen YT et al. "Two weeks of detraining reduces cardiopulmonary function and muscular fitness in endurance athletes." *Eur J Sport Sci*, 2022. DOI: 10.1080/17461391.2021.1880647.
- Spiering BA et al. "Maintaining physical performance: minimal dose." *JSCR*, 2021.

### Cross-references

- → Integration Rule #21 (shift, don't skip)
- → Concurrent Training §4 (minimum effective dose for strength maintenance)
- → Periodization §5 (autoregulation accommodates disruptions)
- → Recovery §4.6 (illness-specific return protocols)



-----

# DOMAIN 6: BIOMARKER INTEGRATION

## 6.1 Blood markers relevant to training adaptation

### 6.1A Ferritin and iron status

#### Core principle

Iron is the rate-limiting mineral for oxygen transport and aerobic enzyme function. Athletes require ferritin substantially above the clinical "normal" floor of 12–15 ng/mL because even iron depletion without anemia (IDNA) measurably impairs VO2max adaptation. Optimal ferritin for athletes: **50–100 ng/mL** for males. Minimum performance threshold: **35–40 ng/mL**.

#### Evidence summary

- **IDNA diagnostic criteria:** Ferritin <30 ng/mL with transferrin saturation <20% and normal hemoglobin (>13.5 g/dL males).
- **Performance impact of IDNA:** Burden et al. (2015) meta-analysis, 17 studies: iron supplementation in IDNA improved VO2max with **Hedges' g of 0.61** (moderate effect, p<0.001). Hinton et al. (2000): IDNA impairs aerobic training adaptation even when hemoglobin is normal.
- **Hepcidin dynamics:** Peeling et al. (2014): athletes with ferritin 30–50 ng/mL experience post-exercise hepcidin spikes blocking absorption. Athletes below 30 ng/mL paradoxically show suppressed hepcidin, favoring absorption.
- **Pre-altitude requirement:** Ferritin ≥40 ng/mL before altitude exposure (Sim et al., 2019).

**Supplementation protocols:**
- Oral: 100 mg elemental iron/day (ferrous sulfate or iron bisglycinate) for 6–8 weeks when ferritin <35 ng/mL.
- Morning dosing preferred, ideally within 30 min after exercise when hepcidin is still low.
- Alternate-day dosing: comparable efficacy with fewer GI effects (McCormick et al., 2020).
- IV iron consideration: when oral fails to raise ferritin above 35 ng/mL after 6–8 weeks.

#### Application rule

- FLAG ferritin < 35 ng/mL → dietary intervention + supplementation.
- FLAG ferritin < 20 ng/mL → aggressive supplementation with possible training load reduction.
- FOR mountain athletes planning altitude (ski touring at elevation) → verify ferritin ≥40 ng/mL at least 6–8 weeks prior.
- RECHECK ferritin every 6–8 weeks during supplementation, annually for males in maintenance.

### 6.1B Testosterone-to-cortisol ratio

#### Core principle

The free testosterone-to-cortisol ratio (FTCR) reflects anabolic/catabolic balance. A **≥30% decline from individual baseline** is the traditional threshold for excessive stress (Adlercreutz et al., 1986), but ECSS/ACSM 2013 clarified it indicates strain rather than diagnosing OTS. Serial intra-individual monitoring is far more informative than single absolute values.

#### Evidence summary

- **30% decline threshold:** Transient 30% drops normal after acute heavy exercise; normalize within 24–48 hours. Only persistent declines (>72 hours at rest) concerning.
- **Absolute FTCR values:** <0.35 × 10⁻³ = high overtraining risk; 0.35–0.50 = moderate; >0.80 = well-rested (Banfi et al., 2006).
- **EROS study (Cadegiani & Kater, 2019):** Total testosterone <400 ng/dL in males = risk factor. Basal levels "mostly normal" in OTS — **stimulated (dynamic) responses** become blunted.
- **Endurance training suppression:** Hackney (2020): long-term endurance reduces testosterone by **20–40%** — stable adaptation, not pathology.

#### Application rule

- ESTABLISH baseline T:C during well-rested state (after recovery week).
- FLAG 20–30% decline → recovery optimization.
- FLAG ≥30% persistent decline → training modification: reduce volume 30–50%, increase recovery days.
- NEVER diagnose OTS from T:C alone → combine with performance, wellness, sleep, and other biomarkers.

### 6.1C CRP and inflammation

#### Core principle

High-sensitivity CRP (hs-CRP) distinguishes normal training inflammation from chronic overload. Well-trained athletes typically have **lower baseline hs-CRP** (~0.1–0.5 mg/L vs ~0.8 mg/L sedentary).

#### Evidence summary

- **Athlete baselines:** Trained swimmers median **0.1 mg/L**. Trained rowers ~0.26 mg/L (Kasapis & Thompson, 2005).
- **Acute response:** CRP increases up to **2,000% (20-fold)** after marathon, peaks 24–48 hours, returns to baseline within 2–6 days.
- **Chronic training effect:** Fedewa et al. (2017) meta-analysis: exercise reduces CRP, **ES = 0.26** (95% CI: 0.18–0.34).
- **Threshold interpretation (at rest, ≥48h post-exercise):** <0.5 mg/L = optimal; 0.5–1.0 = normal for athletes; 1.0–3.0 = elevated, investigate; **3.0–10.0 = concerning**; **>10.0 = acute illness**, not training response.

#### Application rule

- ALWAYS require ≥48h post-exercise for meaningful hs-CRP.
- FLAG persistent hs-CRP > 1.0 mg/L → training load review.
- FLAG > 3.0 mg/L → volume reduction + investigation.
- FLAG > 10.0 mg/L → halt training + medical evaluation.

### 6.1D Vitamin D

#### Core principle

Athletes require 25(OH)D levels well above clinical sufficiency (30 ng/mL). Peak neuromuscular performance and injury protection at **40–60 ng/mL** (100–150 nmol/L). Deficiency prevalence **33–90%** of athletes at latitudes >35° in winter — directly relevant to alpine environments.

#### Evidence summary

- **Optimal range:** 40–60 ng/mL (Cannell et al., 2009; Larson-Meyer, 2015). Peak neuromuscular function at ~50 ng/mL. No benefit above 60 ng/mL.
- **Stress fracture risk:** Ruohola et al. (2006): **3.6× higher** with <30 ng/mL. Miller et al. (2020, NCAA): incidence dropped **7.51% → 1.69%** when athletes maintained ≥40 ng/mL.
- **Immune function:** Martineau et al. (2017) meta-analysis: supplementation reduced respiratory infections (OR 0.88 overall; **OR 0.30 in deficient**). Daily/weekly dosing superior to bolus.

**Supplementation protocols by level:**

| Status | 25(OH)D | Protocol |
|---|---|---|
| Severe deficiency | <10 ng/mL | 50,000 IU/week × 8 weeks → 1,500–2,000 IU/day maintenance |
| Deficiency | 10–20 ng/mL | 4,000–6,000 IU/day × 8–12 weeks → 1,500–2,000 IU/day |
| Insufficiency | 20–30 ng/mL | 2,000–4,000 IU/day × 8–10 weeks → 1,000–2,000 IU/day |
| Suboptimal for athletes | 30–40 ng/mL | 1,500–2,000 IU/day year-round |
| Optimal | 40–60 ng/mL | 1,000 IU/day maintenance in winter |

#### Application rule

- TEST twice yearly (autumn and spring) at minimum.
- FOR mountain athletes at northern latitudes → assume winter insufficiency unless supplementing.
- FLAG <30 ng/mL → initiate supplementation. FLAG <20 ng/mL → aggressive repletion with recheck at 8–12 weeks.
- DURING winter training blocks → default to 1,000–2,000 IU/day maintenance even without lab data.

### 6.1E Thyroid markers and energy availability

#### Core principle

Heavy training frequently produces "low T3 syndrome" (euthyroid sick syndrome) — low fT3, elevated reverse T3, with near-normal TSH and T4. This is a **hypothalamic adaptation to energy deficit, not thyroid disease**, and **does not warrant thyroid hormone replacement**. The critical question is whether low T3 reflects acceptable adaptation or problematic low energy availability (RED-S).

#### Evidence summary

- **Energy availability threshold:** Loucks & Heath (1994): T3 reduction of **16%** occurred abruptly between EA of 19 and **25 kcal/kg lean body mass/day**.
- **IOC 2023 RED-S Consensus (Mountjoy et al.):** EA < 30 kcal/kg FFM/day = threshold for physiological disruption. T3 = key biomarker in IOC REDs CAT2 tool. The 2023 consensus explicitly recognizes REDs in males.
- **EROS study:** Free T3 and IGF-1 proposed as "sentinel markers of recovery from OTS" (Cadegiani, 2020).
- **Reference ranges for athletes:** TSH 0.4–4.5 mIU/L, fT4 0.9–1.7 ng/dL, fT3 2.0–4.4 pg/mL. Concerning: fT3 < 3.5 pmol/L or >15% decline from baseline.

#### Application rule

- NEVER recommend thyroid hormone replacement for low T3 in context of heavy training.
- FLAG low T3 as energy availability red flag.
- IF fT3 drops >15% from baseline OR falls below 2.5 pg/mL → assess energy intake vs. expenditure.
- FOR mountain athletes with high expenditure → low T3 strongly suggests caloric deficit. Intervention = increased energy intake.

-----

## 6.2 Retest intervals

### Application rule

**Screening (healthy athletes):**
- Comprehensive panel **1–2× per year**. Best timing: pre-season (autumn) and mid-season (spring).

**Monitoring (structured training):**
- Key performance markers every **6–8 weeks** for recreational athletes.
- During intensified blocks: ferritin, hs-CRP every 4–6 weeks.

**Issue-tracking:**

| Marker | Retest interval |
|---|---|
| Iron (oral supplementation) | 6–8 weeks |
| Iron (IV) | 4 weeks |
| Vitamin D repletion | 8–12 weeks |
| Thyroid follow-up | 6–8 weeks |
| Hormonal recovery (T:C) | 4–8 weeks |
| CRP normalization | 2–4 weeks |

**Recommended panels:**
- Hybrid mountain athlete: CBC with differential, full iron panel, vitamin D, thyroid panel (TSH, fT3, fT4), hs-CRP, AM cortisol, testosterone (total + free), metabolic panel, liver enzymes (ALT, AST, GGT), CK, creatinine/eGFR (essential for creatine users).

**Pre-analytic notes:** Blood draws **7:00–10:00 AM, fasted 8–12 hours, ≥48 hours after strenuous exercise** (≥7 days for CK and liver enzymes after heavy resistance training). Seated 15 min before venipuncture. Euhydrated. Biotin >1,000 mcg interferes with TSH/T3/T4 immunoassays — discontinue 3–5 days before.

-----

## 6.3 Red flag thresholds

### Application rule

**Tier 1: Training modification triggers**

| Marker | Threshold | Action |
|---|---|---|
| Ferritin | <35 ng/mL | Reduce high-intensity volume; initiate iron supplementation |
| Hemoglobin | <13.5 g/dL | Reduce intensity; investigate iron status |
| Testosterone (total) | <400 ng/dL | Assess energy availability; reduce training load 30% |
| T:C ratio | >20% decline from baseline | Increase recovery; reduce intensity |
| hs-CRP | >3.0 mg/L (persistent, ≥48h post-exercise) | Reduce volume; review recovery |
| Free T3 | <2.5 pg/mL or >15% decline | Increase caloric intake; assess EA |
| CK | >1,000 U/L (resting, 72h+ post-exercise) | Reduce eccentric load; extend recovery |
| WBC | <3.5 × 10⁹/L (persistent) | Reduce load; assess immune function |

**Tier 2: Medical referral triggers**

| Marker | Threshold | Action |
|---|---|---|
| Ferritin | <12 ng/mL with low Hb (IDA) | Urgent referral; IV iron |
| Ferritin | >300 ng/mL | Referral (hemochromatosis screening) |
| Hemoglobin | <11.0 g/dL | Urgent medical evaluation |
| Testosterone | <300 ng/dL (persistent) | Endocrine workup |
| Cortisol (AM) | <3 or >23 µg/dL (persistent) | Adrenal evaluation |
| hs-CRP | >10.0 mg/L (non-acute, at rest) | Medical evaluation |
| TSH | >10 or <0.1 mIU/L | Endocrine referral |
| Vitamin D | <10 ng/mL | Medical supervision for repletion |
| CK | >5,000 U/L | Rhabdomyolysis workup; check renal function |
| Creatinine | >2.0 mg/dL or acute rising | Nephrology referral; stop creatine |
| eGFR | <60 mL/min/1.73m² (confirmed repeat) | Nephrology referral |

**Tier 3: Supplementation/dietary intervention triggers**

| Marker | Threshold | Intervention |
|---|---|---|
| Ferritin | <50 ng/mL | Dietary iron optimization; oral 65–100 mg elemental/day |
| Ferritin | <20 ng/mL | Aggressive oral 100 mg/day; consider IV if no response at 6–8 wks |
| Vitamin D | <20 ng/mL | 4,000–6,000 IU D3/day × 8–12 weeks |
| Vitamin D | 20–30 ng/mL | 2,000–4,000 IU D3/day × 8–10 weeks |
| Vitamin D | 30–40 ng/mL | 1,500–2,000 IU D3/day year-round |
| Low T3 pattern | Low T3 + normal TSH | Increase energy +300–500 kcal/day; target EA >30 kcal/kg FFM |

### Application rule

- TIER 1 findings → automatically reduce prescribed training load within next programming cycle.
- TIER 2 findings → generate prominent alert for medical evaluation; hold training at reduced levels until clearance.
- TIER 3 findings → trigger supplementation recommendations alongside training adjustments.
- ALWAYS interpret multiple markers together — **two or more markers trending same direction** demand immediate action.

-----

## 6.4 Creatine supplementation

### Core principle

Creatine monohydrate reliably increases serum creatinine (spontaneous conversion at ~1.7%/day of body stores) without impairing kidney function. Supplementation increases intramuscular creatine by **20–40%**, proportionally increasing creatinine production. This creates false positives on standard panels. **Cystatin C** is the definitive alternative marker. Beyond muscle performance, emerging evidence supports creatine's cognitive benefits — particularly relevant for mountain athletes making safety-critical decisions under physiological fatigue.

### Evidence summary

**Creatinine increase magnitude:**
- Maintenance dosing (3–5 g/day): **+0.1–0.3 mg/dL** above baseline. Users commonly present at 1.2–1.5 mg/dL.
- Loading (20 g/day): **+0.2–0.4 mg/dL**.
- Naeini et al. (2025, *BMC Nephrology*, 21 studies): pooled increase of **0.07 µmol/L** — clinically trivial. **No significant change in GFR**.
- Gualano et al. (2008): cystatin C actually **decreased** (0.82 → 0.71 mg/L) during 12 weeks creatine.
- Washout: normalizes within **2–4 weeks** of cessation.

**Strength benefits:**
- Rawson & Volek (2003) meta-analysis, 22 studies: average strength increase **20% with creatine vs 12% with placebo** (8 pp greater).
- Lanhers et al. (2017): upper limb **ES 0.317** (p<0.001); bench press ES 0.265.
- 2025 meta-analysis: overall muscle strength **SMD 0.43** (95% CI: 0.25–0.61). Athletic populations: muscle power **ES 1.19**.
- Absolute gains: bench **+6.85 kg**, squat **+9.76 kg** vs placebo (Dempsey et al., 2002). Upper-body **+4.43 kg** (Wang et al., 2024).
- Lean body mass: Delpino et al. (2022, 35 RCTs): **+1.10 kg** with RT. Males: **+1.46 kg**. Desai et al. (2024): **+1.14 kg LBM**, −0.88% body fat.

**Cognitive benefits (new v1.1 addition):**
- **Xu et al. (2024, *Frontiers in Nutrition*) — first comprehensive meta-analysis on creatine and cognitive function:** Significant improvements in memory (SMD = **0.31**, p = 0.004), attention (SMD = **−0.31**, p = 0.01), and processing speed (SMD = **−0.51**, p = 0.01). Effects were more pronounced under conditions of **sleep deprivation and cognitive stress**.
- **Mountain athlete relevance:** Creatine's cognitive benefits are directly applicable to safety-critical decision-making in avalanche terrain, route-finding in poor visibility, and paraglider launch decisions — all of which occur under physiological fatigue, altitude-induced hypoxia, and often sleep deprivation (multi-day tours, early alpine starts). The brain consumes ~20% of the body's ATP at rest, and creatine contributes to brain phosphocreatine reserves.
- **Antonio et al. (2025, JISSN) "Part II" common questions update:** 20 leading creatine researchers reaffirmed monohydrate's safety, addressed persistent myths, and highlighted the expanding evidence for cognitive and neuroprotective benefits.

**Endurance relevance for mountain athletes:**
- **Ineffective for steady-state VO2max** in trained athletes. May slightly decrease VO2max from body mass increase.
- Forbes et al. (2023, JISSN): creatine **increases time to exhaustion** during high-intensity endurance and benefits performances requiring **multiple surges, pace changes, finishing kicks** — matching ski touring (steep skin tracks), splitboarding (repeated climbs), hike-and-fly (rapid ascents).
- Body mass increase ~**1–2 kg**. Study on 8% incline climbing at 90% VO2max: **no detrimental effect** from creatine mass gain.
- **Net assessment:** Likely beneficial year-round for ski touring and splitboarding (variable terrain + cognitive demands). For hike-and-fly where every gram matters during sustained ascent, 1–2 kg may be a concern — but cognitive benefits at altitude likely outweigh the mass penalty.

**Safety:**
- ISSN Position Stand (Kreider et al., 2017): up to **30 g/day for 5 years** safe in healthy individuals.
- Antonio et al. (2021 + 2025) ISSN updates: reaffirmed all safety conclusions.
- No controlled trial shows kidney impairment in healthy individuals.

**Dosing protocols:**
- **Loading:** 0.3 g/kg/day (typically 20 g/day in 4 × 5g) × 5–7 days. Co-ingest with ~50g CHO.
- **Maintenance:** 3–5 g/day (0.03–0.05 g/kg/day). Larger athletes (>90 kg): 5–10 g/day.
- **No-loading alternative:** 3 g/day × 28+ days reaches same saturation, slower onset.
- **Timing:** Post-exercise slightly superior. Co-ingest with CHO + protein. Consistency > timing.
- **Form:** Creatine monohydrate exclusively. No other form has demonstrated superiority.

**Sarshin et al. (2024, JISSN):** First GRADE-assessed dose-response analysis of creatine on body composition. Confirmed 3–5 g/day as the optimal maintenance range. DOI: 10.1080/15502783.2024.2380058.

### Application rule

- RECOMMEND creatine monohydrate **year-round at 3–5 g/day** for mountain athletes, including during endurance phases, based on combined strength + cognitive benefits.
- The cognitive benefits at altitude and during fatigued decision-making outweigh the 1–2 kg mass concern for all but the most weight-sensitive hike-and-fly race scenarios.
- ALWAYS flag creatine use in athlete profile for blood work interpretation.
- IF creatinine 1.2–1.5 mg/dL in creatine user with no other concerns → note as expected; no kidney concern.
- IF creatinine > 1.5 mg/dL on creatine → recommend cystatin C before concern.
- TRUE RED FLAGS: creatinine rising progressively after dose stabilization, proteinuria, or cystatin C-based eGFR also reduced.
- PREFER no-loading protocol for athletes sensitive to weight gain or with GI issues.

### Key sources

- Kreider RB et al. "ISSN Position Stand: creatine supplementation." *JISSN*, 2017.
- Antonio J et al. "Common questions about creatine supplementation." *JISSN*, 2021.
- Antonio J et al. "Common questions about creatine supplementation: an update." *JISSN*, 2025. DOI: 10.1080/15502783.2024.2441760.
- Rawson ES, Volek JS. "Effects of creatine on muscle strength." *JSCR*, 2003.
- Lanhers C et al. "Creatine and upper limb strength." *Sports Medicine*, 2017.
- Forbes SC et al. "Creatine and endurance performance." *JISSN*, 2023.
- Delpino FM et al. Creatine and lean mass. *Nutrition*, 2022.
- Naeini F et al. Creatine and kidney function. *BMC Nephrology*, 2025.
- Gualano B et al. Cystatin C study. *Eur J Appl Physiol*, 2008.
- Xu R et al. "The effects of creatine supplementation on cognitive function in adults: a systematic review and meta-analysis." *Frontiers in Nutrition*, 2024; 11: 1424972. DOI: 10.3389/fnut.2024.1424972.
- Sarshin A et al. "Creatine supplementation protocols: a GRADE-assessed systematic review and dose-response meta-analysis." *JISSN*, 2024. DOI: 10.1080/15502783.2024.2380058.

### Cross-references

- → Biomarkers §6.3 (creatinine red flag thresholds adjusted for creatine users)
- → Concurrent Training §3.4 (body mass considerations)
- → Integration Rule #22 (cognitive function under fatigue — supports year-round creatine)


-----

# DOMAIN 7: METRIC HIERARCHY & SIGNAL QUALITY

## 7.1 Evidence-based metric hierarchy

### Core principle

Consumer wearable platforms emphasize proprietary composite scores, sleep stage breakdowns, and VO2max estimates from non-running activities — metrics that sit at the bottom of the evidence hierarchy. The tools with the strongest and most replicated support — daily subjective wellness checks and session RPE logging — require no wearable at all. Ascent's coaching logic must weight metrics by evidence strength, not by how prominently Garmin displays them.

### Metric hierarchy table

| Tier | Metric | Evidence strength | Actionability | Key thresholds | Primary citation |
|------|--------|-------------------|---------------|----------------|------------------|
| **1** | Subjective wellness composite (5-item) | **Strong** | High | Z < −1.0 SD for 2 consecutive days | Saw et al. 2016 (56 studies) |
| **1** | HRV (7-day rolling ln(rMSSD) mean + CV) | **Strong** | High | SWC = 0.5 × SD of 7-day rolling; CV > 7–10% with declining mean = maladaptation risk | Plews et al. 2012, 2013, 2014 |
| **1** | Session RPE (sRPE = CR-10 × duration) | **Strong** | High | Week-to-week increase > 10–15% = spike alert | Foster et al. 2001; Haddad et al. 2017; McLaren et al. 2018 |
| **2** | Resting heart rate trend | Moderate | Moderate | Sustained elevation > 5 bpm above 7-day baseline, corroborated by declining HRV | Nature Sci Reports 2025 |
| **2** | Total sleep duration (7-day rolling avg) | **Strong** for duration | Moderate | < 7 hours for ≥ 14 consecutive days → 1.7× injury risk; Garmin TST accuracy ± 20–30 min | Milewski et al. 2014; Chinoy et al. 2021 |
| **2** | VO2max trend (running-derived only) | Moderate (running); Weak (non-running) | Low–Moderate | Flag single-session changes > 3 ml/kg/min as noise; ± 5% MAPE with chest strap; ± 9.8 ml/kg/min individual error | Molina-Garcia et al. 2022 (INTERLIVE) |
| **2** | Body weight (7-day rolling average) | Moderate | Moderate | React only to > 0.5 kg shift sustained over 2+ weeks; daily fluctuations of 1–3 kg are noise | — |
| **3** | Garmin Body Battery | Proprietary-unvalidated | Low | No independent validation; display as qualitative trend only | No peer-reviewed validation exists |
| **3** | Sleep staging (deep/REM/light %) | Weak | Very low | ~69% epoch accuracy; REM correct only 33% (Schyvens 2025); MAPE > 60% for all stages | Chinoy et al. 2021; Schyvens et al. 2025 |
| **3** | ACWR (acute:chronic workload ratio) | **Discredited** as ratio | None | Do not implement; use absolute weekly load + spike detection instead | Impellizzeri et al. 2020, 2021 |
| **3** | Garmin Training Readiness/Status | Proprietary-unvalidated | Low | Composite of composites; can show "Unproductive" from GPS/HR artifacts, not detraining | — |
| **3** | BIA body fat % (consumer) | Weak | Very low | Under-reads fat mass by ~5 kg vs MRI; ± 7 kg limits of agreement; hydration causes up to 4.2% within-day variation | — |

### The decision hierarchy principle

When signals conflict, weight them in this order: **subjective wellness > HRV (7-day rolling) > sRPE > resting HR > sleep duration > everything else.** This reflects the evidence: Saw et al. (2016, BJSM, 56 studies) demonstrated subjective self-reported measures "trump commonly used objective measures" for monitoring training response; Nummela et al. (2024) confirmed subjective markers — readiness to train and leg soreness — were the most sensitive indicators of training load response, with greater magnitude responses in overreached individuals than resting or exercise HR.

### Consumer app divergences worth flagging

- **Garmin Training Readiness:** Composite of composites — unvalidated proprietary metric layered on unvalidated proprietary metrics. Strength training poorly captured; systematically underestimates neuromuscular fatigue from lifting.
- **Garmin Training Status:** Can show "Unproductive" due to poor GPS, wrist HR artifacts, heat, or altitude — not actual detraining.
- **Whoop Recovery / Oura Readiness:** Same limitations — proprietary weighting of partially validated inputs with no published independent validation.
- **All consumer platforms:** The biggest gap is the absence of subjective wellness capture — the single metric with the strongest evidence base.

### Application rule

- NEVER use Tier 3 metrics as inputs to automated coaching decisions. Display as contextual information only.
- ALWAYS present Tier 2 metrics alongside Tier 1 for confirmation, never in isolation.
- WHEN Tier 1 signals conflict with Tier 3 → trust Tier 1 unconditionally.
- WHEN presenting VO2max → only use running-derived values; ignore non-running estimates; display as "48 ± 5 ml/kg/min" not false-precision single numbers.
- WHEN presenting sleep data → only reference total sleep duration as reliable; present stages as "~2h deep sleep (±45 min)" with explicit uncertainty.
- LABEL all metrics as "measured" (HR, accelerometry, GPS) or "estimated" (VO2max, Body Battery, sleep stages) in coaching messages.

-----

## 7.2 Data validation rules

### Core principle

Every metric from a consumer wearable contains measurement error. Before any metric reaches the dashboard or coaching layer, it must pass plausibility checks. The goal is to reject physiologically impossible values (data corruption) and flag values that are physiologically plausible but atypical (warrant human review before acting on them).

### Comprehensive validation rule set

| Metric | Reject if | Flag for review if |
|--------|-----------|-------------------|
| rMSSD (ms) | < 5 or > 250 | < 8 or > 200 (outside typical athletic range) |
| Resting HR (bpm) | < 25 or > 120 | < 30 or > 100 at rest |
| Exercise HR (bpm) | < 30 or > 230 | > (220 − age + 15) sustained |
| HR rate of change | > 40 bpm in < 5 sec (non-sprint) | > 25 bpm in < 5 sec |
| Sleep duration (hours) | < 2 or > 16 | < 3 or > 14 |
| Daily weight change (kg) | > ± 3.0 in 24h | > ± 2.0 in 24h |
| Weekly weight change (kg) | > ± 4.0 in 7 days | > ± 3.0 in 7 days |
| Elevation gain rate | > 300 m/hour (non-climbing) | > 200 m/hour for hiking activities |
| VO2max change | > 5 ml/kg/min in one session | > 3 ml/kg/min week-over-week |

### Wrist HR during strength training

Optical wrist HR is effectively invalid during resistance training. Zhang et al. (2020 meta-analysis, 44 studies, 738 effect sizes) found wrist optical HR **systematically underestimates by 7.26 bpm** during resistance training (95% CI: −10.46 to −4.07), with error increasing by 3 bpm per 10 bpm increase in true HR. Garmin Instinct showed MAPE of 15.9% at moderate-high intensity RT; inner wrist placement reached 28% MAPE with CCC of 0.17 — functionally useless (Kerwin et al., 2025). Failure modes: grip-induced venous pooling, wrist flexion displacement, isometric contraction artifacts, Valsalva-related HR spikes, and cadence lock (PPG locking onto lifting cadence at ~0.5 Hz).

**Rule:** Flag all HR data during tagged strength activities with an explicit low-confidence warning. Do not use wrist HR zones or TRIMP for strength sessions.

### Wrist HRV reliability

PPG-derived HRV shows excellent agreement with ECG at rest (ICC = 0.955 for RMSSD in supine position; Sensors 2025) but degrades progressively with motion, cold exposure, and exercise intensity (Jamieson et al., 2025). For a mountain athlete frequently operating in cold conditions with variable wrist blood flow, **only nocturnal HRV data should inform coaching decisions**. Garmin's enhanced BBI system includes a confidence score; filter out beats with confidence < 0.5.

### Elevation gain correction

Raw barometric elevation data accumulates noise from pressure fluctuations, weather drift, and GPS auto-calibration interference. Cumulative elevation gain is commonly overestimated by **10–20% without post-processing**. A 4 hPa pressure change (typical approaching storm) creates ~37 meters of false elevation. Apply dead-band filtering (suppress elevation changes below 3–5 meter threshold). Additionally: flag activities where start/end elevation differs > 30 meters at the same location, flag elevation gain > 150 m/hour during non-technical climbing as suspicious, and cross-reference with known route profiles where available. Calibrated barometric accuracy is ± 3–10 meters absolute; GPS-only elevation is ± 120 meters.

### Gap-aware rolling calculations

The critical PostgreSQL implementation detail: `ROWS BETWEEN N PRECEDING AND CURRENT ROW` counts rows, not calendar dates — if dates are missing, the window silently spans more time than intended. Always use a `generate_series()` date spine with LEFT JOIN to daily metrics, then apply window functions over the filled spine with NULL-aware aggregation and minimum-count thresholds: **4 of 7 valid days for weekly averages, 20 of 30 for monthly, 60 of 90 for quarterly.**

### Epoch-aware baselines

Use a multi-window baseline architecture:

| Metric | Short-term window | Long-term baseline |
|--------|------------------|--------------------|
| HRV | 7-day rolling | 60-day normal |
| Resting HR | 7-day rolling | 30-day normal |
| Sleep | 7-day rolling | 30-day normal |
| Weight | 7-day rolling | 30-day normal |
| Performance (VO2max, e1RM) | 30-day rolling | 90-day normal |

When a device change, firmware update, or detected algorithm shift creates a new "epoch," baselines must reset and recalculate from epoch start to prevent spurious drift signals. Maintain a `data_epochs` table recording start date, device model, firmware version, and trigger type. For drift detection, CUSUM (Cumulative Sum) sequential analysis is the gold-standard technique — O(n) complexity, effective for small gradual shifts characteristic of sensor calibration drift.

### Data retention policy

For a single-user system, daily-resolution data volume is trivial (~365 rows/year). **Keep everything at daily granularity forever.** For sub-daily data (minute-level HR, stress scores): full resolution for 90 days → hourly aggregates (min/max/avg/count) for 90 days to 2 years → daily aggregates permanently.

### Application rule

- APPLY reject-level validation in `garmin_sync.py` before writing to Supabase — rejected values should not enter the database.
- APPLY flag-level validation at the dashboard/coaching query layer — flagged values are stored but marked for human review.
- NEVER compute rolling averages using row-based windows — always use date-spine pattern with `generate_series()`.
- TRACK data quality daily via `daily_data_quality` table: wear hours, completeness score, max gap duration, is_valid_day flag (requires ≥ 10h wear time).
- LOG device changes in `data_epochs` table and reset baselines accordingly.
- DISTINGUISH "measured" vs. "estimated" metrics in all UI and coaching outputs.

### Key sources

- Zhang M et al. "Wrist-worn optical heart rate monitors: a meta-analysis." *Sports Medicine*, 2020; 50(4): 761–780.
- Kerwin M et al. Garmin Instinct optical HR during resistance training, 2025.
- Jamieson A et al. PPG-derived HRV accuracy degradation, 2025.
- Chinoy ED et al. "Performance of seven consumer sleep-tracking devices." *Sleep*, 2021; 44(5): zsaa291.
- Schyvens AM et al. "Consumer wearable sleep staging accuracy." 2025.
- Impellizzeri FM et al. "Acute:chronic workload ratio: conceptual issues and fundamental pitfalls." *Int J Sports Physiol Perform*, 2020; 15(6): 907–913.
- Impellizzeri FM et al. "Training load and injury: Part 2." *J Sports Sci*, 2021.

### Cross-references

- → Recovery §1 (HRV validation before coaching use)
- → Recovery §3 (subjective wellness is Tier 1, device composites are Tier 3)
- → Endurance §3.5 (elevation gain correction)
- → Integration Rule #13 (multi-signal convergence)


-----

# DOMAIN 8: DASHBOARD & COMMUNICATION DESIGN PRINCIPLES

## 8.1 Information density and visual design

### Core principle

Restraint in information density is critical. For a single recreational athlete, the dashboard should feel like a calm, helpful companion — not an ICU monitoring station. Miller's Law (1956) limits working memory to 7 ± 2 chunks, but modern UX refinements suggest 3–7 for dashboards under cognitive load (Sweller, 1988). Fuller et al. (2020) demonstrated well-designed health dashboards *reduce* cognitive burden compared to raw data presentation.

### Dashboard design rules

**Daily morning dashboard (< 30 seconds):**
- Maximum **5–6 Stat panels**: readiness composite (color-coded), sleep summary (duration + quality), HRV status versus baseline (with trend arrow), today's training guidance (text from AI), current training phase, and any active alerts.
- Use Grafana's Stat visualization with **background color mode** — the entire panel turns green/amber/red so the screen is predominantly green during normal periods, with red panels immediately drawing the eye.
- Place most critical metric (readiness composite) in **top-left per F-pattern** reading behavior (Sommer, 2022).
- **Mobile-first**: single-column, full-width panel layouts. Research shows 80% of patients abandon health apps with poor UX (CapMinds, 2024).
- Use large stat numbers and sparklines rather than complex multi-axis charts. Avoid pie charts, radar charts, and horizontal scrolling.
- Use Grafana's row collapse feature for progressive disclosure: daily essentials expanded, deep-dive sections collapsed by default.

**Weekly review (5–10 minutes, Sunday evening):**
- 7-day training load breakdown, sleep trends, HRV rolling average vs. baseline, weight trend, and AI-generated weekly summary.
- More detail acceptable — expandable rows, multi-metric charts.

**Quarterly strategic review (20–30 minutes):**
- 90-day training volume and intensity evolution (stacked area), fitness progression (VO2max, e1RM trajectories), body composition trends, season periodization assessment, and goal progress visualization.
- This dashboard is for detailed analysis, not phone glance — wider panels, multi-axis charts acceptable.

### RAG indicator rules

Traffic-light systems (Red/Amber/Green) are effective only when applied to **2–3 genuinely actionable composite metrics** with personalized thresholds. Bernard Marr identifies three major RAG pitfalls: overuse (50 RAG icons = noise), ambiguous definitions (what does "amber" mean?), and avoidance of red (people twist metrics to dodge it). Stacey Barr advocates Statistical Process Control over simplistic period-to-period comparisons.

**Rules:**
- Apply RAG to at most **2–3 composite metrics**, never individual raw values.
- All thresholds must derive from **personal rolling baselines** (30-day mean ± 1 SD), not population norms.
- Display personal baseline bands as shaded areas on all trend charts.
- For inherently noisy metrics (HRV, weight), show **trend direction indicators** ("trending up over 14 days") rather than daily color-coding.
- **Always pair colors with non-color cues** (↑↓→ arrows, text labels) — 10% of males cannot distinguish red from green.

### Time window recommendations per metric

| Metric | Default view | Smoothing | Rationale |
|--------|-------------|-----------|-----------|
| HRV | 30-day | 7-day rolling average overlay | Single-day values are meaningless noise |
| Sleep duration | 7-day | 7-day rolling average | Night-to-night variation too high for daily interpretation |
| Weight | 21-day | EWMA trend line | Daily fluctuations of 1–3 kg are not signal |
| Training load (sRPE) | 28-day | EWMA acute/chronic comparison | 7-day acute, 28-day chronic windows |
| Performance (VO2max, e1RM) | 90-day or full-season | Multi-week rolling | These move slowly |

Layer raw data points beneath smoothed trend lines. Add annotation markers for key events (race days, illness, travel, altitude changes) to provide the "why" behind metric shifts.

### Application rule

- LIMIT daily dashboard to ≤ 6 panels. Every panel must answer: "Should I train normally today?"
- EVERY dashboard must be scannable in < 30 seconds on a phone.
- DEFAULT to collapsed rows on mobile; expand on tap.
- USE Stat panel background color mode for composite readiness — not small color dots.
- LABEL sleep architecture panels as "approximate — ± 45 min accuracy per stage" and never color-code individual stages red/green.
- LAYER raw data beneath smoothed trends on all time-series charts.

-----

## 8.2 Alert architecture

### Core principle

Clinical research shows 85–99% of hospital alarms are false or clinically insignificant, causing dangerous alarm fatigue (PMC review, 2025). Apple Watch's hypertension monitoring deliberately accepts ~40% sensitivity for high specificity, using continuous monitoring to compensate. For a recreational athlete, target **no more than 1–2 genuine alerts per week**.

### Alert design rules

**Compound conditions required:** Alert only when **2+ signals converge** (e.g., HRV drop AND poor sleep, not HRV drop alone). Compound conditions dramatically reduce false positives.

**Time-delay filtering:** Require **2–3 consecutive days** of concerning values before triggering. Single-day anomalies are noise.

**Three-tier alert structure:**

| Tier | Delivery | Urgency | Example |
|------|----------|---------|---------|
| **Red** | Push notification (Telegram) | Requires action today | HRV 7-day rolling > 1.5 SD below baseline for 2+ days AND sleep < 6h |
| **Amber** | Dashboard badge | Visible at next check | Weight 7-day rolling shifted > 0.5 kg over 2 weeks |
| **Informational** | Weekly summary only | No real-time alert | e1RM plateau detected (4+ weeks flat) |

**Auto-updating thresholds:** Van Rossum et al. (2022, J Clin Monit Comput) demonstrated that adaptive threshold strategies either increase sensitivity or reduce alarm rates compared to fixed thresholds. Implement three tiers: safety alerts (absolute, fixed, manual-only update), anomaly alerts (deviation-based with automatic weekly recalculation from 60-day baseline), and trend alerts (slope-based, continuous).

### Application rule

- NEVER fire single-metric, single-day alerts. Always require compound conditions.
- TARGET 1–2 genuine alerts per week maximum. If alert volume exceeds this, thresholds are too sensitive.
- STORE all thresholds with version history, effective dates, and recalculation timestamps.
- ROUTE alerts through Jarvis so the coach can add context (e.g., "HRV is low AND you had a hard mountain day yesterday, so this is expected").

-----

## 8.3 Coaching communication: SDT-grounded principles

### Core principle

The most robust finding across coaching psychology literature is that **autonomy-supportive communication consistently outperforms directive framing** for adherence and long-term motivation. This is especially true for knowledgeable athletes with strong self-regulation (Mageau & Vallerand, 2003; Amorose & Anderson-Butcher, 2007). Carpentier & Mageau (2013, N=340 athletes) demonstrated that change-oriented feedback quality — not quantity — predicts athlete experience and performance.

### Autonomy-supportive language rules

- Use **"consider," "one option is," "the data supports"** — never "should," "must," "need to."
- Frame Ascent as a **"second pair of eyes on the data"** not an authority. Research on expert athletes shows they judge their own performances more accurately than their coaches (Millar et al., 2017). The system adds value through pattern detection across multiple simultaneous data streams — not through superior judgment.
- Every recommendation requires a **rationale**: "Based on your HRV trend (down 12% over 3 days), backing off intensity could support adaptation."
- Offer **2–3 options with tradeoffs** rather than single prescriptions.

### Presenting negative signals without demotivating

- Lead with **objective data, not judgments**: "HRV dropped 15% this week" rather than "your recovery has been poor."
- **Normalize variation**: "Recovery fluctuates — this dip is within the range we'd expect given last week's volume increase."
- Connect findings to the athlete's **goals**: "Given your Chamonix preparation timeline, this recovery trend is worth watching because…"
- Use **trend language, not snapshot language**: "Over the past 10 days…" rather than "Yesterday your score was…"
- Never use shame-adjacent framing ("You missed 3 sessions") — reframe as neutral observation ("3 scheduled sessions didn't happen this week — life happens. Here's how the plan could adapt").

### Calibrated confidence tiers

Adapting the BODHI framework (2025, PLOS Digital Health):

| Confidence | Signal quality | Communication style | Example |
|------------|---------------|--------------------|---------| 
| **High** | Strong signal, multiple converging data points | Specific recommendation + explicit rationale | "Your HRV, sleep, and subjective scores all point to good recovery. Consider pushing intensity today." |
| **Moderate** | Emerging pattern, fewer data points | Note with hedging | "Your sleep quality appears to be declining, though the data is limited — worth monitoring." |
| **Low** | Single data point, ambiguous | Exploratory language | "Today's HRV reading was unusual. This could mean several things — let's see how the next few days look." |

Explicitly label data limitations: "Your watch didn't record sleep data for 2 of the last 7 nights, so this sleep trend has gaps."

### Optimal message structures

**Daily briefing** (Telegram, ~100–200 words, 06:00–07:00 AM):
- One-sentence readiness assessment
- 2–3 key metrics with context
- One autonomy-supportive guidance statement
- Optional deep-dive link

**Weekly summary** (~500–800 words, Sunday evening):
- Week overview versus plan
- 2–3 key metric trends with 4-week context
- One positive observation
- One attention area framed as opportunity
- Coming week preview
- One reflection prompt

**Quarterly strategic review** (~2,000–3,000 words):
- Executive summary
- Goal progress with visual tracking
- 12-week training load evolution
- Performance indicator trajectories
- Periodization assessment
- Strategic recommendations framed as options
- Structured athlete self-assessment questions

### SDT needs in digital coaching

Teixeira et al. (2012, 66 studies) confirmed that competence need satisfaction shows the most consistent positive association with exercise behavior, while relatedness is the hardest to satisfy digitally (MAP to Health, JMIR 2024).

- **Autonomy:** Meaningful choices, non-controlling language, customizable notification preferences.
- **Competence:** Clear progress markers, PB tracking, educational content that builds the athlete's knowledge.
- **Relatedness:** Personalized communication, "shared journey" language ("we've been building toward…"), acknowledgment of the athlete as a whole person.

### Guarding against automated coaching failure modes

- **Over-alerting:** 50% of Drink Less app users disengaged within 22 days (Maycock et al., 2023). Build signal-to-noise filtering.
- **False precision:** Presenting wearable data with unknown confidence intervals erodes trust. Always communicate measurement uncertainty.
- **Context blindness:** A bad training week may stem from a work deadline, not a physiological problem. Build periodic context-gathering check-ins ("Anything unusual this week?").
- **Quiet mode:** When everything is fine, reduce message frequency. Engagement monitoring should reduce frequency if messages go unread.

### Key sources

- Mageau GA, Vallerand RJ. "The coach-athlete relationship: a motivational model." *J Sports Sci*, 2003; 21(11): 883–904.
- Amorose AJ, Anderson-Butcher D. "Autonomy-supportive coaching and self-determined motivation." *Psychol Sport Exerc*, 2007; 8(5): 654–670.
- Carpentier J, Mageau GA. "When change-oriented feedback enhances motivation, well-being and performance." *J Sport Exerc Psychol*, 2013; 35(5): 497–507.
- Millar SK et al. "Self-assessment accuracy in athletes." *J Sport Behav*, 2017.
- Teixeira PJ et al. "Exercise, physical activity, and self-determination theory: a systematic review." *Int J Behav Nutr Phys Act*, 2012; 9: 78.
- Saw AE et al. "Monitoring the athlete training response: subjective self-reported measures trump commonly used objective measures." *BJSM*, 2016; 50(5): 281–291.
- Fuller R et al. "Health dashboard design reduces cognitive burden." 2020.
- Maycock KW et al. "Drink Less app user engagement." 2023.
- Van Rossum T et al. "Adaptive threshold strategies." *J Clin Monit Comput*, 2022.

### Cross-references

- → Domain 7 (metric hierarchy determines what appears on dashboards)
- → Recovery §3 (subjective readiness is highest-priority signal)
- → Integration Rule #13 (multi-signal convergence for decisions)


-----

# GAPS & FUTURE RESEARCH NEEDED

The following topics received thin or incomplete coverage across all source materials and represent areas where the AI coach should exercise caution, use conservative defaults, or prompt the user for more information.

**Status key:** ✅ = addressed in v1.1 | ⚠️ = partially addressed | ❌ = remains a gap

## 1. Mobility and flexibility training ❌

No domain-specific knowledge base was created for mobility. Key unanswered questions:
- What minimum mobility routine prevents injury in mountain athletes with heavy eccentric loading (descents)?
- How should hip flexor, ankle, and thoracic mobility be periodized alongside strength and endurance?
- What is the interaction between mobility work and recovery (does it help or add to fatigue)?
- Optimal timing of mobility work relative to strength sessions?

## 2. Female-specific physiology ❌ (excluded by design for this athlete profile)

Coverage is male-normative by design for this athlete profile. The Huiberts et al. (2024) sex-specific concurrent training data has been noted in §3.1 for reference. If the system is extended to other users, this domain requires full development including menstrual cycle effects, hormonal contraceptive interactions, female-specific HRV patterns, and iron supplementation protocols accounting for menstrual losses.

## 3. Age-related adaptations (masters athletes >40) ❌

Limited evidence on:
- How recovery timelines change with age beyond the generic "deload more frequently."
- Age-specific volume landmarks (do MEV/MAV/MRV shift meaningfully after 40?).
- Tendon and connective tissue recovery differences — particularly relevant for mountain athletes doing high eccentric loads.
- Hormonal recovery differences and when natural testosterone decline warrants medical vs. training intervention.
- Note: the Bickel et al. (2011) age-specific caveat has been added to §3.4 — older adults may not maintain hypertrophy on reduced doses.

## 4. Sport-specific strength transfer ❌

Unanswered questions:
- What is the minimum effective strength level for ski touring performance (is there a squat:bodyweight ratio threshold)?
- How do unilateral strength deficits affect mountain sport injury risk?
- What is the role of plyometric training for mountain athletes (relevant for steep, technical descent performance)?
- Optimal eccentric training protocols for descent preparation.

## 5. Hike-and-fly specific evidence ❌

Nearly all evidence is extrapolated from military load carriage, trail running, or general hiking. No studies specifically on:
- Physiological demands of competitive hike-and-fly events.
- Effect of fatigue on paraglider launch safety margins.
- Optimal training periodization for hike-and-fly season.
- Core and shoulder endurance requirements for active flying after hard ascent.

## 6. Wearable device validation ❌

The knowledge base relies on Garmin metrics (Body Battery, Training Readiness, HRV Status) without published independent validation. Key gaps:
- How accurately does Garmin's optical HRV capture rMSSD compared to chest strap?
- How should Body Battery be weighted relative to subjective and HRV data?
- Do Training Readiness scores reliably predict training session quality?
- Validation of Garmin's VO2max estimates for mountain-specific activities.

## 7. Nutrition periodization detail ⚠️ (partially addressed in §4.4, §4.7, §2.7)

While macronutrient targets are well-covered and caloric deficit interaction has been added (§4.7), gaps remain in:
- Practical meal planning around split mountain + gym days.
- Intra-workout nutrition protocols specific to ski touring (cold environment, altitude) — partially covered in §2.7 multi-day touring.
- Electrolyte replacement strategies at altitude (sodium, potassium, magnesium losses).
- Carbohydrate periodization (train-low/compete-high strategies) and their applicability to mountain athletes.
- Long-term effects of high-protein diets (>2.0 g/kg) on kidney markers in creatine users.

## 8. Psychological and cognitive factors ⚠️ (partially addressed via creatine cognitive benefits §6.4)

Not systematically addressed:
- Decision-making quality under physiological fatigue (critical for avalanche terrain, paragliding) — partially addressed by creatine cognitive benefit evidence in §6.4.
- Motivation and adherence patterns for autonomous AI-coached training — partially addressed by schedule disruption management in §5.6.
- Mental fatigue effects on mountain sport performance and safety.
- How to distinguish motivational fatigue from physical overtraining in an automated system.

## 9. Environmental factors beyond altitude ❌

Minimal coverage of:
- Cold exposure effects on strength performance (gym in cold conditions vs. heated).
- UV exposure and vitamin D synthesis at altitude with snow reflection.
- Wind chill effects on energy expenditure during touring.
- Seasonal affective disorder impact on training adherence in alpine locations.
- Heat acclimatization for cold-adapted mountain athletes (relevant for summer hike-and-fly). Lorenzo et al. showed heat acclimation improves performance in cool conditions too (VO2max +5%). Post-exercise passive heating (15–40 min sauna at ~40°C for 10+ days) is the most practical protocol.

## 10. Injury prevention and return-to-training protocols ⚠️ (partially addressed)

Illness-related return-to-training is now covered (§4.6). Remaining gaps:
- Common injury profiles for ski touring (knee, ankle, shoulder) and prevention strategies.
- Return-to-training protocols after common mountain sport injuries (not illness).
- Prehabilitation exercises specific to avalanche rescue demands (shoveling under duress).
- How to modify the training plan when an athlete is injured but can still train some modalities.

## 11. Schedule disruption management ✅ (addressed in §5.6)

Fully addressed in v1.1. See §5.6 for complete protocols covering single missed sessions through extended breaks of >4 weeks, including travel disruptions and unplanned mountain opportunities.

## 12. Training during illness ✅ (addressed in §4.6)

Fully addressed in v1.1. See §4.6 for illness severity classification, return-to-training timelines, post-COVID protocols (ACC 2022), and plan-level adjustments.

## 13. Multi-day touring protocol ✅ (addressed in §2.7)

Fully addressed in v1.1. See §2.7 for pre-trip preparation, in-trip load management (nutrition, pacing, rest day scheduling), and post-trip recovery protocols.

## 14. Caloric deficit interaction ✅ (addressed in §4.7)

Fully addressed in v1.1. See §4.7 for Murphy & Koehler (2022) evidence, maximum deficit thresholds, protein requirements, optimal timing within annual plan, and training modifications during deficit.

-----

*End of Ascent Scientific Knowledge Base v1.2*
*Total domains: 8 | Integration rules: 24 | Gap areas: 14 (4 fully resolved, 3 partially addressed, 7 remaining)*
*All thresholds, ranges, and protocols are population-level starting estimates requiring personalization through the individual's response data over time.*
*New in v1.2: Domain 7 (Metric Hierarchy & Signal Quality), Domain 8 (Dashboard & Communication Design Principles), autoregulation SUCRA rankings (§1.3), double progression decision logic (§1.1), autoregulated deload triggers and natural deload concept (§1.5), interference mechanism clarification (§3.1), session displacement strategy (§3.1), e1RM tracking rules (§3.4), subjective wellness questionnaire specification (§4.3), Le Meur HRV caveat (§4.1), data validation rule set (§7.2), comprehensive alert architecture (§8.2), SDT-grounded coaching communication (§8.3).*
*New in v1.1: Schedule disruption management (§5.6), illness protocols (§4.6), multi-day touring (§2.7), caloric deficit interaction (§4.7), Robinson et al. 2024 proximity-to-failure update (§1.3), corrected Schoenfeld volume threshold (§1.2), corrected Roberts snowboarding data (§2.5c), creatine cognitive benefits (§6.4), 2025 ACSM Position Stand context (§1.1, §5.1), and 15+ additional landmark sources from 2023–2025.*

