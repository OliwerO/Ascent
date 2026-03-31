# Evidence-Based Training Knowledge Base for Ascent

## 1. Strength Training — Programming Principles

### 1.1 Progressive Overload Models

**Core principle**  
Progressive overload means gradually increasing training stress (load, volume, or density) so that strength and hypertrophy continue to adapt rather than plateau. Different periodization models (linear, double progression, undulating, block) structure this progression over weeks and months to balance stimulus and fatigue.[^1][^2][^3][^4]

**Evidence summary**  
Linear progression typically increases load week to week at similar rep ranges, and is effective for novices but tends to stall as lifters advance. Daily undulating periodization (DUP) alternates hypertrophy, strength, and power sessions within a week; Zourdos et al. found DUP configurations produce significant 1RM gains in trained powerlifters over 6 weeks, with some weekly orderings slightly outperforming others. Meta-analytic reviews indicate that undulating and block models tend to outperform non-periodized training in trained lifters, while differences are smaller in beginners.[^2][^4][^5]

**Application guideline (Ascent)**  
- Novice: Use simple linear double progression (e.g., 3×5–8 at ~65–75% 1RM, add weight when top of rep range is achieved across sets) until weekly progression stalls.  
- Early-intermediate: Shift to weekly linear or DUP with distinct hypertrophy (3–4×8–12 at 65–75%), strength (3–5×3–6 at 75–85%), and power/technique (3–6×1–3 at 60–75%) days per lift.[^2]
- Advanced: Use block periodization—3–4 week accumulation blocks (higher volume, moderate intensity) followed by 2–3 week intensification (lower volume, higher intensity), then a short realization/taper week; progress load by 2.5–5% every 1–2 weeks if performance and RPE allow.[^6][^7]
- Ascent should detect repeated failure to hit prescribed reps or excessive RPE drift for ≥2 weeks and automatically switch from simple linear models to DUP/block for that lift.

**Key sources**  
- Zourdos et al. “Modified Daily Undulating Periodization Model Produces Greater Performance Than a Traditional Configuration in Powerlifters.” J Strength Cond Res, 2016.[^4]
- Issurin. “Block Periodization versus Traditional Training Theory: A Review.” J Sports Med Phys Fitness, 2008.[^6]
- Issurin. “Benefits and Limitations of Block Periodized Training Approaches to Athletes’ Preparation: A Review.” Sports Med, 2016.[^7]

***

### 1.2 Volume Landmarks (MEV, MAV, MRV)

**Core principle**  
Volume landmarks (maintenance volume, minimum effective volume, maximum adaptive volume, maximum recoverable volume) describe ranges of weekly work that maintain, minimally grow, optimally grow, or exceed recovery capacity for each muscle group. These landmarks shift upward as training status and work capacity increase.[^3][^1]

**Evidence summary**  
Schoenfeld’s 2017 dose–response meta-analysis found that higher weekly set volumes are associated with greater hypertrophy, with each additional weekly set per muscle increasing effect size by 0.023 and estimated percentage gain by ~0.37% up to at least 10+ sets/week. Later reviews suggest an optimal range around 12–20 weekly sets per muscle for hypertrophy in trained men, with potential plateau or inverted-U at very high volumes. Israetel’s Renaissance Periodization framework synthesizes this and practical data into approximate landmarks: MV ~4–8 sets, MEV ~8–12, MAV ~14–20, MRV ~20–28 sets per muscle per week for many trained lifters, with lower values for beginners and higher for advanced athletes.[^8][^9][^10][^11][^1][^3]

**Application guideline (Ascent)**  
- Default hypertrophy target for most muscles in intermediates: 12–18 hard sets/week (near MAV), split across 2–3 sessions.[^8][^1]
- Beginners: Start near the low end of MEV (8–10 sets/week per muscle) and progress volume over mesocycles as long as performance and recovery are good.  
- Advanced: Allow 14–22 sets/week for priority muscle groups, while non-priority muscles stay closer to MEV or maintenance (4–8 sets/week).[^1][^3]
- Ascent should progressively increase weekly sets within a mesocycle (e.g., +2–4 sets per muscle over 3–5 weeks) until early signs of under-recovery appear, then deload and restart near MEV.  
- Use wearable and performance data (RPE drift, HRV, soreness reports) to infer when the user is at or beyond MRV and automatically trim volume.

**Key sources**  
- Schoenfeld et al. “Dose–Response Relationship Between Weekly Resistance Training Volume and Increases in Muscle Mass: A Systematic Review and Meta-Analysis.” J Sports Sci, 2017.[^9]
- Tzanetakis. “The Effects on Muscle Hypertrophy of Different Weekly Training Loads in Resistance Training.” 2023 review.[^10]
- Israetel et al., Renaissance Periodization Hypertrophy Guides and Volume Landmarks resources.[^11][^3][^1]

***

### 1.3 Intensity and RPE / RIR-Based Autoregulation

**Core principle**  
External intensity (percentage of 1RM) and internal intensity (RPE or repetitions in reserve, RIR) are complementary ways to regulate load. RIR-based RPE allows autoregulation so athletes can adjust for day-to-day fatigue while targeting a desired proximity to failure.[^12]

**Evidence summary**  
Helms et al. compared RPE-based loading versus percentage 1RM in trained men over 8 weeks of DUP squat and bench programs; both groups significantly increased 1RM and muscle thickness, with non-significant but small effect size advantages favoring the RPE group in strength gains. Research indicates RPE anchored to RIR (e.g., RPE 7 ≈ 3 RIR) can prescribe effective training while allowing lifters to reduce load on “bad” days and increase it on “good” days without compromising outcomes. RPE accuracy improves with training experience; novices systematically misestimate proximity to failure, especially at lighter loads, whereas trained lifters are within ~1–2 reps of actual failure more consistently.[^13][^12]

**Application guideline (Ascent)**  
- Novice: Use percentage-based loads (e.g., 65–75% for sets of 8–12, 75–85% for sets of 4–6) with simple cues (“stop 2 reps before form breaks”) rather than full RPE scales.  
- Intermediate/advanced: Prescribe combined %1RM and target RIR (e.g., 3×5 at ~80% 1RM, RPE 7–8 / 2–3 RIR) and let the user adjust load to hit the RIR.[^12]
- For main strength lifts: Most working sets in the 3–8 rep range at RPE 7–9 (1–3 RIR), with occasional lower-RPE technique or power work.  
- Ascent should:  
  - Track estimated e1RM from recent sets and adjust percentage tables.  
  - Flag consistent RPE overshoot (>1 RPE above target) as potential underestimation of fatigue and adjust loads down ~2.5–5%.  
  - For users with limited logging skill, bias toward simple %1RM prescription and gradually introduce RPE when data show consistent execution.

**Key sources**  
- Helms et al. “RPE vs. Percentage 1RM Loading in Periodized Programs Matched for Sets and Repetitions.” Front Physiol, 2018.[^14][^12]
- Zourdos et al., work on daily undulating periodization and autoregulation in powerlifters.[^4][^2]

***

### 1.4 Frequency for Hypertrophy vs Strength

**Core principle**  
Training frequency per muscle group mainly matters as a way to distribute volume; when weekly volume is equated, hypertrophy is similar across a wide range of frequencies, while strength may benefit slightly from higher frequency due to more frequent practice of heavy lifts.[^15][^16][^5]

**Evidence summary**  
Schoenfeld’s 2016 frequency meta-analysis found that training a muscle group twice per week produced greater hypertrophy than once per week when volume was equated (effect sizes 0.49 vs 0.30). Later reviews suggest that, under volume-equated conditions, hypertrophy is broadly similar whether frequency is 1–3+ times per week, provided total weekly sets are matched, though strength and skill outcomes may still benefit from higher frequency in trained lifters. Other analyses indicate no clear additional benefit beyond two sessions per muscle for hypertrophy, but higher frequencies can be used for practical volume distribution and recovery.[^16][^17][^5][^15]

**Application guideline (Ascent)**  
- Hypertrophy: Default to training each major muscle group at least 2×/week; allow 3×/week if weekly volume per session would otherwise exceed ~8–10 hard sets.[^15][^16]
- Strength / technical lifts (squat, bench, deadlift, OHP): For intermediate/advanced lifters, program 2–3 exposures per week per lift at varying intensities and rep ranges.  
- Time-constrained users: Permit 1×/week per muscle if total weekly sets fall in the target volume range and soreness tolerance is acceptable, but flag this as suboptimal for most.  
- Ascent should choose frequency based on total intended weekly sets, schedule constraints, and soreness / recovery data.

**Key sources**  
- Schoenfeld et al. “Effects of Resistance Training Frequency on Measures of Muscle Hypertrophy: A Systematic Review and Meta-Analysis.” Sports Med, 2016.[^16][^15]
- Schoenfeld. “Resistance Training Frequency and Skeletal Muscle Hypertrophy: A Review of Available Evidence.” 2019.[^5]

