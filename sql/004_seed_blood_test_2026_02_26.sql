-- =============================================
-- SEED: Blood Test Panel — 26.02.2026
-- Lab: Dr. Peter Hörtnagl, Innsbruck
-- Patient: Oliwer Owczarek
-- =============================================

-- Insert the panel
INSERT INTO blood_test_panels (date, lab_name, fasting, notes, pdf_url)
VALUES ('2026-02-26', 'Dr. Peter Hörtnagl, Allgemeinmedizin, Innsbruck', NULL, 'Großes Blutbild. Report date: 2026-03-03. Two flagged values: phosphor (mildly elevated), creatinine (mildly elevated, likely athletic context).', NULL);

-- Insert all results referencing the panel
WITH panel AS (SELECT id FROM blood_test_panels WHERE date = '2026-02-26' LIMIT 1)
INSERT INTO blood_test_results (panel_id, biomarker, value, unit, reference_low, reference_high, optimal_low, optimal_high, flag, category, notes) VALUES

-- CBC
((SELECT id FROM panel), 'basophils_pct', 0.5, '%', 0.0, 2.0, NULL, NULL, 'normal', 'cbc', 'Basophile Granulozyten'),
((SELECT id FROM panel), 'eosinophils_pct', 0.8, '%', 0.0, 7.0, NULL, NULL, 'normal', 'cbc', 'Eosinophile Granulozyten'),
((SELECT id FROM panel), 'rbc', 5.69, 'T/l', 4.4, 5.9, 4.5, 5.5, 'normal', 'cbc', 'Erythrozyten'),
((SELECT id FROM panel), 'hemoglobin', 16.3, 'g/dL', 12, 18, 14.5, 16.5, 'normal', 'cbc', 'Hämoglobin'),
((SELECT id FROM panel), 'hematocrit', 51.1, '%', 40, 54, 42, 48, 'normal', 'cbc', 'Hämatokrit'),
((SELECT id FROM panel), 'lymphocytes', 28.7, '%', 15, 40, 25, 40, 'normal', 'cbc', 'Lymphozyten'),
((SELECT id FROM panel), 'mch', 28.0, 'pg', 27, 32, 27, 33, 'normal', 'cbc', 'MCH'),
((SELECT id FROM panel), 'mchc', 32, '%', 30, 36, 32, 36, 'normal', 'cbc', 'MCHC'),
((SELECT id FROM panel), 'mcv', 85.3, 'fL', 77, 96, 82, 95, 'normal', 'cbc', 'MCV'),
((SELECT id FROM panel), 'monocytes_pct', 7.5, '%', 2, 10, NULL, NULL, 'normal', 'cbc', 'Monozyten'),
((SELECT id FROM panel), 'neutrophils_segmented', 60.9, '%', 42, 75, 40, 60, 'normal', 'cbc', 'Segmentkernige Granulozyten'),
((SELECT id FROM panel), 'neutrophils_band', 1.6, '%', 0.0, 4.0, NULL, NULL, 'normal', 'cbc', 'Stabkernige Granulozyten'),
((SELECT id FROM panel), 'wbc', 5.8, 'G/l', 4, 10, 4.5, 7.5, 'normal', 'cbc', 'Leukozyten'),
((SELECT id FROM panel), 'platelets', 189, 'G/l', 140, 400, 200, 350, 'normal', 'cbc', 'Thrombozyten'),
((SELECT id FROM panel), 'esr', 3, 'mm/hr', 0, 10, NULL, 10, 'normal', 'cbc', 'Blutsenkung nach 1h'),
((SELECT id FROM panel), 'mpv', 9.4, 'fL', 5.9, 12, NULL, NULL, 'normal', 'cbc', 'Mean Platelet Volume'),

-- Absolute differential
((SELECT id FROM panel), 'ckmb_pct', 8.4, '%', NULL, NULL, NULL, NULL, NULL, 'cbc', 'CKMB%'),
((SELECT id FROM panel), 'neutrophils_band_abs', 93, '/uL', NULL, NULL, NULL, NULL, NULL, 'cbc', 'STABA absolute'),
((SELECT id FROM panel), 'neutrophils_seg_abs', 3532, '/uL', 1600, 7000, NULL, NULL, 'normal', 'cbc', 'SEGA absolute'),
((SELECT id FROM panel), 'lymphocytes_abs', 1665, '/uL', 1000, 5500, NULL, NULL, 'normal', 'cbc', 'LYMPHOA absolute'),
((SELECT id FROM panel), 'monocytes_abs', 435, '/uL', 0, 800, NULL, NULL, 'normal', 'cbc', 'MONOA absolute'),
((SELECT id FROM panel), 'eosinophils_abs', 46, '/uL', 0, 450, NULL, NULL, 'normal', 'cbc', 'EOA absolute'),
((SELECT id FROM panel), 'basophils_abs', 29, '/uL', 0, 200, NULL, NULL, 'normal', 'cbc', 'BASOA absolute'),

