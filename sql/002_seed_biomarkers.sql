-- =============================================
-- SEED: Biomarker Definitions
-- Comprehensive panel with optimal + reference ranges
-- =============================================

INSERT INTO biomarker_definitions (name, display_name, category, standard_unit, optimal_low, optimal_high, reference_low, reference_high, description, higher_is) VALUES

-- LIPID PANEL
('total_cholesterol', 'Total Cholesterol', 'lipids', 'mg/dL', 125, 200, 100, 240, 'Total blood cholesterol level', 'mixed'),
('ldl_cholesterol', 'LDL Cholesterol', 'lipids', 'mg/dL', NULL, 100, NULL, 130, 'Low-density lipoprotein — primary target for cardiovascular risk', 'worse'),
('hdl_cholesterol', 'HDL Cholesterol', 'lipids', 'mg/dL', 50, 90, 40, NULL, 'High-density lipoprotein — protective against cardiovascular disease', 'better'),
('triglycerides', 'Triglycerides', 'lipids', 'mg/dL', NULL, 100, NULL, 150, 'Blood fat level, affected by diet and exercise', 'worse'),
('vldl_cholesterol', 'VLDL Cholesterol', 'lipids', 'mg/dL', NULL, 20, 5, 40, 'Very low-density lipoprotein', 'worse'),
('total_hdl_ratio', 'Total/HDL Ratio', 'lipids', 'ratio', NULL, 3.5, NULL, 5.0, 'Ratio of total cholesterol to HDL', 'worse'),
('ldl_hdl_ratio', 'LDL/HDL Ratio', 'lipids', 'ratio', NULL, 2.0, NULL, 3.5, 'Ratio of LDL to HDL cholesterol', 'worse'),
('apolipoprotein_b', 'Apolipoprotein B', 'lipids', 'mg/dL', NULL, 90, 50, 130, 'Primary protein in LDL particles — better CVD risk marker than LDL-C', 'worse'),
('lp_a', 'Lipoprotein(a)', 'lipids', 'nmol/L', NULL, 75, NULL, 125, 'Genetic cardiovascular risk factor', 'worse'),

-- HORMONES
('testosterone_total', 'Total Testosterone', 'hormones', 'ng/dL', 500, 900, 264, 916, 'Primary male sex hormone — affects muscle, energy, mood', 'better'),
('testosterone_free', 'Free Testosterone', 'hormones', 'pg/mL', 10, 25, 5, 30, 'Unbound bioavailable testosterone', 'better'),
('shbg', 'SHBG', 'hormones', 'nmol/L', 20, 50, 10, 70, 'Sex hormone-binding globulin — binds testosterone', 'mixed'),
('estradiol', 'Estradiol (E2)', 'hormones', 'pg/mL', 20, 40, 10, 50, 'Primary estrogen — important for bone and joint health in men', 'mixed'),
('dhea_s', 'DHEA-S', 'hormones', 'mcg/dL', 200, 500, 100, 620, 'Adrenal hormone precursor to testosterone', 'better'),
('cortisol', 'Cortisol (AM)', 'hormones', 'mcg/dL', 8, 15, 5, 25, 'Stress hormone — morning level', 'mixed'),
('igf_1', 'IGF-1', 'hormones', 'ng/mL', 150, 300, 100, 400, 'Insulin-like growth factor — growth and recovery marker', 'better'),
('tsh', 'TSH', 'thyroid', 'mIU/L', 0.5, 2.5, 0.4, 4.0, 'Thyroid-stimulating hormone', 'mixed'),
('free_t4', 'Free T4', 'thyroid', 'ng/dL', 1.0, 1.5, 0.8, 1.8, 'Free thyroxine — active thyroid hormone', 'mixed'),
('free_t3', 'Free T3', 'thyroid', 'pg/mL', 3.0, 4.0, 2.3, 4.2, 'Free triiodothyronine — most active thyroid hormone', 'mixed'),
('insulin_fasting', 'Fasting Insulin', 'metabolic', 'uIU/mL', 2, 6, 2, 20, 'Fasting insulin level — marker of insulin sensitivity', 'worse'),

-- VITAMINS & MINERALS
('vitamin_d', 'Vitamin D (25-OH)', 'vitamins', 'ng/mL', 40, 60, 30, 100, '25-hydroxyvitamin D — bone health, immune function, mood', 'better'),
('vitamin_b12', 'Vitamin B12', 'vitamins', 'pg/mL', 500, 1000, 200, 1100, 'Cobalamin — nerve function, energy, red blood cells', 'better'),
('folate', 'Folate', 'vitamins', 'ng/mL', 10, 25, 3, 30, 'Vitamin B9 — DNA synthesis, cell division', 'better'),
('ferritin', 'Ferritin', 'vitamins', 'ng/mL', 50, 150, 20, 300, 'Iron storage protein — energy, oxygen transport', 'mixed'),
('iron', 'Iron (Serum)', 'vitamins', 'mcg/dL', 80, 150, 60, 170, 'Serum iron level', 'mixed'),
('tibc', 'TIBC', 'vitamins', 'mcg/dL', 250, 350, 250, 400, 'Total iron-binding capacity', 'mixed'),
('transferrin_saturation', 'Transferrin Saturation', 'vitamins', '%', 25, 45, 20, 50, 'Percentage of transferrin bound to iron', 'mixed'),
('magnesium', 'Magnesium (RBC)', 'vitamins', 'mg/dL', 5.0, 6.5, 4.0, 6.8, 'Red blood cell magnesium — better than serum for deficiency', 'better'),
('zinc', 'Zinc (Serum)', 'vitamins', 'mcg/dL', 80, 120, 60, 130, 'Essential mineral — immune function, testosterone, recovery', 'better'),