***

### 1.5 Deload Protocols

**Core principle**  
Deloads are planned or reactive reductions in training stress to dissipate accumulated fatigue, restore performance, and allow supercompensation. They can reduce volume, intensity, or both for a short period (typically 5–10 days) within or between mesocycles.[^18][^11]

**Evidence summary**  
Direct experimental evidence on specific deload configurations is limited; most support comes from periodization studies and fatigue monitoring work showing that high, continuous loads increase fatigue markers and that temporary reductions in volume and/or intensity restore performance. Practical models (e.g., Israetel’s MRV framework) recommend proactive deloads every 3–6 weeks of hard training, with larger volumes and higher advancement requiring more frequent or deeper deloads. Research on strength and endurance tapers supports reducing volume ~30–60% while maintaining or slightly reducing intensity to preserve adaptations while reducing fatigue.[^19][^20][^11][^18][^1]

**Application guideline (Ascent)**  
- Proactive: Insert a deload week after 3–5 weeks of progressive overload or when approaching known MRV based on prior cycles.  
- Structure:  
  - Reduce volume by ~40–60% (sets per muscle) but keep intensity at ~70–85% of usual (no sets to failure, RPE capped at ~7).[^20][^11]
  - Alternatively, for highly beat-up joints, reduce both intensity (~60–75%) and volume (~30–50%) and focus on technique.  
- Reactive triggers:  
  - ≥2 weeks of declining performance at equal or higher RPE, persistent soreness, worsening sleep/HRV trend, or motivation drops.  
- Ascent should continuously monitor load, HRV, sleep, and subjective fatigue; when multiple indicators show strain, automatically propose a deload or insert a 3–4 day “recovery microcycle” with sharply reduced volume.

**Key sources**  
- Israetel & Hoffman, discussions of MRV and planned deloads in Renaissance Periodization materials.[^11][^1]
- Mølmen et al. “Block Periodization of Endurance Training – A Systematic Review and Meta-analysis.” Open Access J Sports Med, 2019 (volume-taper data).[^20]

***

### 1.6 Fatigue Management and SFR

**Core principle**  
Fatigue is both local (muscle-specific) and systemic (CNS, hormonal, psychological). The Stimulus-to-Fatigue Ratio (SFR) concept rates exercises and protocols by how much adaptation they produce relative to fatigue cost. Programs should favor exercises and schemes with high SFR for the user’s joints, skill, and goals.[^1][^11]

**Evidence summary**  
Research on HRV and training load shows that high training stress produces reductions in HRV and increased day-to-day variability, which associate with poorer adaptation and performance. Multi-joint free-weight lifts provide strong hypertrophy and strength stimulus but also impose higher systemic fatigue; machine and single-joint work can add local stimulus at lower systemic cost. Studies of periodization and fatigue monitoring in powerlifters suggest that organizing hypertrophy, strength, and power days with consideration for recovery (e.g., not placing highest-volume and heaviest sessions back-to-back) improves outcomes and hormonal responses.[^21][^22][^10][^5][^18][^19][^4]

**Application guideline (Ascent)**  
- Detect systemic fatigue via combinations of:  
  - Falling performance at equal RPE (or rising RPE at same load).  
  - Negative HRV trend or increased coefficient of variation (CV).  
  - Reports of poor sleep, high soreness, low motivation.[^22][^18]
- Exercise selection:  
  - Favor high-SFR compounds: e.g., front squats or safety-bar squats over very deep low-bar squats for some; Romanian deadlifts and leg presses to reduce lower-back fatigue versus frequent max-effort deadlifts.  
  - Use machines and isolation lifts to add volume for hypertrophy without excessive systemic fatigue.  
- Scheduling: Avoid stacking multiple very high-stress days; position the heaviest/most fatiguing sessions after rest or low-stress days.  
- Ascent should adapt by swapping or downgrading low-SFR exercises (for that user) when chronic fatigue markers accumulate.

**Key sources**  
- Altini, “Coefficient of Variation: What Is It and How Can You Use It?” HRV4Training blog, 2019 (HRV and CV as fatigue markers).[^22]
- Frontiers and other HRV fatigue reviews for athletes.[^18][^19]

***

### 1.7 Exercise Selection and Movement Hierarchies

**Core principle**  
Primary exercises are the main competition or high-transfer lifts; secondary movements are close variations to add volume or address weak links; tertiary lifts are accessories for local hypertrophy, stability, and balance. Exercise effectiveness depends on goal (strength in specific lift vs general hypertrophy) and individual tolerance.[^10][^5]

**Evidence summary**  
Research shows that multi-joint free-weight lifts (squat, bench press, deadlift, overhead press, rows) produce robust strength and hypertrophy and transfer to performance. Variations such as front squat, high-bar squat, and split squat target similar muscles with different joint angles and may reduce joint stress or change emphasis. Bench press variations (incline, close-grip, dumbbell) alter pectoral vs triceps emphasis but all support upper-body pushing strength. Row variations (barbell, chest-supported, seated cable) show similar hypertrophic potential when volume and effort are matched, but differ in spinal loading.[^5][^10]

**Application guideline (Ascent)**  
- Primary movements (for strength and skill):  
  - Squat pattern: high-bar or low-bar back squat, or front squat if mobility or back issues exist.  
  - Hip hinge: conventional or sumo deadlift, or trap-bar deadlift where joint stress is problematic.  
  - Horizontal press: barbell bench press (flat) or close-grip / incline if shoulders prefer.  
  - Vertical press: barbell or dumbbell overhead press.  
  - Row: barbell row or chest-supported row.  
- Secondary: paused squats, tempo squats, Romanian deadlifts, deficit deadlifts, incline bench, dumbbell bench, pull-ups, heavy rows at higher volumes.  
- Tertiary/accessory: split squats, leg presses, hamstring curls, lateral raises, flyes, face pulls, curls, triceps extensions.  
- Ascent should:  
  - Anchor each main lift to 1–2 primary variants.  
  - Add 1–3 secondary movements per session for additional volume and specific weaknesses.  
  - Rotate or down-rank exercises that repeatedly produce pain, poor technique, or disproportionate fatigue, replacing them with higher-SFR alternatives.

**Key sources**  
- Tzanetakis review on weekly training loads and hypertrophy (exercise considerations).[^10]
- Schoenfeld et al. volume and frequency work (multi-joint vs single-joint training).[^8][^5]

***

## 2. Endurance Training for Mountain Sports

### 2.1 Polarized Training (80/20 Model)

**Core principle**  
Polarized endurance training organizes most training time at low intensity (below first lactate/aerobic threshold) with a small portion at high intensity (near/above second lactate/anaerobic threshold), and minimal time in the moderate “threshold” middle zone.[^23][^24][^25]

**Evidence summary**  
Seiler’s work in multiple endurance sports describes a typical intensity distribution of ~80% low-intensity and 15–20% high-intensity work in successful athletes, measured by time or sessions. A 2024 meta-analysis reported that polarized distributions with ~75–80% low-intensity and 15–20% high-intensity significantly improve VO2max, VO2peak, and work economy compared with other patterns over short-term interventions. These findings are consistent across runners, cyclists, rowers, and skiers.[^26][^25][^23]

**Application guideline (Ascent)**  
- For recreational mountain athletes:  
  - Target ~75–85% of endurance time in low-intensity hiking, easy running, or cycling where breathing is comfortable and conversation is possible (RPE ~2–3/10).[^24][^23]
  - Allocate ~15–20% to high-intensity intervals: hill repeats, tempo climbs, or VO2max intervals, usually 1–3 times per week depending on volume and season.[^25]
- In base periods: Skew toward even more low intensity (~85–90%) and minimal high intensity.  
- Ascent should classify sessions via HR and RPE (mapping to zones) and maintain a running 2–4 week intensity distribution, auto-reducing high-intensity prescription if the proportion exceeds ~20% or HRV and soreness show accumulating fatigue.

**Key sources**  
- Seiler & Tønnessen. Analyses of training intensity distribution in elite endurance athletes.[^23][^26]
- Fiskerstrand & Seiler. “Training and Performance in the Norwegian Rowing Team.” 2004.[^23]
- Recent meta-analysis: “The Effect of Polarized Training Intensity Distribution on Maximal Oxygen Uptake and Work Economy,” 2024.[^25]

***

### 2.2 Zone-Based Training and HR

**Core principle**  
Intensity zones can be organized into three broad physiological domains (Zone 1 below first ventilatory/lactate threshold, Zone 2 between thresholds, Zone 3 above second threshold) or subdivided into 5 zones. For hiking/touring without power, heart rate and perceived exertion are primary tools to anchor these zones.[^26][^23]