-- Lipids
((SELECT id FROM panel), 'total_cholesterol', 170, 'mg/dL', NULL, 200, 125, 200, 'normal', 'lipids', 'Cholesterin total'),
((SELECT id FROM panel), 'hdl_cholesterol', 51, 'mg/dL', 40, 68, 50, 90, 'normal', 'lipids', 'HDL-Cholesterin'),
((SELECT id FROM panel), 'ldl_cholesterol', 104, 'mg/dL', NULL, 116, NULL, 100, 'normal', 'lipids', 'LDL-Cholesterin'),
((SELECT id FROM panel), 'triglycerides', 83, 'mg/dL', NULL, 150, NULL, 100, 'normal', 'lipids', 'Triglyceride'),
((SELECT id FROM panel), 'total_hdl_ratio', 3.3, 'ratio', NULL, 3.5, NULL, 3.5, 'normal', 'lipids', 'Cholesterin Ratio'),

-- Electrolytes
((SELECT id FROM panel), 'chloride', 96, 'mmol/L', 95, 110, NULL, NULL, 'normal', 'metabolic', 'Chlorid'),
((SELECT id FROM panel), 'potassium', 5.40, 'mmol/L', 3.5, 5.4, 4.0, 4.8, 'normal', 'metabolic', 'Kalium — at upper edge of reference'),
((SELECT id FROM panel), 'magnesium_serum', 0.96, 'mmol/L', 0.6, 1.0, NULL, NULL, 'normal', 'vitamins', 'Magnesium (serum)'),
((SELECT id FROM panel), 'sodium', 142, 'mmol/L', 136, 145, 138, 142, 'normal', 'metabolic', 'Natrium'),
((SELECT id FROM panel), 'phosphorus', 1.73, 'mmol/L', 0.74, 1.52, NULL, NULL, 'high', 'metabolic', 'Phosphor — mildly elevated. Likely diet/exercise related.'),

-- Blood sugar
((SELECT id FROM panel), 'glucose_fasting', 60, 'mg/dL', 60, 100, 72, 90, 'normal', 'metabolic', 'Blutzucker — at lower edge of reference'),

-- Liver
((SELECT id FROM panel), 'ggt', 14, 'U/L', 12, 64, NULL, 25, 'normal', 'metabolic', 'γ-GT'),
((SELECT id FROM panel), 'ast', 24, 'U/L', 5, 34, NULL, 25, 'normal', 'metabolic', 'GOT (ASAT)'),
((SELECT id FROM panel), 'alt', 44, 'U/L', 0, 55, NULL, 25, 'normal', 'metabolic', 'GPT (ALAT) — within reference but above optimal, common in athletes'),
((SELECT id FROM panel), 'uric_acid', 6.5, 'mg/dL', 3, 7.2, 3.0, 6.0, 'normal', 'inflammation', 'Harnsäure'),
((SELECT id FROM panel), 'bun', 36, 'mg/dL', 18, 50, 10, 20, 'normal', 'metabolic', 'Harnstoff — within reference, above optimal. High protein diet likely.'),

-- Thyroid
((SELECT id FROM panel), 'free_t3', 4.82, 'pmol/L', 2.5, 6.7, 3.0, 4.0, 'normal', 'thyroid', 'FT3 — note: pmol/L, need to convert for comparison with pg/mL definitions'),
((SELECT id FROM panel), 'tsh', 0.74, 'mU/L', 0.35, 3.5, 0.5, 2.5, 'normal', 'thyroid', 'TSH-Sensitiv'),
((SELECT id FROM panel), 'free_t4', 19.5, 'pmol/L', 10.3, 21.9, NULL, NULL, 'normal', 'thyroid', 'Freies T4 — note: pmol/L'),

-- Other
((SELECT id FROM panel), 'cholinesterase', 5.9, 'kU/L', 4.4, 12.9, NULL, NULL, 'normal', 'metabolic', 'Cholinesterase'),
((SELECT id FROM panel), 'ck', 237.2, 'U/L', 57, 395, NULL, 200, 'normal', 'metabolic', 'CPK — above optimal, normal for active athlete'),
((SELECT id FROM panel), 'hs_crp', 0.06, 'mg/dL', 0.00, 0.50, NULL, 0.10, 'normal', 'inflammation', 'C-Reaktives Protein — excellent, very low inflammation'),
((SELECT id FROM panel), 'iron', 152, 'ug/dL', 65, 175, 80, 150, 'normal', 'vitamins', 'Eisen'),
((SELECT id FROM panel), 'ferritin', 132.3, 'ng/mL', 15, 400, 50, 150, 'normal', 'vitamins', 'Ferritin — good level'),
((SELECT id FROM panel), 'ldh', 187, 'U/L', 125, 243, NULL, 200, 'normal', 'metabolic', 'LDH'),
((SELECT id FROM panel), 'ck_mb', 20, 'U/L', 0, 24, NULL, NULL, 'normal', 'metabolic', 'CK-MB'),
((SELECT id FROM panel), 'creatinine', 1.43, 'mg/dL', 0.5, 1.3, 0.8, 1.2, 'high', 'metabolic', 'Kreatinin — mildly elevated, common in muscular athletes + creatine supplementation');
