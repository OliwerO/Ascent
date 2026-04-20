#!/usr/bin/env python3
"""Build and upload mobility workouts (Protocols A/B/C) to Garmin Connect.

Library + CLI. Used by:
  - workout_generator.py (imports build_workout / build_step_list)
  - workout_push.py      (imports build_step_list to prepend Protocol B
                          warm-up steps to a strength session)
  - coach_adjust.py      (shells out via --protocol A --push --json-out)
  - health-coach SKILL   (shells out for Tuesday/rest mobility days)

CLI:
    python mobility_workout.py --protocol A --json-out                # build only
    python mobility_workout.py --protocol A --date 2026-04-07 --push  # upload + schedule
    python mobility_workout.py --protocol B --target A --json-out     # B for squat day
    python mobility_workout.py --protocol C --json-out
    python mobility_workout.py --protocol A --date 2026-04-07 --push --write-planned --json-out

stdout: single-line JSON when --json-out is set; full JSON otherwise.
stderr: human logs.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,  # keep stdout clean for --json-out
)
log = logging.getLogger("mobility_workout")


# ---------------------------------------------------------------------------
# Garmin exercise mapping (mobility / stretch / yoga library)
# ---------------------------------------------------------------------------

EXERCISE_MAP: dict[str, tuple[str, str]] = {
    # Protocol A
    "Cat-Cow":                  ("WARM_UP",       "CAT_CAMEL"),
    "Ankle Mobilization":       ("WARM_UP",       "ANKLE_DORSIFLEXION_WITH_BAND"),
    "Hip Flexor Stretch":       ("WARM_UP",       "ELBOW_TO_FOOT_LUNGE"),
    "90/90 Hip Stretch":        ("HIP_STABILITY", "HIP_CIRCLES"),
    "Thoracic Rotation":        ("WARM_UP",       "THORACIC_ROTATION"),
    "Figure-4 Stretch":         ("HIP_STABILITY", "SUPINE_HIP_INTERNAL_ROTATION"),
    # Protocol B (shared)
    "Foam Roll T-Spine":        ("WARM_UP",       "FOAM_ROLLER"),
    "Foam Roll Hamstrings":     ("WARM_UP",       "FOAM_ROLLER"),
    "Foam Roll Lats":           ("WARM_UP",       "FOAM_ROLLER"),
    "Goblet Squat Hold":        ("WARM_UP",       "GOBLET_SQUAT"),
    "World's Greatest Stretch": ("WARM_UP",       "WORLDS_GREATEST_STRETCH"),
    "Bodyweight Squat":         ("WARM_UP",       "BODY_WEIGHT_SQUAT"),
    "Single-Leg RDL":           ("WARM_UP",       "SINGLE_LEG_DEADLIFT"),
    "Inchworm":                 ("WARM_UP",       "INCHWORM"),
    "Good Morning":             ("WARM_UP",       "GOOD_MORNING"),
    "90/90 Hip Switch":         ("HIP_STABILITY", "HIP_CIRCLES"),
    "Wall Slides":              ("WARM_UP",       "WALL_SLIDE"),
    "Band Pull-Aparts":         ("WARM_UP",       "BAND_PULL_APART"),
    "Thread the Needle":        ("WARM_UP",       "THORACIC_ROTATION"),
    "Half-Kneeling OH Press":   ("WARM_UP",       "HALF_KNEELING_OVERHEAD_PRESS"),
    # Protocol C
    "Couch Stretch":            ("WARM_UP",       "COUCH_STRETCH"),
    "Calf Stretch":             ("WARM_UP",       "STANDING_CALF_STRETCH"),
    "Pigeon Pose":              ("HIP_STABILITY", "PIGEON_POSE"),
    "Doorway Pec Stretch":      ("WARM_UP",       "DOORWAY_PEC_STRETCH"),
    "Jefferson Curl":           ("WARM_UP",       "JEFFERSON_CURL"),
    "Reverse Lunge":            ("WARM_UP",       "REVERSE_LUNGE"),
    "Tempo RDL":                ("WARM_UP",       "ROMANIAN_DEADLIFT"),
    "Touring Stride":           ("WARM_UP",       "WALKING_LUNGE"),
    "Prone I-T-Y":              ("WARM_UP",       "PRONE_I_T_Y"),
    "Leg Swings":               ("WARM_UP",       "LEG_SWING"),
    "Spiderman Lunge":          ("WARM_UP",       "SPIDERMAN_LUNGE"),
    "Overhead Band Distraction": ("WARM_UP",      "OTHER"),
}

# 1–2 sentence cues sourced from domain-9 §9.1–9.6. Used by health-coach SKILL
# to render the Slack mobility-day card and by ask-coach for grounded answers.
EXERCISE_CUES: dict[str, str] = {
    "Cat-Cow":                  "Spinal segmental wake-up — exhale to round, inhale to extend; 8–10 cycles.",
    "Ankle Mobilization":       "Half-kneeling, knee tracks over 2nd–3rd toe with the heel planted. Critical for ski boot interface and squat depth.",
    "Hip Flexor Stretch":       "Squeeze the glute, tuck the pelvis (PPT), reach the same-side arm overhead for an added lat stretch.",
    "90/90 Hip Stretch":        "Sit tall, lean forward over the front shin with a straight spine. Front hip = ER, back hip = IR.",
    "Thoracic Rotation":        "Side-lying open book — 5 controlled reps with a 5s end-range hold; addresses pack/harness posture.",
    "Figure-4 Stretch":         "Cross ankle over opposite knee, pull the bottom leg toward the chest. Hip ER capsule.",
    "Foam Roll T-Spine":        "Segmental extension — pause at each segment 10–15s and exhale over the roller.",
    "Foam Roll Hamstrings":     "30s per area per side; pause on tender points without breath-holding.",
    "Foam Roll Lats":           "Side-lying, roller at armpit level; rotate the palm up to bias the lat.",
    "Goblet Squat Hold":        "Prying — elbows pry knees out, shift weight side to side at the bottom.",
    "World's Greatest Stretch": "Lunge → elbow to instep → rotate and reach → straighten the front leg.",
    "Bodyweight Squat":         "Sit tall, full depth, 3s pause at the bottom — groove the pattern.",
    "Single-Leg RDL":           "Active hamstring lengthening under control; hips square, slow eccentric.",
    "Inchworm":                 "Walk hands out → push hips high → pedal feet → walk feet to hands.",
    "Good Morning":             "Hinge with hands behind head, reach one arm to the opposite foot for rotation.",
    "90/90 Hip Switch":         "Flow from one side to the other actively — 5 transitions each direction.",
    "Wall Slides":              "Back flat to wall, forearms on wall, slide arms up while maintaining contact.",
    "Band Pull-Aparts":         "Light band, slow tempo, retract scapulae before the arms move.",
    "Thread the Needle":        "Quadruped — hand behind head, rotate up toward the ceiling (2s pause), then under.",
    "Half-Kneeling OH Press":   "Light DB; tests overhead mobility under load and stretches the rear-leg hip flexor.",
    "Couch Stretch":            "Rear foot elevated against the wall — work toward an upright torso. Deep hip flexor / quad.",
    "Calf Stretch":             "Straight knee = gastroc, bent knee = soleus. Both feed ankle dorsiflexion.",
    "Pigeon Pose":              "Front shin angled, back leg long — hip ER capsule. Use figure-4 if pigeon is uncomfortable.",
    "Doorway Pec Stretch":      "Forearm on doorframe at 90°, step through. Counteracts protracted shoulder posture.",
    "Jefferson Curl":           "Light load only; segmental flexion, total control, stop at any pain.",
    "Reverse Lunge":            "Deficit (front foot on plate) — 3s pause at the bottom, hip flexor stretch on the trailing leg.",
    "Tempo RDL":                "4s eccentric, 2s pause at the bottom — hamstring length under control.",
    "Touring Stride":           "Alternating deep lunges with arm drive and overhead reach — mimics uphill touring.",
    "Prone I-T-Y":              "Lower trap, mid-trap, serratus — 8 reps each shape. Critical for brake toggle endurance.",
    "Leg Swings":               "Standing, full ROM hip swings — sagittal then frontal plane.",
    "Spiderman Lunge":          "Walking — deep lunge, same-side arm overhead reach, touring + pack pattern.",
    "Overhead Band Distraction": "Band anchored behind at waist, loop around upper arm, step forward, small circles. Opens subacromial space.",
}


# ---------------------------------------------------------------------------
# Protocols
# Step format: (name, description, side, reps_or_none, duration_s_or_none)
# "__REST__" entries become Garmin rest/transition steps on the watch.
# ---------------------------------------------------------------------------

_StepTuple = tuple[str, str, str | None, int | None, int | None]

PROTOCOL_A: list[_StepTuple] = [
    ("Cat-Cow",            "Spinal segmental wake-up", None, None, 60),
    ("__REST__",           "Transition to half-kneeling", None, None, 10),
    ("Ankle Mobilization", "Knee over 2nd-3rd toe, heel planted", "R", None, 30),
    ("Ankle Mobilization", "Knee over 2nd-3rd toe, heel planted", "L", None, 30),
    ("Ankle Mobilization", "Set 2", "R", None, 30),
    ("Ankle Mobilization", "Set 2", "L", None, 30),
    ("Hip Flexor Stretch", "Squeeze glute, tuck pelvis, reach arm overhead", "R", None, 30),
    ("Hip Flexor Stretch", "Squeeze glute, tuck pelvis, reach arm overhead", "L", None, 30),
    ("Hip Flexor Stretch", "Set 2", "R", None, 30),
    ("Hip Flexor Stretch", "Set 2", "L", None, 30),
    ("__REST__",           "Transition to seated", None, None, 10),
    ("90/90 Hip Stretch",  "Sit tall, lean forward with straight spine", "R", None, 45),
    ("90/90 Hip Stretch",  "Sit tall, lean forward with straight spine", "L", None, 45),
    ("__REST__",           "Transition to side-lying", None, None, 10),
    ("Thoracic Rotation",  "5 reps + 5s end-range hold", "R", 5, None),
    ("Thoracic Rotation",  "5 reps + 5s end-range hold", "L", 5, None),
    ("Figure-4 Stretch",   "Ankle over opposite knee, pull toward chest", "R", None, 30),
    ("Figure-4 Stretch",   "Ankle over opposite knee, pull toward chest", "L", None, 30),
]

# Protocol B variants — keyed by the strength session_key they precede.
# 'A' = squat day (B1), 'B' = upper-body day (B3), 'C' = hinge day (B2).
# Sets aligned with KB §9.6 Protocol B prescriptions.
PROTOCOL_B_BY_TARGET: dict[str, list[_StepTuple]] = {
    "A": [  # Squat day → ankle/hip/thoracic (KB B1: 2×10 ankle, 3×15s goblet, 2×5 squat)
        ("Foam Roll T-Spine",        "Segmental T-spine extension",     None, None, 120),
        ("__REST__",                  "Transition to half-kneeling",     None, None, 10),
        ("Ankle Mobilization",       "Banded if available",              "R", 10, None),
        ("Ankle Mobilization",       "Banded if available",              "L", 10, None),
        ("Ankle Mobilization",       "Set 2",                            "R", 10, None),
        ("Ankle Mobilization",       "Set 2",                            "L", 10, None),
        ("__REST__",                  "Get kettlebell",                   None, None, 10),
        ("Goblet Squat Hold",        "Prying, 8–12 kg KB",               None, None, 15),
        ("Goblet Squat Hold",        "Set 2",                             None, None, 15),
        ("Goblet Squat Hold",        "Set 3",                             None, None, 15),
        ("__REST__",                  "Transition",                       None, None, 10),
        ("World's Greatest Stretch", "Elbow to instep, rotate, reach",   "R", 3, None),
        ("World's Greatest Stretch", "Elbow to instep, rotate, reach",   "L", 3, None),
        ("Bodyweight Squat",         "3s pause at bottom",               None, 5, None),
        ("Bodyweight Squat",         "Set 2",                             None, 5, None),
    ],
    "B": [  # Upper-body day → thoracic/shoulder/scapular (KB B3: 2×8 wall, 2×10 band, 2×8 thread, 2×5 press)
        ("Foam Roll T-Spine", "Segmental T-spine extension + lats",  None, None, 120),
        ("__REST__",           "Transition to standing",               None, None, 10),
        ("Wall Slides",       "Back flat, slide arms up",            None, 8, None),
        ("Wall Slides",       "Set 2",                                None, 8, None),
        ("Band Pull-Aparts",  "Light band, slow tempo",              None, 10, None),
        ("Band Pull-Aparts",  "Set 2",                                None, 10, None),
        ("__REST__",           "Transition to quadruped",              None, None, 10),
        ("Thread the Needle", "Quadruped thoracic rotation",         "R", 8, None),
        ("Thread the Needle", "Quadruped thoracic rotation",         "L", 8, None),
        ("Thread the Needle", "Set 2",                                "R", 8, None),
        ("Thread the Needle", "Set 2",                                "L", 8, None),
        ("__REST__",           "Transition to half-kneeling",          None, None, 10),
        ("Half-Kneeling OH Press", "5 kg DB — overhead mobility",    "R", 5, None),
        ("Half-Kneeling OH Press", "5 kg DB — overhead mobility",    "L", 5, None),
        ("Half-Kneeling OH Press", "Set 2",                           "R", 5, None),
        ("Half-Kneeling OH Press", "Set 2",                           "L", 5, None),
    ],
    "C": [  # Hinge day → hamstring/hip/posterior chain (KB B2: 2×5 90/90, 2×6 SL-RDL, 2×8 GM)
        ("Foam Roll Hamstrings",     "30s per area per side",           None, None, 120),
        ("__REST__",                  "Transition to seated",            None, None, 10),
        ("90/90 Hip Switch",         "5 transitions each direction",     None, 10, None),
        ("90/90 Hip Switch",         "Set 2",                            None, 10, None),
        ("__REST__",                  "Transition to standing",           None, None, 10),
        ("Single-Leg RDL",           "Bodyweight, slow eccentric",       "R", 6, None),
        ("Single-Leg RDL",           "Bodyweight, slow eccentric",       "L", 6, None),
        ("Single-Leg RDL",           "Set 2",                            "R", 6, None),
        ("Single-Leg RDL",           "Set 2",                            "L", 6, None),
        ("Inchworm",                 "Walk out → downdog → walk in",     None, 5, None),
        ("Good Morning",             "Hinge + reach, BW",                None, 8, None),
        ("Good Morning",             "Set 2",                            None, 8, None),
    ],
}

# Protocol C — dedicated 40–45 min session. Five phases, aligned with KB §9.6.
# Multi-set exercises now match KB prescriptions. __REST__ steps provide
# transition time between position changes.
PROTOCOL_C: list[_StepTuple] = [
    # Phase 1: Foam rolling preparation (5 min)
    ("Foam Roll T-Spine",     "Phase 1: segmental extension at 4–5 segments", None, None, 90),
    ("Foam Roll Hamstrings",  "Phase 1: quads + rectus femoris on front",      "R", None, 30),
    ("Foam Roll Hamstrings",  "Phase 1: quads + rectus femoris on front",      "L", None, 30),
    ("Figure-4 Stretch",      "Phase 1: glute / piriformis release",           "R", None, 30),
    ("Figure-4 Stretch",      "Phase 1: glute / piriformis release",           "L", None, 30),
    ("Foam Roll Lats",        "Phase 1: side-lying, roller at armpit",         "R", None, 30),
    ("Foam Roll Lats",        "Phase 1: side-lying, roller at armpit",         "L", None, 30),
    # Phase 2: Dynamic mobility flow (8 min)
    ("__REST__",               "Transition to Phase 2: dynamic flow",          None, None, 10),
    ("Cat-Cow",                "Phase 2: 10 full-spine cycles",                None, None, 60),
    ("World's Greatest Stretch","Phase 2",                                     "R", 3, None),
    ("World's Greatest Stretch","Phase 2",                                     "L", 3, None),
    ("__REST__",               "Transition to seated",                          None, None, 10),
    ("90/90 Hip Switch",       "Phase 2: 6 transitions each direction",        None, 12, None),
    ("__REST__",               "Transition to standing",                        None, None, 10),
    ("Spiderman Lunge",        "Phase 2: deep lunge + overhead reach",         "R", 5, None),
    ("Spiderman Lunge",        "Phase 2: deep lunge + overhead reach",         "L", 5, None),
    ("Leg Swings",             "Phase 2: sagittal + frontal, full ROM",        None, 20, None),
    # Phase 3: Loaded stretching (12 min) — KB: 3×20s goblet, 2×6/side lunge,
    # 2×8 tempo RDL, 2×5 jefferson, 2×5/side OH press
    ("__REST__",               "Get kettlebell for Phase 3",                    None, None, 10),
    ("Goblet Squat Hold",      "Phase 3: prying, 12–16 kg KB, 20s holds",      None, None, 20),
    ("Goblet Squat Hold",      "Phase 3 set 2",                                None, None, 20),
    ("Goblet Squat Hold",      "Phase 3 set 3",                                None, None, 20),
    ("__REST__",               "Transition",                                    None, None, 10),
    ("Reverse Lunge",          "Phase 3: deficit, 3s pause at bottom",         "R", 6, None),
    ("Reverse Lunge",          "Phase 3: deficit, 3s pause at bottom",         "L", 6, None),
    ("Reverse Lunge",          "Phase 3 set 2",                                "R", 6, None),
    ("Reverse Lunge",          "Phase 3 set 2",                                "L", 6, None),
    ("Tempo RDL",              "Phase 3: 4s eccentric, 2s pause",              None, 8, None),
    ("Tempo RDL",              "Phase 3 set 2",                                None, 8, None),
    ("Jefferson Curl",         "Phase 3: light load, 5s down 5s up",           None, 5, None),
    ("Jefferson Curl",         "Phase 3 set 2",                                None, 5, None),
    ("__REST__",               "Transition to half-kneeling",                   None, None, 10),
    ("Half-Kneeling OH Press", "Phase 3: 8 kg KB",                             "R", 5, None),
    ("Half-Kneeling OH Press", "Phase 3: 8 kg KB",                             "L", 5, None),
    ("Half-Kneeling OH Press", "Phase 3 set 2",                                "R", 5, None),
    ("Half-Kneeling OH Press", "Phase 3 set 2",                                "L", 5, None),
    # Phase 4: Static stretching (10 min) — KB: 2×45s/side couch, 30s gastroc +
    # 30s soleus each side, 60s/side pigeon, 2×45s thoracic, 45s/side pec
    ("__REST__",               "Transition to Phase 4: static holds",           None, None, 10),
    ("Couch Stretch",          "Phase 4: work toward upright torso",            "R", None, 45),
    ("Couch Stretch",          "Phase 4 set 2",                                "R", None, 45),
    ("Couch Stretch",          "Phase 4",                                       "L", None, 45),
    ("Couch Stretch",          "Phase 4 set 2",                                "L", None, 45),
    ("__REST__",               "Transition to standing",                        None, None, 10),
    ("Calf Stretch",           "Phase 4: gastroc — straight knee",             "R", None, 30),
    ("Calf Stretch",           "Phase 4: gastroc — straight knee",             "L", None, 30),
    ("Calf Stretch",           "Phase 4: soleus — bent knee",                  "R", None, 30),
    ("Calf Stretch",           "Phase 4: soleus — bent knee",                  "L", None, 30),
    ("__REST__",               "Transition to floor",                           None, None, 10),
    ("Pigeon Pose",            "Phase 4: hip ER capsular stretch",             "R", None, 60),
    ("Pigeon Pose",            "Phase 4: hip ER capsular stretch",             "L", None, 60),
    ("Thoracic Rotation",      "Phase 4: supine extension on roller, Y arms",  None, None, 45),
    ("Thoracic Rotation",      "Phase 4 set 2",                                None, None, 45),
    ("__REST__",               "Transition to doorway",                         None, None, 10),
    ("Doorway Pec Stretch",    "Phase 4: 90° forearm",                         "R", None, 45),
    ("Doorway Pec Stretch",    "Phase 4: 90° forearm",                         "L", None, 45),
    # Phase 5: Sport-specific integration (5 min) — KB adds overhead band distraction
    ("__REST__",               "Transition to Phase 5",                         None, None, 10),
    ("Touring Stride",         "Phase 5: alternating deep lunges + arm drive", None, 16, None),
    ("Overhead Band Distraction", "Phase 5: small circles, opens subacromial", "R", None, 30),
    ("Overhead Band Distraction", "Phase 5: small circles, opens subacromial", "L", None, 30),
    ("__REST__",               "Transition to prone",                           None, None, 10),
    ("Prone I-T-Y",            "Phase 5: 8 reps each shape — scapular endurance", None, 24, None),
]


# Protocol T — Tuesday Mobility routine (25 min)
# Source: openclaw/coaching-program.md §Mobility Routine.
PROTOCOL_T: list[_StepTuple] = [
    ("Foam Roll T-Spine",       "Segmental extension, 75s",          None, None, 75),
    ("Foam Roll Lats",          "Side-lying, 60s/side",              "R", None, 60),
    ("Foam Roll Lats",          "Side-lying, 60s/side",              "L", None, 60),
    ("Foam Roll Hamstrings",    "Quads/glutes/hams, 75s/side",       "R", None, 75),
    ("Foam Roll Hamstrings",    "Quads/glutes/hams, 75s/side",       "L", None, 75),
    ("__REST__",                "Transition to dynamic flow",         None, None, 10),
    ("90/90 Hip Switch",        "10 switches per side",              None, 20, None),
    ("World's Greatest Stretch","5 reps per side",                   "R", 5, None),
    ("World's Greatest Stretch","5 reps per side",                   "L", 5, None),
    ("Cat-Cow",                 "10 cycles, slow",                   None, None, 60),
    ("__REST__",                "Transition to side-lying",           None, None, 10),
    ("Thoracic Rotation",       "8 reps/side, side-lying open book", "R", 8, None),
    ("Thoracic Rotation",       "8 reps/side, side-lying open book", "L", 8, None),
    ("__REST__",                "Transition to standing",             None, None, 10),
    ("Wall Slides",             "Shoulder CARs proxy, 5/side",       "R", 5, None),
    ("Wall Slides",             "Shoulder CARs proxy, 5/side",       "L", 5, None),
    ("__REST__",                "Transition to floor",                None, None, 10),
    ("Pigeon Pose",             "60s/side, deep hip ER",             "R", None, 60),
    ("Pigeon Pose",             "60s/side, deep hip ER",             "L", None, 60),
    ("Couch Stretch",           "60s/side, hip flexor",              "R", None, 60),
    ("Couch Stretch",           "60s/side, hip flexor",              "L", None, 60),
]


PROTOCOL_NAMES = {
    "A": "Protocol A: Daily Mobility (12 min)",
    "B": "Protocol B: Pre-Gym Warm-Up",
    "C": "Protocol C: Dedicated Mobility (45 min)",
    "T": "Tuesday Mobility (25 min)",
}

PROTOCOL_DURATIONS = {"A": 12, "B": 12, "C": 45, "T": 25}


# ---------------------------------------------------------------------------
# KB self-check (audit Phase 5)
# ---------------------------------------------------------------------------
#
# Guards against drift between the protocols implemented here and the
# protocols documented in docs/knowledge-base/domain-9-mobility.md.
#
# Direction of risk: a protocol DOCUMENTED but NOT implemented is dangerous
# (the coach will reference a routine that doesn't exist). A protocol
# IMPLEMENTED but NOT documented is acceptable as a script-side extension
# (Protocol T = "Tuesday Mobility" is one such — it's a project-specific
# variant) but should be visible, not silent.
#
# This is a weaker check than workout_generator's because the mobility KB
# uses prose, not a parseable schema. We can only verify protocol headings,
# not exercise lists. Better than nothing.

_MOBILITY_KB_PATH = PROJECT_ROOT / "docs" / "knowledge-base" / "domain-9-mobility.md"


def _parse_documented_protocols(text: str) -> set[str]:
    """Return the set of protocol letters with `### Protocol X:` headings."""
    import re as _re
    found = set()
    for line in text.splitlines():
        m = _re.match(r"^###\s+Protocol\s+([A-Z]):", line.strip())
        if m:
            found.add(m.group(1))
    return found


def _validate_mobility_kb() -> None:
    if not _MOBILITY_KB_PATH.exists():
        # The KB file is optional during early development; warn but don't
        # block. Generator self-check is the load-bearing one.
        log.warning(
            "mobility self-check: %s not found; skipping KB drift check",
            _MOBILITY_KB_PATH,
        )
        return
    text = _MOBILITY_KB_PATH.read_text(encoding="utf-8")
    documented = _parse_documented_protocols(text)
    implemented = set(PROTOCOL_NAMES.keys())
    missing = documented - implemented
    if missing:
        raise RuntimeError(
            "mobility self-check FAILED — protocols documented in "
            f"{_MOBILITY_KB_PATH.name} but NOT implemented: {sorted(missing)}. "
            f"Documented: {sorted(documented)}; implemented: {sorted(implemented)}. "
            "Either implement the missing protocol or remove it from the KB."
        )
    extras = implemented - documented
    if extras:
        log.warning(
            "mobility self-check: implemented protocols not in KB (script extensions): %s",
            sorted(extras),
        )


_validate_mobility_kb()


# ---------------------------------------------------------------------------
# Step builders
# ---------------------------------------------------------------------------

YOGA_SPORT_TYPE = {
    "sportTypeId": 6,
    "sportTypeKey": "yoga",
    "displayOrder": 6,
}


def build_transition_step(description: str, duration_s: int, step_order: int) -> dict:
    """Build a Garmin rest/transition step — gives time to reposition."""
    return {
        "type": "ExecutableStepDTO",
        "stepOrder": step_order,
        "childStepId": None,
        "description": description,
        "stepType": {
            "stepTypeId": 5,
            "stepTypeKey": "rest",
            "displayOrder": 5,
        },
        "endCondition": {
            "conditionTypeId": 2,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        },
        "endConditionValue": float(duration_s),
    }


def build_step(
    name: str,
    description: str,
    side: str | None,
    reps: int | None,
    duration_s: int | None,
    step_order: int,
) -> dict:
    """Build a single timed or rep-based mobility step (Garmin DTO shape)."""
    mapping = EXERCISE_MAP.get(name, ("WARM_UP", "OTHER"))

    desc_parts = [name]
    if side:
        desc_parts[0] = f"{name} ({side})"
    if description:
        desc_parts.append(description)
    desc = " — ".join(desc_parts)

    step: dict[str, Any] = {
        "type": "ExecutableStepDTO",
        "stepOrder": step_order,
        "stepType": {
            "stepTypeId": 3,
            "stepTypeKey": "interval",
            "displayOrder": 3,
        },
        "category": mapping[0],
        "exerciseName": mapping[1],
        "description": desc,
    }

    if duration_s:
        step["endCondition"] = {
            "conditionTypeId": 2,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        }
        step["endConditionValue"] = float(duration_s)
    elif reps:
        step["endCondition"] = {
            "conditionTypeId": 10,
            "conditionTypeKey": "reps",
            "displayOrder": 10,
            "displayable": True,
        }
        step["endConditionValue"] = float(reps)

    return step


def _select_steps(
    protocol: Literal["A", "B", "C", "T"],
    target: str | None,
) -> list[tuple[str, str, str | None, int | None, int | None]]:
    if protocol == "A":
        return PROTOCOL_A
    if protocol == "C":
        return PROTOCOL_C
    if protocol == "T":
        return PROTOCOL_T
    if protocol == "B":
        if target not in PROTOCOL_B_BY_TARGET:
            raise ValueError(
                f"Protocol B requires target in {sorted(PROTOCOL_B_BY_TARGET)}, got {target!r}"
            )
        return PROTOCOL_B_BY_TARGET[target]
    raise ValueError(f"Unknown protocol {protocol!r}")


def protocol_b_warmup_tuples(target: str) -> list[tuple[str, int | None, int | None]]:
    """Return Protocol B steps as (name, reps, duration_s) tuples.

    Same shape as workout_push.WARMUP_PROTOCOLS so callers can run them
    through workout_push.build_warmup_step (which uses the validated
    GARMIN_EXERCISE_MAP and won't trigger Garmin's "Invalid category" error).
    Side-aware steps are flattened: an L+R pair becomes two entries.
    """
    if target not in PROTOCOL_B_BY_TARGET:
        raise ValueError(f"unknown target {target!r}")
    out: list[tuple[str, int | None, int | None]] = []
    for name, _desc, _side, reps, dur in PROTOCOL_B_BY_TARGET[target]:
        if name == "__REST__":
            continue  # workout_push.py manages its own rest steps
        out.append((name, reps, dur))
    return out


def build_step_list(
    protocol: Literal["A", "B", "C", "T"],
    target: str | None = None,
    start_step_order: int = 1,
) -> list[dict]:
    """Return bare Garmin step DTOs for a protocol.

    `workout_push.py` uses this to prepend Protocol B steps to the existing
    strength warm-up block; pass `start_step_order` so step ordering stays
    monotonic when interleaved.
    """
    raw = _select_steps(protocol, target)
    steps: list[dict] = []
    order = start_step_order
    for name, desc, side, reps, dur in raw:
        if name == "__REST__":
            steps.append(build_transition_step(desc, dur or 10, order))
        else:
            steps.append(build_step(name, desc, side, reps, dur, step_order=order))
        order += 1
    return steps


def build_workout(
    protocol: Literal["A", "B", "C", "T"],
    target: str | None = None,
) -> dict:
    """Build a complete Garmin workout JSON envelope for a mobility protocol."""
    steps = build_step_list(protocol, target=target, start_step_order=1)

    name = PROTOCOL_NAMES[protocol]
    if protocol == "B" and target:
        name = f"Protocol B ({target}-day): Pre-Gym Warm-Up"

    descriptions = {
        "A": (
            "Domain 9 daily maintenance. Targets ankle DF, hip flexors, "
            "thoracic rotation, hip ER. Non-negotiable minimum."
        ),
        "B": "Domain 9 pre-gym warm-up. Dynamic emphasis, no long static holds.",
        "C": (
            "Domain 9 dedicated mobility session. Five phases: foam roll, "
            "dynamic flow, loaded stretching, static holds, sport-specific."
        ),
        "T": (
            "Tuesday mobility (coaching-program.md). Foam roll → 90/90 → WGS → "
            "cat-cow + T-rotation → shoulder CARs → pigeon → couch stretch."
        ),
    }

    return {
        "sportType": YOGA_SPORT_TYPE,
        "workoutName": name,
        "description": descriptions[protocol],
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": YOGA_SPORT_TYPE,
                "workoutSteps": steps,
            }
        ],
    }


# Back-compat alias for any caller still importing the old name.
def build_protocol_a_workout() -> dict:
    return build_workout("A")


# ---------------------------------------------------------------------------
# Public summary helpers (used by health-coach SKILL via --json-out)
# ---------------------------------------------------------------------------


def summarize_steps(protocol: Literal["A", "B", "C", "T"], target: str | None = None) -> list[dict]:
    """Compact, app/Slack-friendly representation of a protocol's steps.

    Each entry: {name, side, reps, duration_s, cue}.
    """
    raw = _select_steps(protocol, target)
    out = []
    for name, _desc, side, reps, dur in raw:
        if name == "__REST__":
            continue  # transitions are Garmin-only; omit from Slack/app summaries
        out.append({
            "name": name,
            "side": side,
            "reps": reps,
            "duration_s": dur,
            "cue": EXERCISE_CUES.get(name),
        })
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _emit(payload: dict, json_out: bool) -> None:
    if json_out:
        sys.stdout.write(json.dumps(payload, default=str) + "\n")
        sys.stdout.flush()
    else:
        print(json.dumps(payload, indent=2, default=str))


def _push_to_garmin(workout: dict) -> tuple[int | None, str | None]:
    try:
        from garmin_auth import get_safe_client  # type: ignore
        client = get_safe_client(require_garminconnect=True)
    except Exception as e:
        return None, f"garmin auth failed: {e}"
    try:
        result = client.upload_workout(workout)
        wid = result.get("workoutId") if isinstance(result, dict) else None
        if not wid:
            return None, "upload returned no workoutId"
        return int(wid), None
    except Exception as e:
        return None, f"upload failed: {e}"


def _schedule_to_garmin(workout_id: int, target_date: date) -> str | None:
    try:
        from garmin_auth import get_safe_client  # type: ignore
        client = get_safe_client(require_garminconnect=True)
        client.schedule_workout(workout_id, target_date.isoformat())
        return None
    except Exception as e:
        return f"schedule failed: {e}"


def _write_planned(
    target_date: date,
    protocol: str,
    workout: dict,
    garmin_workout_id: int | None,
) -> tuple[int | None, str | None]:
    """Upsert a planned_workouts row for this mobility session."""
    try:
        from supabase import create_client  # type: ignore
        sb = create_client(
            os.environ["SUPABASE_URL"],
            os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"],
        )
    except Exception as e:
        return None, f"supabase init failed: {e}"

    # Lazy import to avoid a hard cycle
    try:
        from workout_generator import build_mobility_definition  # type: ignore
        wd = build_mobility_definition(protocol)
    except Exception as e:
        return None, f"build_mobility_definition failed: {e}"

    session_name = f"Mobility (Protocol {protocol})"
    row = {
        "training_block": "unscheduled",
        "week_number": 0,
        "session_name": session_name,
        "session_type": "mobility",
        "scheduled_date": target_date.isoformat(),
        "estimated_duration_minutes": PROTOCOL_DURATIONS[protocol],
        "workout_definition": wd,
        "status": "planned",
    }

    try:
        existing = (
            sb.table("planned_workouts")
            .select("id,status")
            .eq("scheduled_date", target_date.isoformat())
            .eq("session_name", session_name)
            .limit(1)
            .execute()
        )
        if existing.data:
            row_id = existing.data[0]["id"]
            patch = {
                "workout_definition": wd,
                "estimated_duration_minutes": PROTOCOL_DURATIONS[protocol],
                "session_type": "mobility",
            }
            sb.table("planned_workouts").update(patch).eq("id", row_id).execute()
        else:
            res = sb.table("planned_workouts").insert(row).execute()
            row_id = res.data[0]["id"] if res.data else None

        # garmin_workout_id linking is owned by workout_push.link_garmin_workout_id
        if garmin_workout_id and row_id:
            from workout_push import link_garmin_workout_id
            link_garmin_workout_id(garmin_workout_id, target_date, sb=sb, planned_id=row_id)

        return row_id, None
    except Exception as e:
        return None, f"supabase write failed: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/upload a mobility workout to Garmin")
    parser.add_argument("--protocol", choices=["A", "B", "C", "T"], default="A")
    parser.add_argument("--target", choices=["A", "B", "C"], help="Required for Protocol B")
    parser.add_argument("--date", help="Schedule date (YYYY-MM-DD); required for --push/--write-planned")
    parser.add_argument("--push", action="store_true", help="Upload + schedule to Garmin")
    parser.add_argument("--write-planned", action="store_true",
                        help="Upsert a planned_workouts row for the date")
    parser.add_argument("--json-out", action="store_true",
                        help="Single-line JSON on stdout (logs go to stderr)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Deprecated; default is no push. Kept for back-compat.")
    args = parser.parse_args()

    if args.protocol == "B" and not args.target:
        log.error("Protocol B requires --target {A,B,C}")
        return 2

    target_date: date | None = None
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            log.error("--date must be ISO YYYY-MM-DD")
            return 2

    if (args.push or args.write_planned) and target_date is None:
        log.error("--push and --write-planned require --date")
        return 2

    # Build
    try:
        workout = build_workout(args.protocol, target=args.target)
    except Exception as e:
        log.error("build failed: %s", e)
        _emit({"ok": False, "error": str(e)}, args.json_out)
        return 2

    steps_summary = summarize_steps(args.protocol, target=args.target)

    payload: dict = {
        "ok": True,
        "protocol": args.protocol,
        "target": args.target,
        "workout_name": workout["workoutName"],
        "step_count": len(workout["workoutSegments"][0]["workoutSteps"]),
        "steps": steps_summary,
        "garmin_workout_id": None,
        "planned_id": None,
        "scheduled": False,
        "error": None,
    }

    # Push
    if args.push:
        wid, err = _push_to_garmin(workout)
        payload["garmin_workout_id"] = wid
        if err:
            payload["ok"] = False
            payload["error"] = err
        elif target_date:
            sched_err = _schedule_to_garmin(wid, target_date)
            if sched_err:
                payload["ok"] = False
                payload["error"] = sched_err
            else:
                payload["scheduled"] = True

    # Plan
    if args.write_planned and target_date is not None:
        pid, err = _write_planned(target_date, args.protocol, workout,
                                  payload.get("garmin_workout_id"))
        payload["planned_id"] = pid
        if err:
            payload["ok"] = False
            payload["error"] = (payload["error"] + "; " if payload["error"] else "") + err

    # When not in --json-out mode, also print the full Garmin workout for debugging
    if not args.json_out and not args.push and not args.write_planned:
        log.info("Built %s — %d steps (no push, no plan)",
                 workout["workoutName"], payload["step_count"])
        print(json.dumps(workout, indent=2))
        return 0

    _emit(payload, args.json_out)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