**Evidence summary**  
Seiler’s 3-zone HR model identifies Zone 1 as below the aerobic threshold (roughly 60–75% of HRmax), Zone 2 between aerobic and anaerobic thresholds, and Zone 3 above the anaerobic threshold (~85–95% HRmax), though individual variation is high. Threshold-based HR prescriptions approximate aerobic threshold around 65–75% HRmax and lactate threshold around 80–90% HRmax for many recreational athletes, but direct testing (lactate or gas exchange) is more accurate. Educational resources and practice guidelines recommend mapping RPE to zones when HR is noisy or altitude/cold alter cardiovascular responses.[^26][^23]

**Application guideline (Ascent)**  
- Without lab data, estimate:  
  - Zone 1 (easy): 60–75% HRmax, RPE 2–3/10 (nose-breathing, conversational pace).  
  - Zone 2/“tempo”: 75–85% HRmax, RPE 4–6/10 (can speak in short phrases).  
  - Zone 3+ (threshold to VO2max): 85–95%+ HRmax, RPE 7–10/10 (few words, breathing hard).  
- Ascent should:  
  - Use wearable HR to infer individual thresholds over time (e.g., HR at sustainable 30–60 min uphill efforts vs HR at 10–20 min best efforts).  
  - Allow the user to calibrate zones manually after key efforts.  
  - Emphasize RPE back-up when HR is unreliable (cold, dehydration, high altitude). 

**Key sources**  
- OpenLearn Polarized Training overview (Seiler’s 3-zone model).[^23]
- FastTalk Labs guide to polarized training with Dr. Seiler.[^24][^26]

***

### 2.3 Vertical-Specific Conditioning

**Core principle**  
Mountain endurance (ski touring, loaded hiking, hike & fly approaches) relies on sustained sub-threshold climbing with high demand on local muscular endurance of quads, calves, glutes, and hip flexors, plus high aerobic capacity at grade. Training must progressively increase vertical gain and time-on-feet while respecting tissue tolerance.[^25][^23]

**Evidence summary**  
Uphill locomotion increases relative metabolic cost versus level ground; climbing VO2 at a given speed is significantly higher due to vertical work and altered biomechanics. Work on trail and mountain runners shows that uphill-specific sessions (graded hill intervals, long climbs) improve both VO2max at grade and neuromuscular adaptations relevant to climbing. Strength-endurance training of knee extensors and plantar flexors (e.g., loaded step-ups, split squats, calf raises) improves economy and fatigue resistance in uphill tasks.[^27][^25][^23]

**Application guideline (Ascent)**  
- Progression variables:  
  - Weekly vertical gain (m), continuous climb duration, pack weight, and surface/steepness.  
- For recreational ski touring / hiking:  
  - Base: Start with 1–2 dedicated uphill sessions per week (e.g., 45–90 min continuous Z1–low Z2 climb or stair/step-up equivalents) and gradually add 10–20% vertical gain per week if recovery is good.  
  - Build: Include 1 uphill interval session/week (e.g., 4–8 × 5–10 min at upper Zone 2–low Zone 3 on climb with easy descents).  
- Ascent should cap weekly increases in vertical gain to ~10–20% depending on user history, monitor soreness/HRV, and reduce progression when negative trends appear.

**Key sources**  
- Seiler and polarized training work applied to skiers and runners.[^26][^25][^23]
- Strength for endurance athletes reviews referencing incline-specific adaptations.[^27]

***

### 2.4 Altitude Considerations (1500–3000 m)

**Core principle**  
Training and touring at moderate altitude reduce oxygen availability, raising heart rate and perceived effort for a given speed while impairing recovery until acclimatization occurs. HR zones remain broadly useful, but pace and power targets must be adjusted downward.[^28][^29]

**Evidence summary**  
Classical altitude training reviews describe living and training at 1800–2700 m for 3–4 weeks, which can increase total hemoglobin mass and improve sea-level performance in some but not all athletes. Acute exposure causes higher submaximal HR at given workloads and reduced VO2max; as acclimatization progresses over ~7–21 days, HR at submaximal workloads trends back toward sea-level values. Applied resources emphasize that HR reflects internal load reasonably well at altitude, while pace or power lag.[^30][^31][^32][^29][^28]

**Application guideline (Ascent)**  
- When user is at 1500–3000 m:  
  - Expect resting and submaximal HR to be elevated in the first week; maintain intensity prescriptions based on HR/RPE, not pace.  
  - Reduce planned training volume and especially high-intensity work by ~20–30% for the first 5–7 days; expand gradually as symptoms and HR normalize.[^30][^28]
- For planned altitude trips, Ascent should:  
  - Build an acclimatization microcycle with conservative Z1–Z2 volume and minimal intervals in the first days at altitude.  
  - Use resting HR, HRV, and submax HR at known workloads to infer acclimatization progress and adjust training.  

**Key sources**  
- Friedmann-Bette. “Classical Altitude Training.” Scand J Med Sci Sports, 2008.[^28]
- Beidleman et al. “Preparation for Endurance Competitions at Altitude: Physiological, Psychological, and Environmental Factors.” 2018.[^29]
- HIIT Science / HRV4Training case reports on HRV and HR at altitude.[^30]

***

### 2.5 Sport-Specific Demands

#### 2.5.1 Splitboarding / Ski Touring

**Core principle**  
Ski touring and splitboarding involve sustained sub-threshold climbs with a pack in cold conditions, followed by technical descents demanding leg strength, power, and agility, often for multiple hours or days.[^25][^23]

**Evidence summary**  
Endurance ski research shows that elite Nordic skiers follow polarized or block-periodized models with large volumes of low-intensity work on skis plus targeted high-intensity sessions, yielding high VO2max and excellent economy. Cold exposure and load carriage increase energy expenditure and strain, while repeated eccentric loading from descents stresses quadriceps and connective tissues.[^20][^23][^25]

**Application guideline (Ascent)**  
- Winter macrocycle structure:  
  - Base (early winter): Emphasize long Z1 touring, progressive vertical gain, and strength maintenance for legs and trunk.  
  - Build: Introduce 1–2 weekly high-intensity uphill sessions (intervals or tempo climbs) and some technical descent sessions.  
  - Peak: 1–3 weeks of slightly reduced volume with specific long outings mimicking target tours.  
  - Maintain: During dense touring periods, reduce gym work to 1–2 short full-body strength sessions focused on maintenance.  
- Ascent should interpret touring days as structured endurance sessions (estimating TSS-equivalent via HR and vertical), reduce other endurance intensity during heavy tour weeks, and auto-classify descents as additional leg fatigue when planning lower-body strength work.

#### 2.5.2 Hike & Fly (Paragliding)

**Core principle**  
Hike & fly emphasizes fast, often steep uphill hiking with a 10–15 kg pack under time pressure, followed by flight phases; demands are more intensity-biased and time-constrained than casual hiking.[^23][^25]

**Evidence summary**  
The primary demands resemble steep uphill trail running with load: high aerobic capacity, strong local muscular endurance, and tolerance for high percentages of VO2max for 30–90 minutes. Load carriage literature shows additional metabolic cost and altered biomechanics with added pack weight, elevating HR and RPE for given speeds.[^27][^25]

**Application guideline (Ascent)**  
- Emphasize:  
  - Steep uphill intervals with pack (e.g., 6–10 × 4–6 min at upper Zone 2–Zone 3, downhill walking recovery).  
  - Continuous loaded climbs (30–60+ min) at race-like gradients.  
- Season plan:  
  - Pre-season: Build general aerobic base and leg strength.  
  - In-season: 1 key uphill interval session + 1–2 longer loaded climbs per week; gym strength at maintenance.  
- Ascent should categorize hikes with >600–800 m vertical gain and >10 kg pack as high-stress sessions and adapt subsequent training accordingly.

#### 2.5.3 Resort Snowboarding

**Core principle**  
Resort snowboarding is high-intensity intermittent work: bouts of leg- and trunk-intensive effort on descents separated by rest on lifts. This resembles repeated-sprint or high-intensity interval patterns.[^33][^34]

**Evidence summary**  
Sleep- and fatigue-related research on high-intensity intermittent exercise shows that such efforts are very sensitive to sleep debt and recovery status. Repeated eccentric and isometric contractions in lower body contribute to delayed-onset muscle soreness and neuromuscular fatigue similar to other intermittent field sports.[^34][^33]

**Application guideline (Ascent)**  
- Classify resort days as:  
  - “High-intensity intermittent lower-body” days, roughly equivalent to a hard interval or small-sided game session.  
- On heavy resort days (several hours of active riding):  
  - Reduce or omit separate lower-body strength sessions within the next 24 hours.  
  - Emphasize recovery (sleep, nutrition, light mobility).  
- Ascent should adjust weekly lower-body load upwards slightly in base periods if resort time is low, and downwards when multiple intense resort days are logged.

***

### 2.6 Endurance Progression and the 10% Rule

**Core principle**  
Endurance volume (time, distance, vertical) must progress gradually to avoid overuse injuries; the popular “10% rule” (no more than 10% weekly volume increase) is a rough heuristic rather than an absolute limit.[^35][^23]