-- INFLAMMATION
('hs_crp', 'hs-CRP', 'inflammation', 'mg/L', NULL, 1.0, NULL, 3.0, 'High-sensitivity C-reactive protein — systemic inflammation marker', 'worse'),
('esr', 'ESR', 'inflammation', 'mm/hr', NULL, 10, 0, 20, 'Erythrocyte sedimentation rate — general inflammation marker', 'worse'),
('homocysteine', 'Homocysteine', 'inflammation', 'umol/L', NULL, 8, NULL, 15, 'Amino acid linked to cardiovascular risk when elevated', 'worse'),
('uric_acid', 'Uric Acid', 'inflammation', 'mg/dL', 3.0, 6.0, 2.5, 7.0, 'Waste product — elevated levels linked to gout and cardiovascular risk', 'worse'),

-- COMPLETE BLOOD COUNT (CBC)
('wbc', 'White Blood Cells', 'cbc', 'K/uL', 4.5, 7.5, 3.5, 10.5, 'Total white blood cell count — immune function', 'mixed'),
('rbc', 'Red Blood Cells', 'cbc', 'M/uL', 4.5, 5.5, 4.0, 6.0, 'Total red blood cell count — oxygen transport', 'mixed'),
('hemoglobin', 'Hemoglobin', 'cbc', 'g/dL', 14.5, 16.5, 13.0, 17.5, 'Oxygen-carrying protein in red blood cells', 'mixed'),
('hematocrit', 'Hematocrit', 'cbc', '%', 42, 48, 38, 52, 'Percentage of blood volume occupied by red blood cells', 'mixed'),
('mcv', 'MCV', 'cbc', 'fL', 82, 95, 80, 100, 'Mean corpuscular volume — average red blood cell size', 'mixed'),
('mch', 'MCH', 'cbc', 'pg', 27, 33, 26, 34, 'Mean corpuscular hemoglobin — avg hemoglobin per RBC', 'mixed'),
('mchc', 'MCHC', 'cbc', 'g/dL', 32, 36, 31, 37, 'Mean corpuscular hemoglobin concentration', 'mixed'),
('platelets', 'Platelets', 'cbc', 'K/uL', 200, 350, 150, 400, 'Blood clotting cells', 'mixed'),
('neutrophils', 'Neutrophils', 'cbc', '%', 40, 60, 40, 70, 'Most common white blood cell — bacterial infection response', 'mixed'),
('lymphocytes', 'Lymphocytes', 'cbc', '%', 25, 40, 20, 45, 'Immune cells — viral infection response', 'mixed'),

-- METABOLIC PANEL
('glucose_fasting', 'Fasting Glucose', 'metabolic', 'mg/dL', 72, 90, 65, 100, 'Fasting blood sugar level', 'worse'),
('hba1c', 'HbA1c', 'metabolic', '%', 4.5, 5.3, 4.0, 5.7, 'Glycated hemoglobin — 3-month average blood sugar', 'worse'),
('bun', 'BUN', 'metabolic', 'mg/dL', 10, 20, 7, 25, 'Blood urea nitrogen — kidney function and protein metabolism', 'mixed'),
('creatinine', 'Creatinine', 'metabolic', 'mg/dL', 0.8, 1.2, 0.6, 1.3, 'Kidney function marker — can be higher in muscular individuals', 'mixed'),
('egfr', 'eGFR', 'metabolic', 'mL/min', 90, NULL, 60, NULL, 'Estimated glomerular filtration rate — kidney function', 'better'),
('alt', 'ALT', 'metabolic', 'U/L', NULL, 25, 7, 45, 'Alanine aminotransferase — liver function marker', 'worse'),
('ast', 'AST', 'metabolic', 'U/L', NULL, 25, 10, 40, 'Aspartate aminotransferase — liver/muscle damage marker', 'worse'),
('ggt', 'GGT', 'metabolic', 'U/L', NULL, 25, 5, 55, 'Gamma-glutamyl transferase — liver and bile duct marker', 'worse'),
('alkaline_phosphatase', 'Alkaline Phosphatase', 'metabolic', 'U/L', 40, 80, 30, 120, 'Bone and liver enzyme', 'mixed'),
('albumin', 'Albumin', 'metabolic', 'g/dL', 4.2, 5.0, 3.5, 5.5, 'Liver-produced protein — nutritional status marker', 'better'),
('total_protein', 'Total Protein', 'metabolic', 'g/dL', 6.5, 7.5, 6.0, 8.3, 'Total serum protein', 'mixed'),
('sodium', 'Sodium', 'metabolic', 'mEq/L', 138, 142, 136, 145, 'Electrolyte — fluid balance', 'mixed'),
('potassium', 'Potassium', 'metabolic', 'mEq/L', 4.0, 4.8, 3.5, 5.0, 'Electrolyte — muscle and nerve function', 'mixed'),
('calcium', 'Calcium', 'metabolic', 'mg/dL', 9.2, 10.0, 8.5, 10.5, 'Bone health, muscle function', 'mixed'),
('phosphorus', 'Phosphorus', 'metabolic', 'mg/dL', 3.0, 4.0, 2.5, 4.5, 'Bone health, energy metabolism', 'mixed'),
('ck', 'Creatine Kinase', 'metabolic', 'U/L', NULL, 200, 30, 300, 'Muscle damage marker — elevated after intense training is normal', 'mixed'),
('ldh', 'LDH', 'metabolic', 'U/L', NULL, 200, 100, 250, 'Lactate dehydrogenase — tissue damage marker', 'worse')

ON CONFLICT (name) DO NOTHING;