**Evidence summary**  
Endurance nutrition and training guidelines acknowledge the need for gradual volume increases and adequate fueling but emphasize that tolerance varies with training age and prior load. HRV and fatigue-monitoring literature indicates that rapid spikes in training load and monotony (low variation) associate with maladaptation and increased injury risk.[^36][^19][^35][^18][^22]

**Application guideline (Ascent)**  
- For recreational mountain athletes with stable training:  
  - Default to 5–10% weekly increases in total endurance time and vertical gain when last 2–3 weeks have been well tolerated.  
  - Allow up to 15–20% temporary increases for highly conditioned athletes if recovery markers remain solid, but reduce the following week (step-loading approach).  
- Ascent should track rolling 4-week load (e.g., average weekly vertical and duration), flag acute:chronic load spikes (>20–30%), and auto-adjust planned increases when HRV, sleep, or soreness markers deteriorate.

**Key sources**  
- HRV and training load monitoring literature.[^19][^18][^22]
- Endurance training and nutrition overview articles.[^35][^36]

***

## 3. Concurrent Training (Strength + Endurance)

### 3.1 Interference Effect

**Core principle**  
Concurrent training refers to combining strength and endurance training within the same program. The “interference effect” is the potential for endurance work to blunt strength, power, or hypertrophy gains compared with strength-only training, largely via molecular (AMPK vs mTOR) and recovery interactions.[^37][^38][^39]

**Evidence summary**  
Wilson et al.’s 2012 meta-analysis found that concurrent strength + endurance training led to smaller improvements in strength and power than strength training alone, particularly when endurance volume and frequency were high and when running (vs cycling) was used. Hypertrophy was less affected, with concurrent training still producing substantial hypertrophy compared with endurance-only training. More recent systematic reviews report that concurrent training generally does not significantly compromise maximal strength or hypertrophy in practical programs, though power adaptations can be more sensitive. The magnitude of interference in recreational athletes performing moderate endurance loads appears modest when sessions are well scheduled.[^38][^39][^37]

**Application guideline (Ascent)**  
- Expect some trade-offs when high volumes of running or hard endurance work are combined with heavy strength emphasis, particularly for lower-body power.  
- For recreational mountain athletes, interference is acceptable if:  
  - Strength is maintained or slowly improved in-season while endurance is prioritized.  
  - Strength-focused blocks are placed in off-season or early pre-season with relatively lower endurance volume.  
- Ascent should:  
  - Monitor strength performance trends during endurance-heavy phases; if 1RMs or key rep performances drop >5–10% for several weeks, reduce endurance intensity or volume slightly and prioritize recovery.  

**Key sources**  
- Wilson et al. “Concurrent Training: A Meta-Analysis Examining Interference of Aerobic and Resistance Exercises.” J Strength Cond Res, 2012.[^37][^38]
- Recent systematic review: “Concurrent Strength and Endurance Training: A Systematic Review and Meta-analysis” (2023).[^39]

***

### 3.2 Scheduling Strength and Endurance

**Core principle**  
The order, proximity, and type of concurrent sessions influence interference. Greater separation in time, smart sequencing, and limiting overlapping fatigue help reduce negative interactions.[^38][^39][^37]

**Evidence summary**  
Meta-analytic data show that running-based endurance training more negatively impacts strength and hypertrophy than cycling, and that higher frequency and longer duration of endurance sessions correlate with larger decrements in strength and hypertrophy adaptations. Reviews suggest that placing strength and endurance on separate days, or at least separating them by several hours (≥6 h), reduces interference, especially when high-intensity endurance work is involved. When sessions are same-day, performing strength before endurance tends to preserve strength development better, particularly for lower body.[^39][^37][^38]

**Application guideline (Ascent)**  
- Ideal: Alternate strength and endurance days (e.g., Mon/Wed/Fri strength, Tue/Thu endurance).  
- If same-day is necessary:  
  - Strength first, endurance later in the day, with at least 6 hours between sessions when possible.  
  - For athletes prioritizing endurance, occasional endurance-first days are acceptable, but heavy lower-body strength should not follow exhaustive endurance.
  
- Sport-specific: When cycling or ski-specific work can substitute for running, prefer those modalities during strength-development phases to reduce impact forces and interference.  
- Ascent should detect same-day planned sessions and, if ordering is suboptimal (e.g., long run then heavy squats), prompt reordering or downscaling of the second session.

**Key sources**  
- Wilson et al. concurrent training meta-analysis.[^37][^38]
- Updated reviews on concurrent high-intensity interval training and resistance training compatibility.[^39][^37]

***

### 3.3 Priority Periodization Across the Year

**Core principle**  
Concurrent programs for mountain athletes should shift emphasis across macrocycles: off-season strength focus, pre-season concurrent development, and in-season endurance/sport focus with strength maintenance.[^7][^27][^20]

**Evidence summary**  
Block periodization frameworks separate concentrated blocks of strength and endurance work to reduce overlap and enhance adaptations. Reviews of block periodized endurance training show small to moderate benefits in VO2max and maximal power compared with traditional mixed distributions. Strength training of endurance athletes improves economy and performance when integrated thoughtfully, especially when scheduled in dedicated blocks or carefully periodized with endurance load.[^6][^7][^27][^20]

**Application guideline (Ascent)**  
- For a typical mountain athlete:  
  - Off-season (late summer/autumn): Strength priority—3–4 weekly strength sessions, 2–3 low- to moderate-intensity endurance sessions for maintenance.  
  - Pre-winter (late autumn/early winter): Concurrent—2–3 strength sessions and 3–4 endurance sessions, adding ski-specific vertical work.  
  - In-season winter touring: Endurance/sport priority—2–4 touring days/week; strength downshifted to 1–2 short, heavy, low-volume sessions.  
  - Summer hike & fly: Endurance and sport skill priority with similar pattern; any heavy strength work concentrated in gaps between big objectives.  
- Ascent should implement explicit “priority tags” for blocks (strength, endurance, balanced) and automatically bias training prescriptions and fatigue decisions accordingly.

**Key sources**  
- Issurin, “Benefits and Limitations of Block Periodized Training Approaches.”[^7]
- Mølmen et al. “Block Periodization of Endurance Training – A Systematic Review and Meta-analysis.”[^20]
- Issurin et al. “Strength Training of Endurance Athletes” (Acta Kinesiologica, overview).[^27]

***

### 3.4 Strength Maintenance During Endurance Phases

**Core principle**  
Strength and muscle can be maintained with substantially lower volume and frequency than needed to build them, provided some exposure to heavy loading is preserved.[^40][^1]

**Evidence summary**  
A systematic review on minimum effective training dose for strength in resistance-trained men reports that a single set of 6–12 repetitions at ~70–85% 1RM, performed 1–3 times per week, is sufficient to induce significant 1RM strength gains, implying that this is above pure maintenance dose. Maintenance volume landmarks (MV) are typically around 4–8 sets per muscle per week, much less than MEV/MAV. Concurrent training meta-analyses show that strength can be preserved or modestly improved even alongside substantial endurance work when at least 1–2 heavy sessions per week are maintained.[^41][^40][^11][^1][^37][^39]

**Application guideline (Ascent)**  
- In endurance/sport-priority phases:  
  - Program 1–2 full-body strength sessions per week.  
  - For key lifts/muscle groups, aim for ~4–8 total hard sets per week in moderate rep ranges (3–8 reps) at ~75–85% 1RM (RPE ~7–8).[^40][^1]
  - Avoid training to failure; focus on quality, fast reps, and joint-friendly movements.  
- Ascent should detect shifts into heavy endurance blocks and automatically transition from hypertrophy/strength-building templates to maintenance templates, substantially reducing volume but retaining intensity.

**Key sources**  
- Baz-Valle et al. “The Minimum Effective Training Dose Required to Increase 1RM Strength in Resistance-Trained Men: A Systematic Review and Meta-analysis.” 2020.[^41][^40]
- Israetel / RP volume landmarks resources.[^11][^1]

***

## 4. Recovery and Readiness

### 4.1 HRV as a Readiness Marker

**Core principle**  
Heart rate variability (HRV), especially vagally mediated indices like rMSSD and Ln rMSSD, reflect autonomic balance and can track adaptation and fatigue over time. Rolling averages and coefficients of variation are more informative than single daily readings.[^42][^18][^19]

**Evidence summary**  
Plews and colleagues have highlighted both potential and complexity in HRV monitoring among elite endurance athletes, noting that individual HRV profiles vary and that both increases and decreases in HRV can represent positive or negative adaptation depending on context. Time-domain HRV measures (rMSSD, Ln rMSSD) from short morning recordings are considered practical indicators of parasympathetic activity. Flatt and others report that HRV-guided training can improve VO2max and performance versus fixed plans, with reductions in HRV or increased day-to-day variability (higher CV) indicating poor adaptation and suggesting the need to reduce load. Studies show that lower CV of rMSSD during increased-load weeks corresponds with better performance gains, while higher CV and depressed baselines indicate maladaptation.[^43][^44][^45][^42][^18][^22][^19]

**Application guideline (Ascent)**  
- Metrics to use:  
  - 7-day rolling mean of morning Ln rMSSD.  
  - 7-day coefficient of variation (CV) of Ln rMSSD.  
- Rules of thumb:  
  - Baseline within individual normal range and stable/gradually rising + low or reducing CV → coping well with training.  
  - Marked drop in baseline below normal with increased CV sustained ≥3–4 days → accumulated fatigue; reduce intensity/volume 20–40% or insert extra easy days.[^42][^22]
- Ascent should integrate HRV data where available and treat it as one input among several (sleep, RPE, soreness, performance), not as a sole decision-maker. When HRV conflicts with subjective readiness, Ascent should bias toward caution if multiple objective markers (HRV, resting HR) are adverse.

**Key sources**  
- Plews et al. “HRV Monitoring in Elite Endurance Athletes.”[^44]
- Altini, HRV4Training blog on coefficient of variation and training adaptation.[^22]
- HRV-guided training systematic review and trials (e.g., Nuuttila et al., 2017; HRV-based VO2max improvements).[^42]

***

### 4.2 Sleep and Performance

**Core principle**  
Sleep quantity and quality are strong determinants of both strength and endurance performance and of adaptation to training. Acute and chronic sleep restriction impair performance, especially in high-intensity and skill-demanding tasks.[^33][^34]

**Evidence summary**  
Experimental work in endurance athletes shows that extending sleep (e.g., from ~7 to >8 h/night) over several nights improves time-trial performance by ~3%, while restricting sleep to ~5 h/night impairs performance by a similar magnitude compared with normal ~7 h. A 2024 meta-analysis of acute sleep deprivation in athletes found an overall effect size of −0.56 on performance, with more severe decrements for high-intensity intermittent exercise (ES −1.57) and skill control (ES −1.06). Even partial sleep loss late in the night had substantial negative effects.[^34][^33]

**Application guideline (Ascent)**  
- General target:  
  - At least 7–9 h/night for most athletes, with “red flag” thresholds <6 h for more than 1–2 consecutive nights before hard sessions.[^33][^34]
- If sleep is significantly reduced (e.g., <6 h) before a planned high-intensity or heavy strength day, Ascent should:  
  - Reclassify to moderate or low intensity, or propose swapping with an easier day.  
  - Limit same-day high neuromuscular or high-skill demands (technical descents, heavy squats).  
- Over 7–14 day windows, Ascent should consider average sleep in recovery assessments and adjust deload timing and progression rates accordingly.

**Key sources**  
- HIIT Science article on sleep duration and endurance performance.[^33]
- Meta-analysis “Effects of Acute Sleep Deprivation on Sporting Performance in Athletes,” 2024.[^34]

***

### 4.3 Subjective Readiness and Wearable “Body Battery”

**Core principle**  
Subjective measures (fatigue scales, soreness, motivation) and composite wearable metrics (e.g., Garmin Body Battery) provide practical but imperfect insights into readiness. Disagreement between objective and subjective markers should be resolved conservatively.

**Evidence summary**  
Research on perceived fatigue and RPE confirms that simple scales (0–10 or 1–5) correlate with performance and physiological stress in many contexts; high perceived fatigue often predicts poor training outcomes even when HRV is normal. Wearable “body battery” metrics are proprietary composites of HRV, HR, sleep, and activity; limited independent validation exists, but internal documentation suggests they track overall stress well qualitatively. HRV reviews note that HRV alone cannot distinguish all fatigue types and should be interpreted alongside subjective indicators.[^31][^32][^44][^18][^19]

**Application guideline (Ascent)**  
- Ascent should collect:  
  - Daily perceived fatigue (e.g., 1–5), soreness, and motivation.  
  - Optional wearable recovery scores (Body Battery, readiness).  
- Decision rules:  
  - If both subjective and objective markers indicate poor readiness (high fatigue, low HRV/readiness), downscale or reschedule high-intensity work.  
  - If subjective is poor but HRV/readiness normal, consider moderating intensity but allow user choice; suggest emphasizing technique, mobility, or easy endurance.  
  - If subjective is good but objective markers poor, err on caution for high-risk sessions (max strength, technical descents, very long tours) while still allowing some moderate training.

**Key sources**  
- HRV fatigue-monitoring reviews.[^18][^19]
- HRV4Training and wearable-based trend detection guides.[^22][^30]

***

### 4.4 Nutrition for Recovery (Protein, Carbs, Hydration)

**Core principle**  
Sufficient protein, carbohydrate, and hydration are essential to support training adaptation, especially under concurrent strength and endurance loads.

**Evidence summary**  
Meta-analyses show that protein intakes around 1.6 g/kg/day optimize fat-free mass gains with resistance training, with little additional benefit beyond ~1.6–2.2 g/kg/day in most. Position stands for athletes recommend protein in the 1.2–2.0 g/kg/day range, with higher values (up to ~2.4 g/kg) during energy restriction. Endurance nutrition guidelines suggest carbohydrate intakes of 5–7 g/kg/day for general training, 6–10 g/kg/day for 1–3 h/day of moderate–high intensity, and 8–12 g/kg/day for 4–5 h/day, with 1–1.2 g/kg/h for 3–5 h post-exercise for optimal glycogen resynthesis after long events. Adequate hydration and electrolytes are particularly important at altitude to maintain plasma volume and performance.[^46][^47][^48][^49][^50][^29][^36][^35]

**Application guideline (Ascent)**  
- Protein:  
  - Default 1.6–2.2 g/kg/day for users regularly strength training; at least 1.2–1.6 g/kg/day when primarily endurance-focused.[^47][^50]
  - Encourage distribution across 3–4+ meals with ~0.3–0.5 g/kg per meal including post-exercise.  
- Carbohydrate:  
  - 3–5 g/kg/day on light days; 5–7 g/kg/day on moderate days (~1 h endurance); 6–10 g/kg/day when doing 1–3 h/day of endurance or ski touring; up to 8–12 g/kg/day for very long days or multi-day tours.[^46][^36][^35]
  - After long or intense sessions, 1.0–1.2 g/kg/h for 3–4 h or 8–10 g/kg in the first 24 h.  
- Hydration:  
  - Encourage starting sessions euhydrated, replacing fluid losses (~0.4–0.8 L/h depending on conditions) and including sodium in long, sweaty, or hot/altitude sessions.[^49][^35]
- Ascent should provide daily macro targets based on planned training load and body mass, and flag when logged intake appears substantially inadequate for recovery.

**Key sources**  
- Morton et al. “A Systematic Review, Meta-Analysis and Meta-Regression of the Effect of Protein Supplementation on Resistance Training-Induced Gains in Muscle Mass and Strength in Healthy Adults.” 2018.[^50]
- Bagheri et al. review on protein intake and performance.[^48]
- Burke et al., and subsequent guidelines on carbohydrate needs in endurance athletes.[^49][^36][^35]

***

### 4.5 Deload and Recovery Weeks at Mesocycle Level

**Core principle**  
Recovery weeks between accumulation blocks allow dissipation of fatigue and consolidation of adaptations (supercompensation).[^6][^7][^20]

**Evidence summary**  
Block periodization research shows that concentrated loading phases followed by recovery microcycles or tapers enhance performance compared with continuous high-load training. Endurance and strength studies supporting tapers report that reducing volume 30–60% while maintaining or slightly reducing intensity over 1–3 weeks improves performance (e.g., VO2max, time-trial, 1RM).[^7][^6][^20]

**Application guideline (Ascent)**  
- For 3–6 week mesocycles:  
  - Plan 2–5 weeks of progressive overload followed by ~1 week of reduced volume (30–60% lower) at maintained intensity (or slightly reduced intensity for heavily fatigued athletes).  
- For concurrent mountain athletes:  
  - Consider alternating emphasis blocks (e.g., 3 weeks strength-focused + 1 recovery, then 3 weeks endurance-focused + 1 recovery) rather than constantly high loads in both domains.  
- Ascent should schedule these recovery weeks proactively in annual plans and retain flexibility to bring one forward if multi-indicator fatigue flags are triggered.

**Key sources**  
- Issurin periodization reviews.[^6][^7]
- Mølmen et al. block periodization meta-analysis.[^20]

***

## 5. Periodization for the Recreational Mountain Athlete

### 5.1 Annual Planning (Macrocycle)

**Core principle**  
A recreational mountain athlete’s year should align with seasonal sports (winter ski touring, summer hiking/flying) and maintain strength year-round, shifting priorities across macrocycle phases.

**Evidence summary**  
Block and traditional periodization reviews support annual plans that cycle through accumulation, intensification, and realization phases, with block approaches showing small advantages for trained athletes when peaks are well-timed. Strength training improves endurance performance and economy when integrated into endurance athletes’ annual plans, particularly when heavy phases avoid periods of maximal endurance stress.[^27][^7][^6][^20]

**Application guideline (Ascent)**  
- Example yearly structure for someone in a climate like Tromsø:  
  - Autumn (Sep–Nov): Strength priority + base endurance.  
  - Winter (Dec–Mar): Ski touring/splitboard priority with strength maintenance.  
  - Spring (Apr–May): Transition + general conditioning; rebuild structured strength and running/hiking base.  
  - Summer (Jun–Aug): Hike & fly and hiking priority with 1–2 strength sessions/week.  
- Ascent should allow user to define primary sports and seasons, then auto-generate a macrocycle with block tags (strength, endurance, mixed) and adjust as objectives are added.

**Key sources**  
- Issurin block periodization reviews.[^7][^6]
- Strength training for endurance athletes overview.[^27]

***

### 5.2 Mesocycle Design

**Core principle**  
Mesocycles (3–6 weeks) structure medium-term training with clear goals (accumulation, intensification, realization) for both strength and endurance.

**Evidence summary**  
Block periodization frameworks commonly use 2–4 week concentrated load blocks followed by 1 week recovery or transition. Endurance block meta-analysis suggests small but meaningful improvements in VO2max and performance with block over mixed traditional structures in trained athletes. Strength programs similarly benefit from cycles of higher volume followed by higher intensity.[^6][^7][^20]

**Application guideline (Ascent)**  
- Typical mesocycle templates:  
  - 3-week load + 1-week deload (for higher volumes).  
  - 4–5-week load + 1–2-week taper/realization for event peaking.  
- For concurrent mountain athletes:  
  - Strength-focused mesocycle: increase strength session volume and/or intensity while keeping endurance mostly low-intensity base.  
  - Endurance-focused mesocycle: increase vertical gain and Z2–Z3 work while strength is held at MV–MEV.  
- Ascent should tag each mesocycle with clear goals and adjust decision rules (e.g., tolerance for fatigue, progression rate) accordingly.

**Key sources**  
- Issurin periodization reviews.[^7][^6]
- Mølmen et al. block periodization meta-analysis.[^20]

***

### 5.3 Microcycle Templates (Weekly Structure)

**Core principle**  
Microcycles (weekly plans) must coordinate strength, endurance, and sport sessions with adequate rest days and logical ordering to manage fatigue and minimize interference.

**Evidence summary**  
Concurrent training research emphasizes separating high-intensity strength and endurance when possible, sequencing strength before endurance on same days, and including rest or low-stress days. HRV and fatigue literature support including at least one low-load day per week to facilitate autonomic recovery.[^38][^19][^18][^37][^39]

**Application guideline (Ascent)**  
Example patterns (S = strength, E = endurance, T = sport day, R = rest/recovery):  
- 4-day week (busy recreational):  
  - Mon S (full body), Wed E (intervals/hills), Fri S (full body), Sat/Sun T (long tour/hike) with other days light or off.  
- 5-day week:  
  - Mon S (lower + upper), Tue E (Z1–Z2), Thu S (lower + upper), Fri intervals/hills, Sun long Z1–Z2 or tour; Wed/Sat lighter or rest.  
- 6-day week (highly motivated):  
  - Mon S (heavy), Tue E (Z1–Z2), Wed S (lighter/volume), Thu E intervals, Sat T long, Sun E Z1; one half-day or low-stress day mid-week.  
- Ascent should:  
  - Avoid scheduling heavy lower-body strength immediately after long/hard mountain days.  
  - Ensure at least 1 full rest or active recovery day weekly.  
  - Adjust microcycle intensity distribution dynamically based on recent HRV, sleep, and soreness.

**Key sources**  
- Concurrent training meta-analyses.[^37][^39]
- HRV fatigue-monitoring reviews.[^19][^18]

***

### 5.4 Tapering for Events and Objectives

**Core principle**  
Tapering reduces training load before key events to reduce fatigue while maintaining fitness, typically by reducing volume more than intensity.

**Evidence summary**  
Endurance taper literature commonly supports a 1–3 week taper with 40–60% volume reduction and maintained intensity for optimal performance improvements. For strength, similar short tapers (4–7 days) with reduced volume but retained intensity preserve or slightly improve 1RM.[^29][^6][^20]

**Application guideline (Ascent)**  
- For single key objectives (e.g., multi-day touring trip, long hike & fly):  
  - 7–14 day taper: reduce endurance volume to ~50–70% of peak, maintain intensity via a few short intervals or moderate climbs, and keep 1–2 light strength sessions (lower volume, similar intensity, no failure).[^29][^20]
  - Emphasize sleep, nutrition, and logistics (gear practice, pack testing).  
- Ascent should detect user-flagged objectives and automatically insert a taper, depending on event length and importance, adjusting longer for multi-day expeditions.

**Key sources**  
- Mølmen et al. block periodization and taper data.[^20]
- Altitude and endurance event preparation work.[^29]

***

### 5.5 Autoregulation at Plan Level

**Core principle**  
Training plans must adapt to real-world fluctuations in health, stress, and performance. Autoregulation at the plan level decides when to modify, extend, or abandon mesocycles.

**Evidence summary**  
HRV-guided training interventions show benefits of adjusting training based on physiological readiness versus strictly following pre-planned loads. Reviews on HRV and fatigue emphasize monitoring trends and adjusting training when signs of poor adaptation accumulate. Concurrent and periodization research shows that adjusting load and schedule when athletes fail to respond prevents stagnation and overtraining.[^18][^19][^42][^22][^6][^7]

**Application guideline (Ascent)**  
- Criteria to modify within mesocycle:  
  - 1–2 weeks of stagnant or declining performance on key lifts or endurance markers at similar or higher RPE.  
  - Persistent negative trends in HRV baseline and increased CV, alongside poor sleep or mood.  
- Criteria to insert extra deload/recovery week:  
  - Combined objective and subjective strain (HRV down, sleep reduced, soreness high) for >7–10 days.  
- Criteria to abandon/restructure:  
  - Injury, major illness, or repeated training interruptions >2 weeks; shift to rebuilding block.  
- Ascent should implement a scoring system integrating performance, HRV, sleep, and self-report to trigger suggestions (e.g., “extend block 1 week”, “insert deload now”, “restart with lower volume”).

**Key sources**  
- HRV-guided training review and trials.[^42]
- HRV fatigue-monitoring frameworks.[^19][^18][^22]
- Issurin and block periodization reviews.[^6][^7]

***

## 6. Biomarker Integration

### 6.1 Blood Markers Relevant to Training Adaptation

**Core principle**  
Key blood markers provide insight into oxygen transport, hormonal recovery status, inflammation, micronutrient sufficiency, and thyroid function, all of which influence training tolerance and performance.

**Evidence summary**  
Iron status: Ferritin reflects iron stores; low ferritin (<20–30 ng/mL) is strongly associated with iron deficiency and reduced endurance performance, with several sources suggesting cut-offs of 30–50 ng/mL for optimal athletic function. Iron status reviews note performance differences between ferritin below vs above ~30 ng/mL and improved performance with iron repletion into ranges 30–99 ng/mL. Hormones: Testosterone:cortisol ratio is sometimes used as a marker of training stress, but evidence is mixed; trends over time (e.g., falling testosterone, rising cortisol) may suggest under-recovery. Inflammation: High-sensitivity C-reactive protein (hs-CRP) indicates systemic inflammation; chronically elevated values can signal excessive stress or underlying illness. Vitamin D and thyroid (TSH, free T4) status also affect energy, mood, and performance.[^51][^52][^53][^54][^18][^19]

**Application guideline (Ascent)**  
- Core panel for endurance and strength athletes:  
  - CBC, ferritin, serum iron, transferrin saturation.  
  - TSH and free T4 (± free T3).  
  - 25(OH) vitamin D.  
  - hs-CRP.  
  - Optionally total and free testosterone, SHBG, cortisol in appropriate context.  
- Ascent should not diagnose but can:  
  - Flag low ferritin (<30–40 ng/mL) as potential contributor to fatigue and suggest medical consultation.[^52][^54][^51]
  - Flag very high ferritin (>200–300 ng/mL) for evaluation of iron overload or inflammation.  
  - Suggest follow-up when CRP is elevated or thyroid markers abnormal.  

**Key sources**  
- Rodenberg & Gustafson review on ferritin and iron in athletes (referenced by endurance guides).[^51]
- “Iron Status and Physical Performance in Athletes.” 2023 review.[^54]
- Practical guides to athletic blood testing.[^53]

***

### 6.2 When to Retest

**Core principle**  
Regular but not excessive blood testing helps track slow-changing markers (iron, vitamin D, thyroid) and adjust training and nutrition.

**Evidence summary**  
Endurance and sports-medicine guides suggest 6–12 month intervals for routine panels in healthy athletes, with more frequent checks (every 3–6 months) when correcting deficiencies such as iron or vitamin D, or when symptom-driven adjustments are ongoing.[^52][^53][^54]

**Application guideline (Ascent)**  
- Healthy recreational athletes:  
  - Comprehensive panel every 6–12 months.  
  - Iron/ferritin and vitamin D every 6 months if previously low or if at high risk (heavy endurance load, altitude training, menstruating athletes).  
- Ascent should allow users to log lab dates and values, then nudge for retesting based on prior abnormalities and time elapsed (e.g., >6 months since low ferritin reading).

**Key sources**  
- Iron and endurance athlete guidance.[^54][^51][^52]
- Athlete-focused lab testing guides.[^53]

***

### 6.3 Red-Flag Lab Values for Training Modification or Medical Referral

**Core principle**  
Certain lab values should prompt conservative training modifications and medical consultation before continuing heavy training.

**Evidence summary**  
Iron: Ferritin <10–20 ng/mL is strongly indicative of iron deficiency anemia and requires medical evaluation. Endurance athletes may benefit from using higher cut-offs (≤30–40 ng/mL) to identify functional deficits. Thyroid: Markedly abnormal TSH (e.g., >4–5 mIU/L or suppressed) or low free T4 suggest thyroid dysfunction that impacts training capacity. Inflammation: Persistent elevated hs-CRP above reference range can indicate ongoing inflammation or illness. Kidney and liver markers significantly out of range also require medical management.[^52][^53][^54]

**Application guideline (Ascent)**  
- Ascent should flag:  
  - Ferritin <20–30 ng/mL (especially with symptoms) as requiring medical consultation and potential iron treatment; reduce high-intensity and very long endurance loads until addressed.[^54][^52]
  - Ferritin >300 ng/mL or consistently high CRP for further evaluation.  
  - Any clearly abnormal kidney/liver function markers or major hormone derangements (as user-reported) as reasons to pause aggressive training and seek care.  
- The system must avoid giving treatment advice; instead, it should recommend seeking a physician and potentially suggest temporary decrease in training load.

**Key sources**  
- “Iron and the Endurance Athlete.” TrainingPeaks article summarizing clinical cut-offs.[^51]
- “Iron Status and Physical Performance in Athletes.” 2023 review.[^54]
- Athlete blood test guides.[^53]

***

### 6.4 Creatine Supplementation and Kidney Markers

**Core principle**  
Creatine monohydrate is an effective supplement for strength and some performance domains and is generally safe for kidney function in healthy individuals, but it can raise serum creatinine, which may appear as reduced estimated GFR on standard lab tests.[^55][^56][^57][^58]

**Evidence summary**  
Recent systematic reviews and meta-analyses report that creatine supplementation causes a small but statistically significant increase in serum creatinine (e.g., mean difference ~0.07 mg/dL) without significant changes in directly measured GFR or clinically relevant kidney dysfunction in healthy populations. Narrative and systematic reviews emphasize that elevated creatinine in creatine users may reflect increased creatine/creatinine turnover rather than kidney damage and recommend using alternative renal markers (e.g., cystatin C) or interpreting creatinine with this context in mind. Case reports indicate that individuals with pre-existing kidney disease may be at higher risk if using creatine without medical supervision.[^56][^59][^57][^58][^55]

**Application guideline (Ascent)**  
- Creatine for performance:  
  - Standard dosing: 3–5 g/day of creatine monohydrate; optional loading (e.g., 20 g/day for 5–7 days) is not necessary for long-term benefits.[^57]
  - Benefits include increased strength, power, lean mass, and potential small benefits for repeated high-intensity efforts; evidence for endurance benefits is mixed but may include improved sprint capacity during endurance events.[^58][^57]
- Lab interpretation:  
  - If a user reports elevated creatinine after starting creatine but normal eGFR or cystatin C and no symptoms, Ascent should note that creatine can raise creatinine without impairing kidney function and recommend discussing with a clinician rather than automatically stopping training.[^55][^56][^57]
  - For users with kidney disease or concerning lab trends, Ascent should flag creatine use as a topic for immediate medical consultation and avoid recommending it.  

**Key sources**  
- “Effect of Creatine Supplementation on Kidney Function.” 2025 meta-analysis.[^56][^55]
- Longobardi et al. “Is It Time for a Requiem for Creatine Supplementation-Induced Kidney Failure?” Nutrients, 2023.[^57]
- 2025 literature review on creatine and kidney disease.[^59][^58]

---

## References

1. [How to Program Volume Landmarks: MRV, MAV, and MEV ...](https://fitnessrec.com/articles/how-to-program-volume-landmarks-mrv-mav-and-mev-explained-for-optimal-muscle-growth) - These landmarks include: Maintenance Volume (MV) - minimum to maintain muscle, Minimum Effective Vol...

2. [[PDF] Daily-Undulating-Periodization-Research-Zourdos-et-al ... - Lift Vault](https://liftvault.com/wp-content/uploads/2017/07/Daily-Undulating-Periodization-Research-Zourdos-et-al-2012-LiftVault.com_.pdf)

3. [Volume Landmarks - Reinassance Periodization](https://volume-landmarks-rp-rals.vercel.app) - Volume Landmarks for Hypertrophy Training. Visualize all the volume landmarks from the Renaissance P...

4. [Modified Daily Undulating Periodization Model Produces ...](https://pubmed.ncbi.nlm.nih.gov/26332783/) - The primary aim of this study was to compare 2 daily undulating periodization (DUP) models on one-re...

5. [Review Resistance training frequency and skeletal muscle hypertrophy: A review of available evidence](https://www.sciencedirect.com/science/article/abs/pii/S1440244018308624) - Current reviews and position stands on resistance training (RT) frequency and associated muscular hy...

6. [Issurin, V. (2008). Block periodization versus traditional training theory](https://coachsci.sdsu.edu/csa/vol161/issurin.htm)

7. [Benefits and Limitations of Block Periodized Training Approaches to ...](https://www.semanticscholar.org/paper/Benefits-and-Limitations-of-Block-Periodized-to-A-Issurin/e26b149acabc65f37c86d7e821d5e3c1a5f4a603) - It is suggested that block periodization of strength and Endurance training induces superior adaptat...

8. [[PDF] Dose-response relationship between weekly resistance training volume and increases in muscle mass: A systematic review and meta-analysis | Semantic Scholar](https://www.semanticscholar.org/paper/Dose-response-relationship-between-weekly-training-Schoenfeld-Ogborn/0d34206f962394983054451cddd8a3b91818f732) - The findings indicate a graded dose-response relationship whereby increases in RT volume produce gre...

9. [Dose-response relationship between weekly resistance training ...](https://pubmed.ncbi.nlm.nih.gov/27433992/) - The purpose of this paper was to systematically review the current literature and elucidate the effe...

10. [The effects on muscle hypertrophy of different weekly training loads ...](https://www.tzanetakis.com/en/the-effects-on-muscle-hypertrophy-of-different-weekly-training-loads-in-resistance-training/) - Introduction: Resistance training (RT) has been observed for many decades that it has positive effec...

11. [▷ Maximum Recoverable Volume – Optimise your training!【2026 】](https://www.hsnstore.eu/blog/sports/fitness/maximum-recoverable-volume/) - MRV is the maximum volume from which an athlete can recover, generally defined as the recovery from ...

12. [Frontiers | RPE vs. Percentage 1RM Loading in Periodized Programs Matched for Sets and Repetitions](https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2018.00247/full) - Purpose: To investigate differences between rating of perceived exertion (RPE) and percentage one-re...

13. [Table 3 from RPE vs. Percentage 1RM Loading in Periodized Programs Matched for Sets and Repetitions | Semantic Scholar](https://www.semanticscholar.org/paper/RPE-vs.-Percentage-1RM-Loading-in-Periodized-for-Helms-Byrnes/232921d13544e846cad5975257c5137a30210d04/figure/4) - TABLE 3 | Example RPE load adjustments. - "RPE vs. Percentage 1RM Loading in Periodized Programs Mat...

14. [RPE vs. Percentage 1RM Loading in Periodized Programs Matched for Sets and Repetitions](https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2018.00247/pdf)

15. [Effects of Resistance Training Frequency on Measures of Muscle](https://elementssystem.com/wp-content/uploads/2018/04/schoenfeld-frequency.pdf)

16. [[PDF] Effects of Resistance Training Frequency on Measures of Muscle Hypertrophy: A Systematic Review and Meta-Analysis | Semantic Scholar](https://www.semanticscholar.org/paper/Effects-of-Resistance-Training-Frequency-on-of-A-Schoenfeld-Ogborn/384a4adc7317f92e5b56533b54367e6eedeff73a) - It can be inferred that the major muscle groups should be trained at least twice a week to maximize ...

17. [Training Frequency for Muscle Growth: What the Data Say](https://www.ironmaglabs.com/forums/threads/training-frequency-for-muscle-growth-what-the-data-say.26620/) - A lot of people asked whether higher training frequencies were also better for hypertrophy. I respon...

18. [Frontiers | Monitoring Fatigue Status with HRV Measures in Elite Athletes: An Avenue Beyond RMSSD?](https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2015.00343/full) - Among the tools proposed to assess the athlete's “fatigue,” the analysis of heart rate variability (...

19. [Effects of varying training load on heart rate variability and ...](https://www.sciencedirect.com/science/article/abs/pii/S144024401830402X)

20. [Block periodization of endurance training – a systematic review and ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC6802561/) - Block periodization (BP) has been proposed as an alternative to traditional (TRAD) organization of t...

21. [Daily Undulating Periodization & Performance Improvements in Powerlifters](https://optimumsportsperformance.com/blog/daily-undulating-periodization-performance-improvements-in-powerlifters/)

22. [Coefficient of Variation (CV): what is it and how can you ...](https://www.hrv4training.com/blog2/coefficient-of-variation-cv-what-is-it-and-how-can-you-use-it) - Blog post by Marco Altini In this blog post we cover our latest update in HRV4Training Pro , which m...

23. [6.1 Polarised training (or 80/20 training) | OpenLearn](https://www.open.edu/openlearn/health-sports-psychology/training-endurance-sport-and-fitness/content-section-6.1) - In this free course you will explore an important aspect of strength and conditioning which refers t...

24. [Complete Guide to Polarized Training with Dr. Stephen Seiler](https://www.fasttalklabs.com/pathways/polarized-training/) - Explore polarized training for cycling, triathlon, and running with this guide from Dr. Stephen Seil...

25. [The Effect of Polarized Training Intensity Distribution on Maximal ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC11679080/) - High-intensity training (HIT) has commonly been the most effective training method for improvement i...

26. [Polarized Training 101: Dr. Stephen Seiler’s Deep Dive into 80/20 Endurance Training](https://www.youtube.com/watch?v=bxEaAbcO64s) - In this episode of the Fast Talk Podcast from Fast Talk Laboratories, we’re honored to be joined by ...

27. [[PDF] Issurin, VB et. al.: Strength training of endurance athletes... Acta ...](https://akinesiologica.com/wp-content/uploads/2020/04/003.pdf) - Biological background of block periodized endurance training: A review. Sports Med, 49(1): 31–39. Is...

28. [Classical altitude training - Friedmann‐Bette - 2008](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1600-0838.2008.00828.x) - During classical altitude training, athletes live and train at moderate altitudes of about 1500–3000...

29. [Preparation for Endurance Competitions at Altitude: Physiological ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC6218926/) - Beidleman and colleagues demonstrated physiologic adaptations and improved time-trial exercise perfo...

30. [Adaptation and HRV in Elite Triathletes during Altitude Training](https://hiitscience.com/hrv-altitude-training/) - A typical pattern of positive adaptation to an altitude camp shows submaximal exercise HR initially ...

31. [How Altitude Impacts Your Performance - COROS](https://coros.com/stories/d/how-altitude-impacts-performace) - Decreased power output or pace at given intensities. These effects start becoming noticeable above a...

32. [How Altitude Impacts Your Performance - COROS](https://coros.com/stories/coros-coaches/c/how-altitude-impacts-performace) - COROS GPS Watches & Training Tools for Endurance Athletes

33. [Impact of Sleep Duration on Athletes and Endurance Performance](https://hiitscience.com/sleep-endurance-performance/) - Discover the importance of sleep for athletic recovery and performance in endurance athletes. Learn ...

34. [Effects of Acute Sleep Deprivation on Sporting Performance in Athletes](https://www.tandfonline.com/doi/full/10.2147/NSS.S467531) - Using meta-analysis to comprehensively and quantitatively evaluate the impact of acute sleep depriva...

35. [Nutrition and Supplement Update for the Endurance Athlete - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6628334/) - Background: Endurance events have experienced a significant increase in growth in the new millennium...

36. [Guidelines for daily carbohydrate intake: do athletes achieve them?](https://pubmed.ncbi.nlm.nih.gov/11310548/) - Official dietary guidelines for athletes are unanimous in their recommendation of high carbohydrate ...

37. [[PDF] Concurrent Training: A Meta-Analysis Examining Interference of Aerobic and Resistance Exercises | Semantic Scholar](https://www.semanticscholar.org/paper/Concurrent-Training:-A-Meta-Analysis-Examining-of-Wilson-Mar%C3%ADn/26fb11d95a94c238a4cd70dd5df04a5bce2aa9ba) - The results indicate that interference effects of endurance training are a factor of the modality, f...

38. [Concurrent training: a meta-analysis examining interference of aerobic ...](https://pubmed.ncbi.nlm.nih.gov/22002517/) - The primary objective of this investigation was to identify which components of endurance training (...

39. [Concurrent Strength and Endurance Training: A Systematic Review and ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC10933151/) - Many sports require maximal strength and endurance performance. Concurrent strength and endurance tr...

40. [The Minimum Effective Training Dose Required to Increase 1RM Strength ...](https://pubmed.ncbi.nlm.nih.gov/31797219/) - This systematic review was registered with PROSPERO (CRD42018108911).

41. [The minimum effective training dose required to in...](https://sponet.fi/Record/4059872) - Background: Increases in muscular strength may increase sports performance, reduce injury risk, are ...

42. [HRV-Based Training for Improving VO 2max in Endurance Athletes ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC7663087/) - This review aimed to synthesize evidence regarding interventions based on heart rate variability (HR...

43. [HRVtraining | HRV research and consulting by Andrew Flatt Ph.D.](https://hrvtraining.com) - HRV research and consulting by Andrew Flatt Ph.D.

44. [HRV Monitoring in Elite Endurance Athletes | PDF | Heart Rate - Scribd](https://www.scribd.com/document/833055123/Plewsetal2013-SportsMed) - The article discusses the use of heart rate variability (HRV) as a non-invasive tool for monitoring ...

45. [Ultra-Short-Term Heart Rate Variability Indexes at Rest and Post ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC4126289/) - The purpose of this study was to evaluate the agreement of the vagal-related heart rate variability ...

46. [Prioritizing Carbohydrates: A Guide for Endurance Runners | USU](https://extension.usu.edu/nutrition/research/prioritizing-carbohydrates-a-guide-for-endurance-runners) - This article teaches runners how to use carbohydrates for best performance.

47. [How Much Protein Do Athletes Really Need?](https://www.scienceforsport.com/how-much-protein-do-athletes-really-need/) - This guest blog post explores the science behind how much protein athletes really need, in addition ...

48. [The effect of protein intake on athletic performance - PMC - NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC11613885/) - The impact of a protein-rich diet and protein supplements on athletic performance remains a topic of...

49. [DIETARY CARBOHYDRATE AND THE ENDURANCE ATHLETE](https://www.gssiweb.org/sports-science-exchange/article/dietary-carbohydrate-and-the-endurance-athlete-contemporary-perspectives)

50. [A systematic review, meta-analysis and meta-regression of the effect of protein supplementation on resistance training-induced gains in muscle mass and strength in healthy adults](https://bjsm.bmj.com/content/52/6/376) - Objective We performed a systematic review, meta-analysis and meta-regression to determine if dietar...

51. [Iron and the Endurance Athlete (1)](https://www.trainingpeaks.com/blog/iron-and-the-endurance-athlete/) - Is iron really that important for endurance athletes? How can you tell if you may have an iron defic...

52. [Iron Strength: What Endurance Athletes Should Know About Iron ...](https://www.usatriathlon.org/articles/training-tips/what-endurance-athletes-should-know-about-iron-deficiency-anemia-and-ferritin-screening) - “Doc, can you please check my ferritin?” Endurance athletes often want to know what their ferritin l...

53. [Athlete's Blood Test Guide: Markers for Peak Performance](https://www.gogeviti.com/blog/athletes-blood-test-guide-markers-for-peak-performance) - Discover the essential blood test markers every athlete should track to optimize performance, speed ...

54. [Iron Status and Physical Performance in Athletes - PMC - NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC10608302/) - Iron is an important mineral in the body, essential for muscle function and oxygen transport. Adequa...

55. [Effect of creatine supplementation on kidney function - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12590749/) - Creatine monohydrate is a widely used dietary supplement with proven benefits in athletic performanc...

56. [Effect of creatine supplementation on kidney function - PubMed](https://pubmed.ncbi.nlm.nih.gov/41199218/) - Not applicable.

57. [Is It Time for a Requiem for Creatine Supplementation-Induced Kidney ...pmc.ncbi.nlm.nih.gov › articles › PMC10054094](https://pmc.ncbi.nlm.nih.gov/articles/PMC10054094/) - Creatine has become one of the most popular dietary supplements among a wide range of healthy and cl...

58. [Creatine Supplementation and its Impact on Renal Function](https://ijmra.in/v8i3/60.php)

59. [The impact of creatine supplementation on the development of ...](https://apcz.umk.pl/QS/article/view/57864) - Introduction: Creatine, a widely studied dietary supplement, is known for enhancing athletic perform...

