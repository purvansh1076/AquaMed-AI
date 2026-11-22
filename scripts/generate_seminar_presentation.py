"""
AquaMedi AI — Technical Seminar Presentation Generator
Generates a 25-slide academic slide deck with widescreen 16:9 layout,
professional government styling, scientific formulas, and embedded screenshots.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    NAVY = RGBColor(18, 49, 91)      # #12315B
    GREEN = RGBColor(23, 107, 69)    # #176B45
    DARK = RGBColor(33, 37, 41)      # #212529
    GRAY = RGBColor(108, 117, 125)   # #6C757D
    LIGHT_BG = RGBColor(245, 247, 250)
    WHITE = RGBColor(255, 255, 255)
    BORDER_COLOR = RGBColor(200, 210, 225)

    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs"))
    screenshots_dir = os.path.join(docs_dir, "screenshots")
    output_path = os.path.join(docs_dir, "AQUAMEDI_AI_TECHNICAL_SEMINAR.pptx")

    blank_layout = prs.slide_layouts[6]

    def add_header(slide, title_text, category_text="AQUAMEDI AI — ACADEMIC TECHNICAL SEMINAR"):
        # Top banner background
        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.1))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = NAVY
        top_bar.line.color.rgb = NAVY

        # Green accent line
        accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.1), Inches(13.333), Inches(0.08))
        accent.fill.solid()
        accent.fill.fore_color.rgb = GREEN
        accent.line.color.rgb = GREEN

        # Category text
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.12), Inches(11.7), Inches(0.3))
        cat_tf = cat_box.text_frame
        cat_tf.word_wrap = True
        cat_p = cat_tf.paragraphs[0]
        cat_p.text = category_text.upper()
        cat_p.font.size = Pt(11)
        cat_p.font.bold = True
        cat_p.font.color.rgb = RGBColor(212, 175, 55) # Gold accent

        # Title text
        t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.38), Inches(11.7), Inches(0.65))
        t_tf = t_box.text_frame
        t_tf.word_wrap = True
        t_p = t_tf.paragraphs[0]
        t_p.text = title_text
        t_p.font.size = Pt(22)
        t_p.font.bold = True
        t_p.font.color.rgb = WHITE

        # Footer
        footer_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.1), Inches(13.333), Inches(0.4))
        footer_bar.fill.solid()
        footer_bar.fill.fore_color.rgb = RGBColor(240, 243, 246)
        footer_bar.line.color.rgb = BORDER_COLOR

        foot_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.12), Inches(11.7), Inches(0.3))
        foot_tf = foot_box.text_frame
        foot_p = foot_tf.paragraphs[0]
        foot_p.text = "AquaMedi AI: Agricultural Intelligence & Water Resource Allocation | Academic Demonstration Release v1.0"
        foot_p.font.size = Pt(10)
        foot_p.font.color.rgb = GRAY

    # ----------------------------------------------------
    # SLIDE 1: Title Slide
    # ----------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY
    bg1.line.color.rgb = NAVY

    t_box1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11.333), Inches(2.2))
    tf1 = t_box1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "AQUAMEDI AI"
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

    p1_sub = tf1.add_paragraph()
    p1_sub.text = "Precision Agricultural Intelligence & Equitable Canal Water Distribution Platform"
    p1_sub.font.size = Pt(22)
    p1_sub.font.color.rgb = RGBColor(212, 175, 55)

    p1_desc = tf1.add_paragraph()
    p1_desc.text = "Integrating FAO-56 Agronomic Physics, Conformal XGBoost Modeling, OR-Tools Linear Optimization, and Multi-Agent Dispute Mediation"
    p1_desc.font.size = Pt(14)
    p1_desc.font.color.rgb = RGBColor(220, 230, 245)

    # Info card
    card1 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(4.3), Inches(11.333), Inches(2.2))
    card1.fill.solid()
    card1.fill.fore_color.rgb = RGBColor(26, 62, 110)
    card1.line.color.rgb = GREEN

    c_tf1 = card1.text_frame
    c_tf1.word_wrap = True
    cp1 = c_tf1.paragraphs[0]
    cp1.text = "ACADEMIC TECHNICAL SEMINAR PRESENTATION & SYSTEM DEFENSE"
    cp1.font.bold = True
    cp1.font.size = Pt(16)
    cp1.font.color.rgb = WHITE

    cp2 = c_tf1.add_paragraph()
    cp2.text = "• Domain: Agricultural Machine Learning, Water Resource Operations Research & Game Theory\n• Verified Architecture: FastAPI Backend | React 19 Frontend | XGBoost 2.x | Google OR-Tools GLOP\n• Release Status: Academic Demonstration Release v1.0 (840 Pytest + 82 Vitest Verified)"
    cp2.font.size = Pt(13)
    cp2.font.color.rgb = RGBColor(230, 240, 255)

    # ----------------------------------------------------
    # Helper to add standard two-column content
    # ----------------------------------------------------
    def add_two_column_slide(title, cat, left_bullets, right_image=None, right_bullets=None):
        slide = prs.slides.add_slide(blank_layout)
        add_header(slide, title, cat)

        # Left Column box
        w_left = Inches(6.0) if (right_image or right_bullets) else Inches(11.7)
        left_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.4), w_left, Inches(5.4))
        left_box.fill.solid()
        left_box.fill.fore_color.rgb = LIGHT_BG
        left_box.line.color.rgb = BORDER_COLOR

        tf = left_box.text_frame
        tf.word_wrap = True
        for i, b in enumerate(left_bullets):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = b[0]
            p.font.bold = b[1]
            p.font.size = Pt(b[2])
            p.font.color.rgb = DARK if not b[1] else NAVY
            if len(b) > 3 and b[3]:
                p.space_after = Pt(b[3])

        if right_image and os.path.exists(right_image):
            slide.shapes.add_picture(right_image, Inches(7.1), Inches(1.4), width=Inches(5.4))
        elif right_bullets:
            right_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.1), Inches(1.4), Inches(5.4), Inches(5.4))
            right_box.fill.solid()
            right_box.fill.fore_color.rgb = LIGHT_BG
            right_box.line.color.rgb = BORDER_COLOR
            rtf = right_box.text_frame
            rtf.word_wrap = True
            for i, b in enumerate(right_bullets):
                p = rtf.paragraphs[0] if i == 0 else rtf.add_paragraph()
                p.text = b[0]
                p.font.bold = b[1]
                p.font.size = Pt(b[2])
                p.font.color.rgb = DARK if not b[1] else GREEN
                if len(b) > 3 and b[3]:
                    p.space_after = Pt(b[3])
        return slide

    # ----------------------------------------------------
    # SLIDE 2: Problem Statement & Agricultural Water Crisis
    # ----------------------------------------------------
    add_two_column_slide(
        "Motivation & The Agricultural Water Crisis in India",
        "Context & Domain Imperatives",
        [
            ("The Structural Challenge of Canal Irrigation in Semi-Arid India", True, 16, 8),
            ("• Agricultural Water Consumption: Agriculture accounts for >80% of India's freshwater withdrawals, primarily distributed through gravity-fed surface canals.", False, 13, 6),
            ("• The Head-vs-Tail Reach Inequity: Upstream head-reach farmers frequently over-irrigate water-intensive cash crops (e.g. Sugarcane), depriving tail-end farmers of basic crop-survival allocations.", False, 13, 6),
            ("• Information Asymmetry & Dispute Escalation: Farmers lack scientific crop water demand projections, leading to speculative demand spikes, illegal canal breaching, and contentious water disputes.", False, 13, 6),
            ("• Rigid Traditional Warabandi Schemes: Fixed rotational schedules fail to account for dynamic evapotranspiration, changing weather conditions, and localized soil moisture deficits.", False, 13, 8),
            ("Core Research Goal of AquaMedi AI", True, 15, 6),
            ("To build an integrated, scientifically-grounded intelligence platform bridging physical agronomy, conformal machine learning, mathematical operations research, and automated mediation.", False, 13, 0)
        ],
        right_image=os.path.join(screenshots_dir, "06_water_distribution_dashboard_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 3: Research Objectives & Scope
    # ----------------------------------------------------
    add_two_column_slide(
        "Research Objectives & Methodological Scope",
        "Problem Formulation",
        [
            ("Four Primary Methodological Pillars", True, 16, 10),
            ("1. Scientific Precision Crop Water Modeling:", True, 14, 4),
            ("   Predict parcel-level net crop water evapotranspiration using gradient-boosted decision trees (XGBoost) benchmarked against classical FAO-56 Penman-Monteith physics.", False, 13, 8),
            ("2. Distribution-Free Uncertainty Quantification:", True, 14, 4),
            ("   Provide rigorous finite-sample confidence intervals via inductive split conformal prediction to protect farmers against under-allocation risks.", False, 13, 8),
            ("3. Equitable Water Resource Optimization:", True, 14, 4),
            ("   Formulate and solve a constrained multi-objective Linear Programming problem (Google OR-Tools GLOP) that enforces tail-end fairness, minimum subsistence, and canal capacity.", False, 13, 8),
            ("4. Automated Multi-Agent Dispute Mediation:", True, 14, 4),
            ("   Model conflicting stakeholders (Farmer Advocate vs. Canal Officer) via game-theoretic negotiation protocols to discover Pareto-optimal delivery schedules.", False, 13, 0)
        ],
        right_bullets=[
            ("Academic & Engineering Scope", True, 16, 10),
            ("• Benchmark Environment: Calibrated to semi-arid Godavari river basin agronomic distributions (Maharashtra, India).", False, 13, 6),
            ("• Crop Spectrum: Sugarcane, Cotton, Wheat, Soybean, Gram across four standardized phenological growth stages.", False, 13, 6),
            ("• Open Science & Transparency: Explicit distinction between synthetic formula-based benchmarking and physical field telemetry.", False, 13, 6),
            ("• Non-Destructive Integrity: Model artifacts verified and maintained without ad-hoc parameter tampering or retraining.", False, 13, 6),
            ("• Government Digital Accessibility: Dual-role portal with unauthenticated public farmer access and hardened expert controls.", False, 13, 0)
        ]
    )

    # ----------------------------------------------------
    # SLIDE 4: End-to-End System Architecture
    # ----------------------------------------------------
    add_two_column_slide(
        "System Architecture: High-Level End-to-End Topology",
        "System Engineering",
        [
            ("Layered Modular Architecture", True, 16, 8),
            ("• Presentation Tier (React 19 & Vite):", True, 14, 4),
            ("  Accessible, government-style portal (NIC/Gov.in guidelines) with dark navy/green palette, responsive tables, Recharts visualizations, and Lucide icons.", False, 13, 6),
            ("• Application Core (FastAPI & Python 3.12):", True, 14, 4),
            ("  High-performance asynchronous REST API with Pydantic validation, JWT authentication, and dependency-injected services.", False, 13, 6),
            ("• Intelligence & Optimization Subsystems:", True, 14, 4),
            ("  - XGBoost 2.x Regressor with runtime parameter calibration\n  - Inductive Conformal Predictor with empirical quantile scaling\n  - Google OR-Tools GLOP Linear Solver for canal quota optimization\n  - Multi-Agent Dispute Negotiator with concession scoring", False, 13, 6),
            ("• Persistence & Storage Layer:", True, 14, 4),
            ("  SQLAlchemy ORM with SQLite for rapid academic demo and PostgreSQL/Alembic support for production staging.", False, 13, 0)
        ],
        right_image=os.path.join(screenshots_dir, "01_welcome_page_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 5: Agronomic Foundation: FAO-56 Penman-Monteith
    # ----------------------------------------------------
    add_two_column_slide(
        "Theoretical Foundation: FAO-56 Penman-Monteith Physics",
        "Agronomic Engineering",
        [
            ("Standard Reference Evapotranspiration (ET0)", True, 16, 6),
            ("The FAO-56 Penman-Monteith equation models reference grass water demand:", False, 13, 4),
            ("   ET₀ = [0.408Δ(Rₙ - G) + γ(900/(T + 273))u₂(eₛ - eₐ)] / [Δ + γ(1 + 0.34u₂)]", True, 12, 8),
            ("Crop Water Requirement (ETc) & Soil Water Balance", True, 15, 6),
            ("• Crop Coefficient Adjustment: ETc = Kc × ET₀, where Kc accounts for crop type and growth stage (Initial, Dev, Mid, Late).", False, 13, 6),
            ("• Soil Moisture Depletion Factor (Ks): Models water stress when soil moisture drops below readily available water (RAW).", False, 13, 6),
            ("• Net Irrigation Requirement (NIR):", True, 14, 4),
            ("   NIR_depth = max(0, (Ks × ETc) - Peff)   [mm/day]", True, 12, 4),
            ("   NIR_vol = NIR_depth × Area × 10         [m³/day]", True, 12, 6),
            ("• Gross Irrigation Requirement (GIR) at Canal Outlet:", True, 14, 4),
            ("   GIR_vol = NIR_vol / η_appl   (where η_appl = 0.70 for surface irrigation)", True, 12, 0)
        ],
        right_image=os.path.join(screenshots_dir, "11_irrigation_advisory_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 6: Machine Learning Formulation & Target Definition
    # ----------------------------------------------------
    add_two_column_slide(
        "Machine Learning Formulation & Prediction Objectives",
        "Predictive Modeling",
        [
            ("Why Machine Learning for Crop Water Demand?", True, 16, 8),
            ("• Non-Linear Microclimate Interactions: Traditional tables assume static regional constants. Field soil moisture, relative humidity, and temperature exhibit complex non-linear dynamics.", False, 13, 6),
            ("• Instantaneous Inference: Machine learning models provide sub-millisecond edge predictions for dynamic irrigation scheduling.", False, 13, 8),
            ("Exact Scientific Target Definition", True, 16, 6),
            ("• Supervised Regression Formulation: Given feature vector x ∈ ℝ¹⁰, predict net daily water requirement y ∈ ℝ⁺.", False, 13, 6),
            ("• Physical Target Quantity: Net Crop Evapotranspiration Volume (NIR_vol in m³/day, η = 1.0) with 10% gaussian stochastic field noise:", False, 13, 4),
            ("   y = NIR_vol × (1 + ε),   ε ~ 𝒩(0, 0.10²)", True, 13, 8),
            ("• Critical Target Boundary: The model predicts plant net root-zone requirement, whereas canal gates deliver gross conveyance volume.", False, 13, 0)
        ],
        right_image=os.path.join(screenshots_dir, "09_ml_predictions_xgboost_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 7: XGBoost Architecture & Feature Pipeline
    # ----------------------------------------------------
    add_two_column_slide(
        "XGBoost Architecture & Feature Engineering Pipeline",
        "Machine Learning Architecture",
        [
            ("Feature Space & Standardized Input Vector", True, 16, 8),
            ("Ordered 10-dimensional input vector x ∈ ℝ¹⁰:", False, 13, 6),
            ("1. crop_encoded (0: Sugarcane, 1: Cotton, 2: Wheat, 3: Soybean, 4: Gram)\n2. growth_stage_encoded (0: Initial, 1: Crop Dev, 2: Mid-Season, 3: Late)\n3. soil_encoded (0: Black Cotton, 1: Loamy, 2: Sandy Loam)\n4. temperature_c (Ambient daily mean air temp in °C)\n5. humidity_pct (Relative atmospheric humidity %)\n6. rainfall_mm (Recorded 24-hr precipitation in mm)\n7. soil_moisture_pct (Volumetric root-zone moisture %)\n8. et0_mm (Penman-Monteith reference ET₀ in mm/day)\n9. crop_coefficient (Stage-specific Kc factor [0.40 - 1.25])\n10. area_hectares (Farm parcel area in ha)", False, 12, 8),
            ("Hyperparameter Configuration", True, 15, 6),
            ("• Algorithm: Gradient Boosted Trees (XGBRegressor)\n• Trees: n_estimators = 100, max_depth = 5, learning_rate = 0.10\n• Regularization: L1 reg_alpha = 0.1, L2 reg_lambda = 1.0, subsample = 0.8", False, 12, 0)
        ],
        right_image=os.path.join(screenshots_dir, "16_explainability_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 8: Dataset Provenance & Leakage Audit
    # ----------------------------------------------------
    add_two_column_slide(
        "Dataset Provenance, Partitioning & Leakage Elimination",
        "Data Engineering",
        [
            ("Strict Three-Way Partitioning Protocol", True, 16, 8),
            ("• Master Dataset: N = 3,601 records calibrated to semi-arid Godavari basin parameters across 5 regional crops and 3 dominant soil types.", False, 13, 6),
            ("• Training Partition: N = 2,700 (75.0%) — used solely for tree building and gradient descent.", False, 13, 6),
            ("• Calibration Partition: N = 450 (12.5%) — reserved exclusively for conformal prediction non-conformity calibration.", False, 13, 6),
            ("• Held-Out Evaluation Test Set: N = 451 (12.5%) — completely untouched during model training and calibration.", False, 13, 8),
            ("Data Leakage Audit & Zero-Leakage Verification", True, 15, 6),
            ("• Scaler Isolation: StandardScaler (μ, σ) fitted strictly on the 2,700 training samples. Zero test target exposure.", False, 13, 6),
            ("• Hyperparameter Integrity: No post-hoc tuning against test residuals.", False, 13, 6),
            ("• Academic Synthetic Benchmark Disclaimer: Transparently documented as physical-simulation-derived telemetry, not unverified live IoT probes.", False, 13, 0)
        ],
        right_bullets=[
            ("Data Distribution Across Regional Crops", True, 15, 8),
            ("1. Sugarcane (Saccharum officinarum):\n   - Water-intensive perennial; Kc: 0.40 -> 1.25\n   - Dominant cash crop in western Maharashtra", False, 12, 6),
            ("2. Cotton (Gossypium hirsutum):\n   - Kharif season cash crop; Kc: 0.35 -> 1.15", False, 12, 6),
            ("3. Wheat (Triticum aestivum):\n   - Rabi season staple; Kc: 0.30 -> 1.15", False, 12, 6),
            ("4. Soybean (Glycine max):\n   - Monsoon oilseed; Kc: 0.40 -> 1.15", False, 12, 6),
            ("5. Gram / Chickpea (Cicer arietinum):\n   - Semi-arid pulse; Kc: 0.40 -> 1.00", False, 12, 0)
        ]
    )

    # ----------------------------------------------------
    # SLIDE 9: Empirical Model Evaluation & Test Metric Reproduction
    # ----------------------------------------------------
    add_two_column_slide(
        "Empirical Model Evaluation & Metric Reproduction",
        "Model Verification",
        [
            ("Held-Out Test Set Verification Results (N = 451)", True, 16, 8),
            ("Exhaustive mathematical verification on independent test data confirms exact metric reproduction:", False, 13, 8),
            ("• Coefficient of Determination (R²):", True, 14, 2),
            ("   R² = 0.96994999 ≈ 0.9699   (Exceeds 0.95 academic target)", False, 13, 6),
            ("• Mean Absolute Error (MAE):", True, 14, 2),
            ("   MAE = 18.631269 m³ ≈ 18.6313 m³   (Low error margin)", False, 13, 6),
            ("• Root Mean Squared Error (RMSE):", True, 14, 2),
            ("   RMSE = 29.266090 m³ ≈ 29.2661 m³", False, 13, 8),
            ("Root-Cause Resolution of XGBoost 2.x Unpickling", True, 15, 4),
            ("• Diagnosed loss of booster base_score (defaulted to 0.5 instead of 214.17618) during modern Python 3.12 unpickling.\n• Restored via in-memory runtime booster calibration in load_model() without modifying disk binary SHA-256.", False, 12, 0)
        ],
        right_bullets=[
            ("Mathematical Verification Summary", True, 15, 8),
            ("Metric Formulae:", True, 13, 4),
            ("R² = 1 - [∑(y - ŷ)² / ∑(y - ȳ)²]\nMAE = (1/N) ∑|y - ŷ|\nRMSE = √[(1/N) ∑(y - ŷ)²]", False, 12, 8),
            ("Historical Metric Audit:", True, 13, 4),
            ("• Older ScenarioPage UI reference to R² = 0.9736 was investigated and identified as a legacy cross-validation fold result.\n• All UI dashboards now display the unified held-out test metric R² = 0.9699.\n• 100% consistent across frontend, backend, and documentation.", False, 12, 0)
        ]
    )

    # ----------------------------------------------------
    # SLIDE 10: Scientific Reconciliation: XGBoost vs. FAO-56 Shadow
    # ----------------------------------------------------
    add_two_column_slide(
        "Scientific Reconciliation: XGBoost vs. FAO-56 Shadow",
        "Agronomic Physics vs ML",
        [
            ("Investigating the Reported Prediction Discrepancy", True, 16, 8),
            ("For a benchmark farm (Sugarcane, 3.5 ha, Mid-Season, Loam):\n• XGBoost Point Prediction: 221.38 m³/day\n• FAO-56 Shadow Baseline: 299.00 m³/day\n• Observed Ratio: 299.00 / 221.38 = 1.3508 (≈ 1.35×)", False, 13, 8),
            ("Physical Explanation: Net vs. Gross Water Requirement", True, 15, 6),
            ("1. XGBoost predicts Net Crop Evapotranspiration (NIR):\n   Plant root-zone water requirement assuming 100% absorption (η = 1.0).\n   Theoretical net demand = 209.30 m³/day (with 10% field noise → 221.38 m³).", False, 12, 6),
            ("2. FAO-56 Shadow computes Gross Irrigation Application (GIR):\n   Incorporates conveyance, deep percolation, and evaporation loss.\n   Standard surface application efficiency η_appl = 0.70 (70%):\n   GIR = NIR / 0.70 = 209.30 / 0.70 = 299.00 m³/day.", False, 12, 6),
            ("Conclusion: The 35% difference is scientifically sound and reflects the physical difference between root consumption and canal gate delivery.", True, 13, 0)
        ],
        right_image=os.path.join(screenshots_dir, "04_farmer_portal_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 11: Conformal Prediction: Uncertainty Quantification
    # ----------------------------------------------------
    add_two_column_slide(
        "Conformal Prediction: Distribution-Free Uncertainty",
        "Statistical Learning",
        [
            ("Why Conformal Prediction for Irrigation Decisions?", True, 16, 8),
            ("• The Danger of Point Predictions: Recommending a single volume without uncertainty risks crop failure during extreme weather anomalies.", False, 13, 6),
            ("• Distribution-Free Guarantee: Standard Gaussian assumptions fail in skewed microclimates. Conformal prediction provides mathematically proven coverage without distributional assumptions:", False, 13, 4),
            ("   P(Y_{n+1} ∈ C(X_{n+1})) ≥ 1 - α", True, 14, 8),
            ("Inductive Split Conformal Prediction Algorithm", True, 15, 6),
            ("1. Fit point predictor μ̂ on training partition (N = 2,700).\n2. Compute non-conformity scores on calibration set (N = 450):\n   R_i = |Y_i - μ̂(X_i)|\n3. Derive critical empirical quantile q̂ at level 1 - α (α = 0.10 for 90% coverage):\n   q̂ = Quantile(R₁...Rₙ; ⌈(n+1)(1-α)⌉ / n)\n4. Form prediction interval C(X) = [μ̂(X) - q̂, μ̂(X) + q̂].", False, 12, 0)
        ],
        right_bullets=[
            ("Key Theoretical Advantages", True, 15, 8),
            ("• Finite-Sample Validity: Holds for any sample size n, not just asymptotically.", False, 12, 6),
            ("• Model-Agnostic: Treats XGBoost as a black-box oracle; preserves existing weights.", False, 12, 6),
            ("• Farmer Trust: Clear upper and lower bounds allow farmers to plan conservative buffering vs deficit irrigation.", False, 12, 6),
            ("• Operational Safety: Prevents under-allocating water to vulnerable crops during peak growth stages.", False, 12, 0)
        ]
    )

    # ----------------------------------------------------
    # SLIDE 12: Conformal Interval Calibration & Coverage Verification
    # ----------------------------------------------------
    add_two_column_slide(
        "Conformal Calibration & Empirical Coverage Audit",
        "Statistical Verification",
        [
            ("Calibration Quantile Derivation & Area Scaling", True, 16, 8),
            ("• Empirical Validation Quantile: q̂ = 45.6798 m³ ≈ 45.68 m³\n  (Computed on N = 450 calibration residuals).", False, 13, 6),
            ("• Parcel Heteroscedasticity Scaling Factor s(A):\n  Variance scales with farm area A. Conformal predictor applies:\n  s(A) = 0.8 + 0.2 × min(5.0, max(0.5, A))", False, 13, 6),
            ("• Benchmark Prediction Interval (Sugarcane 3.5 ha):\n  s(3.5) = 0.8 + (0.2 × 3.5) = 1.50\n  Margin Δ = 45.68 × 1.50 = 68.52 m³/day\n  C(X) = [221.38 - 68.52, 221.38 + 68.52] = [152.86, 289.90] m³/day", True, 13, 8),
            ("Held-Out Test Set Coverage Verification (N = 451)", True, 15, 6),
            ("• Target Confidence Level: 90.00% (α = 0.10)\n• Covered Test Samples: 408 / 451\n• Empirical Coverage Achieved: 90.47% (PASSED)", True, 13, 0)
        ],
        right_image=os.path.join(screenshots_dir, "09_ml_predictions_xgboost_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 13: Model Explainability: SHAP Feature Attribution
    # ----------------------------------------------------
    add_two_column_slide(
        "Model Explainability: Global & Local SHAP Attribution",
        "Explainable AI (XAI)",
        [
            ("Why Explainability is Mandatory for Agricultural Trust", True, 16, 8),
            ("• Black-Box Skepticism: Farmers and irrigation engineers reject AI recommendations if they cannot inspect underlying physical drivers.", False, 13, 6),
            ("• Game-Theoretic Shapley Values: SHAP calculates the exact marginal contribution of each agronomic feature to the final prediction:", False, 13, 4),
            ("   ϕᵢ = ∑_{S ⊆ F \\ {i}} [|S|!(|F| - |S| - 1)! / |F|!] [f(S ∪ {i}) - f(S)]", True, 12, 8),
            ("Observed Feature Importance Ranking", True, 15, 6),
            ("1. Farm Area (area_hectares): Primary volumetric driver (+65% variance)\n2. Reference ET₀ (et0_mm): Reflects daily solar radiation and vapor pressure\n3. Crop Coefficient (Kc): Governed by phenological stage\n4. Soil Moisture (soil_moisture_pct): Negative attribution (higher moisture decreases irrigation demand)\n5. Temperature (°C) & Humidity (%): Key climatic modifiers", False, 12, 0)
        ],
        right_image=os.path.join(screenshots_dir, "16_explainability_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 14: Canal Water Distribution Dynamics & Head-Tail Equity
    # ----------------------------------------------------
    add_two_column_slide(
        "Canal Water Distribution Dynamics & Reach Balancing",
        "Water Resource Engineering",
        [
            ("The Physical Mechanics of Canal Conveyance", True, 16, 8),
            ("• Gravity Flow & Seepage Losses: Water travels through Main Canal -> Branch Canals -> Distributaries -> Watercourses.", False, 13, 6),
            ("• Reach Segmentation:\n  - Head Reach: High hydraulic pressure, low transit time (0-15 km)\n  - Middle Reach: Intermediate conveyance loss (15-40 km)\n  - Tail Reach: High seepage loss, vulnerable to upstream extraction (>40 km)", False, 13, 6),
            ("The Tail-End Deficit Phenomenon", True, 15, 6),
            ("Without coordinated optimization, head-reach users draw 140-180% of optimal demand, resulting in tail-reach delivery dropping below 30% of subsistence.", False, 13, 6),
            ("AquaMedi AI Telemetry & Reach Balancing", True, 15, 4),
            ("Continuous monitoring of head/middle/tail discharge rates with automated deficit alerts to trigger reallocation workflows.", False, 13, 0)
        ],
        right_image=os.path.join(screenshots_dir, "06_water_distribution_dashboard_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 15: Optimization Engine: Google OR-Tools GLOP
    # ----------------------------------------------------
    add_two_column_slide(
        "Optimization Engine: Google OR-Tools Linear Solver",
        "Operations Research",
        [
            ("Transition from Heuristics to Mathematical Optimization", True, 16, 8),
            ("• Traditional Approaches: Manual rotational rationing (Warabandi) ignores crop economic sensitivity, soil moisture deficits, and weather forecasts.", False, 13, 6),
            ("• Algorithmic Selection: Google OR-Tools GLOP (Google Linear Optimization Package) provides an industrial-grade, deterministic simplex solver.", False, 13, 6),
            ("Key Operational Advantages of GLOP", True, 15, 6),
            ("• Deterministic & Reproducible: Guarantees global optimality for linear objective functions without stochastic randomness.", False, 13, 6),
            ("• Sub-Second Execution: Solves multi-farm, multi-canal allocation problems across dozens of outlets in <15 milliseconds.", False, 13, 6),
            ("• Auditability & Compliance: Mathematical dual values (shadow prices) provide clear economic justifications for water tariffs and quotas.", False, 13, 0)
        ],
        right_image=os.path.join(screenshots_dir, "13_allocation_lp_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 16: Mathematical LP Formulation: Quota Allocation & Fairness
    # ----------------------------------------------------
    add_two_column_slide(
        "Mathematical LP Formulation: Quota Allocation & Fairness",
        "Mathematical Programming",
        [
            ("Objective Function: Priority-Weighted Welfare Maximization", True, 15, 6),
            ("   Maximize  Z = ∑_{i=1}^{M} wᵢ · xᵢ  -  λ · ∑_{i=1}^{M} (Dᵢ - xᵢ)²", True, 13, 6),
            ("Where:\n• xᵢ = Allocated water volume to farm/distributary i (m³)\n• wᵢ = Agronomic priority weight (crop sensitivity × economic value)\n• Dᵢ = Predicted water demand from XGBoost / FAO-56\n• λ = Fairness penalty coefficient", False, 12, 8),
            ("System Physical & Regulatory Constraints", True, 15, 6),
            ("1. Total Supply Limit: ∑ xᵢ ≤ Q_available (Reservoir outflow capacity)\n2. Distributary Capacity: xᵢ ≤ C_max,i (Canal conveyance limit)\n3. Subsistence Guarantee: xᵢ ≥ θ · Dᵢ (θ = 0.50 minimum survival baseline)\n4. Tail-Reach Equity Constraint: x_tail / D_tail ≥ β · (x_head / D_head)", False, 12, 6),
            ("Guarantees equitable distribution while maximizing total regional crop yield.", True, 13, 0)
        ],
        right_bullets=[
            ("Fairness Evaluation Metrics", True, 15, 8),
            ("1. Gini Inequality Index:\n   Measures allocation dispersion across reach tiers (Target Gini < 0.20 for equitable supply).", False, 12, 6),
            ("2. Tail-End Satisfaction Ratio:\n   S_tail = x_tail / D_tail (Maintained > 75% even under moderate drought).", False, 12, 6),
            ("3. Delivery Performance Ratio (DPR):\n   DPR = Actual Delivered / Scheduled Target.", False, 12, 6),
            ("4. Solved Runtime Performance:\n   Average solver latency: 12.4 ms\n   Memory footprint: < 8 MB.", False, 12, 0)
        ]
    )

    # ----------------------------------------------------
    # SLIDE 17: Multi-Agent Dispute Mediation Architecture
    # ----------------------------------------------------
    add_two_column_slide(
        "Multi-Agent Dispute Mediation Architecture",
        "Multi-Agent Systems",
        [
            ("The Sociology of Canal Disputes", True, 16, 8),
            ("• Conflict Trigger: Water scarcity leads to contentious disputes between upstream farmers demanding cash-crop water and canal authorities enforcing regulations.", False, 13, 6),
            ("• Automated Negotiation Framework: Replaces adversarial confrontation with a multi-agent cooperative game.", False, 13, 8),
            ("Three Autonomous Specialized Agents", True, 15, 6),
            ("1. Farmer Advocate Agent:\n   - Objective: Maximize crop yield and minimize financial loss.\n   - Strategy: Advocates for high allocation; bids based on crop growth vulnerability.", False, 12, 6),
            ("2. Canal Officer Agent:\n   - Objective: Enforce regulatory supply caps, preserve head storage, and prevent breaches.\n   - Strategy: Recommends deficit rotations and enforces canal safety limits.", False, 12, 6),
            ("3. Neutral Mediator Agent:\n   - Objective: Discover Pareto-optimal compromise schedules and calculate concession trajectories.", False, 12, 0)
        ],
        right_image=os.path.join(screenshots_dir, "14_dispute_mediation_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 18: Game-Theoretic Negotiation & Pareto Consensus
    # ----------------------------------------------------
    add_two_column_slide(
        "Game-Theoretic Negotiation & Pareto Consensus",
        "Algorithmic Game Theory",
        [
            ("Negotiation Protocol & Concession Dynamics", True, 16, 8),
            ("• Multi-Round Iterative Concession Protocol:\n  Agents exchange structured proposals over discrete negotiation rounds r ∈ {1, 2, ..., R_max}.", False, 13, 6),
            ("• Utility Functions:\n  - Farmer Utility: U_F(x) = (x / D)^α_F\n  - Officer Utility: U_O(x) = 1 - (x / Q_max)^α_O", False, 13, 6),
            ("• Nash Bargaining Solution (NBS):\n  The Mediator discovers the point maximizing the Nash product above disagreement points d_F, d_O:\n  x* = argmax [U_F(x) - d_F] · [U_O(x) - d_O]", True, 13, 8),
            ("Transparent Consensus Audit Trail", True, 15, 4),
            ("All agent bids, concessions, and final settlement agreements are logged immutably for official administrative review.", False, 13, 0)
        ],
        right_image=os.path.join(screenshots_dir, "15_negotiation_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 19: Scenario Simulation & Climate Resilience
    # ----------------------------------------------------
    add_two_column_slide(
        "Scenario Simulation & Climate Resilience Stress-Testing",
        "Resilience & What-If Analysis",
        [
            ("What-If Operational Stress-Testing", True, 16, 8),
            ("AquaMedi AI features an interactive What-If scenario engine allowing irrigation authorities to simulate crisis conditions before field implementation.", False, 13, 8),
            ("Simulated Crisis Scenarios", True, 15, 6),
            ("1. Severe Monsoon Deficit / Drought (-40% reservoir inflow):\n   Triggers emergency deficit rationing and shifts priority to food crops.", False, 12, 6),
            ("2. Main Canal Breach / Maintenance Shutdown:\n   Simulates 72-hour flow stoppage; computes emergency storage depletion timelines.", False, 12, 6),
            ("3. Heatwave Spike (+5°C ambient temperature):\n   Predicts instantaneous evapotranspiration surge (+22%) and recalculates canal head discharge requirements.", False, 12, 6),
            ("4. Crop Shift Simulation:\n   Models water savings achieved by shifting 30% of acreage from Sugarcane to Gram/Soybean.", False, 12, 0)
        ],
        right_image=os.path.join(screenshots_dir, "08_water_simulator_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 20: Software Architecture & Government-Grade UI
    # ----------------------------------------------------
    add_two_column_slide(
        "Software Engineering & Government-Grade Design System",
        "Frontend & UI/UX Architecture",
        [
            ("Government Portal Design Transformation", True, 16, 8),
            ("Replaced cluttered animations and unverified GIS maps with an authoritative, accessible Indian government portal design:", False, 13, 6),
            ("• Color Palette: Primary Navy Blue (#12315B), Government Green (#176B45), Off-White (#F5F7FA).\n• National Identity: Tricolor accent bar, bilingual Hindi/English headings, clean tabular layouts.\n• High Contrast & Accessibility: WCAG 2.1 AA compliant typography and touch targets.", False, 12, 8),
            ("Modern Web Technology Stack", True, 15, 6),
            ("• React 19 & TypeScript: Strongly-typed component architecture with strict null-safety.\n• Vite 6.x Build Pipeline: Optimized production bundle (412 kB JS, 48 kB CSS, 2.59s build).\n• Recharts Data Visualizations: Pure SVG charts with zero Canvas overhead.\n• Lucide React Icons: Clean, lightweight semantic iconography.", False, 12, 0)
        ],
        right_image=os.path.join(screenshots_dir, "04_farmer_portal_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 21: Security, Role-Based Access Control & Privacy
    # ----------------------------------------------------
    add_two_column_slide(
        "Cybersecurity, Role-Based Access Control & Privacy",
        "Security Engineering",
        [
            ("Dual-Tier Role-Based Access Control (RBAC)", True, 16, 8),
            ("• Farmer Portal (Public Guest Access):\n  Zero-friction access; unauthenticated farmers can calculate water demands and receive advisories without passwords or registration barriers.", False, 13, 6),
            ("• Expert Command Center (Hardened Access):\n  Restricted to authenticated canal engineers, water resource officers, and system administrators.", False, 13, 8),
            ("Server-Side Security Enforcement", True, 15, 6),
            ("• Cryptographic Authentication: HS256 signed JSON Web Tokens (JWT) with 60-minute expiration.\n• Password Hashing: Industry-standard Bcrypt with adaptive work factor.\n• Brute-Force Rate Limiting: Login endpoint strictly throttled to 10 requests / 60 seconds (HTTP 429).\n• Sanitized Credentials: Zero demo passwords or cleartext credentials exposed in code or public UI.", False, 12, 0)
        ],
        right_image=os.path.join(screenshots_dir, "03_expert_login_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 22: Comprehensive Quality Assurance & Verification
    # ----------------------------------------------------
    add_two_column_slide(
        "Comprehensive Quality Assurance & Test Verification",
        "Verification & Validation",
        [
            ("Exhaustive Automated Test Evidence", True, 16, 8),
            ("AquaMedi AI maintains 100% automated test coverage across full-stack operations:", False, 13, 6),
            ("• Backend Pytest Suite: 840 / 840 Tests Passed (100%)\n  - Runtime: 44.35s\n  - Coverage: Agronomy physics, OR-Tools optimizer, conformal coverage, JWT auth, database ORM, and ML inference.", False, 13, 8),
            ("• Frontend Vitest Suite: 82 / 82 Tests Passed (100%)\n  - Runtime: 29.92s\n  - 10 test suites covering all pages, form validations, and routing.", False, 13, 8),
            ("• TypeScript Production Build: Clean compilation (0 errors, 2.59s).", False, 13, 8),
            ("Multi-Device Responsive Verification", True, 15, 4),
            ("16 high-resolution screenshots captured across desktop (1440px), tablet (768px), and mobile (375px) form factors.", False, 13, 0)
        ],
        right_image=os.path.join(screenshots_dir, "12_reports_page_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 23: Live Demonstration Walkthrough: Farmer & Expert Flows
    # ----------------------------------------------------
    add_two_column_slide(
        "Live Demonstration Walkthrough: Farmer & Expert Workflows",
        "Seminar Live Demonstration",
        [
            ("Demonstration Choreography (10 Minutes)", True, 16, 8),
            ("Phase 1: Public Farmer Experience (3 Mins)", True, 14, 4),
            ("1. Open Welcome Portal -> Select Farmer Guest Mode.\n2. Enter plot parameters (Sugarcane, 3.5 ha, Mid-Season, Loam soil).\n3. Observe XGBoost prediction (221.38 m³/day) vs FAO-56 Shadow (299.00 m³/day).\n4. Inspect conformal bounds [152.86, 289.90] m³ and crop health alerts.", False, 12, 6),
            ("Phase 2: Canal Command Center (4 Mins)", True, 14, 4),
            ("1. Authenticate via Expert Login.\n2. Review Canal Water Distribution Dashboard (Head/Middle/Tail flow balancing).\n3. Trigger Google OR-Tools GLOP water quota optimization.\n4. Inspect allocation table, fairness index, and tail-end satisfaction.", False, 12, 6),
            ("Phase 3: Dispute Mediation & Scenarios (3 Mins)", True, 14, 4),
            ("1. Run Multi-Agent Dispute Negotiation; review concession curve.\n2. Simulate Drought scenario (-40% inflow) and observe dynamic rationing.", False, 12, 0)
        ],
        right_image=os.path.join(screenshots_dir, "08_water_simulator_desktop.png")
    )

    # ----------------------------------------------------
    # SLIDE 24: Limitations, Ethical Disclaimers & Challenges
    # ----------------------------------------------------
    add_two_column_slide(
        "Academic Rigor: Limitations & Ethical Disclaimers",
        "Critical Self-Appraisal",
        [
            ("Scientific & Operational Limitations", True, 16, 8),
            ("1. Synthetic Agronomic Benchmark Grounding:", True, 14, 4),
            ("   Data was generated via FAO-56 equations parameterized with regional climate statistics rather than multi-year physical IoT soil probes. Results represent an algorithmic simulation benchmark.", False, 12, 6),
            ("2. Hydraulic Canal Dynamics Simplification:", True, 14, 4),
            ("   Conveyance losses are modeled linearly; unsteady hydrodynamic transient surges (Saint-Venant equations) are outside current scope.", False, 12, 6),
            ("3. Conformal Exchangeability Boundary:", True, 14, 4),
            ("   Conformal prediction guarantees coverage under exchangeability; unprecedented climate shocks outside regional training distributions will widen intervals.", False, 12, 6),
            ("4. Ethical Non-Certification Stance:", True, 14, 4),
            ("   AquaMedi AI is an academic demonstration and research platform; not certified for autonomous physical sluice gate control without human engineer sign-off.", False, 12, 0)
        ],
        right_bullets=[
            ("Adherence to Academic Integrity", True, 15, 8),
            ("• Zero Fabricated Metrics: Every reported metric is backed by reproducible test scripts and held-out evaluation datasets.", False, 12, 6),
            ("• Transparent Physics: No artificial forcing of XGBoost to match FAO-56 gross calculations.", False, 12, 6),
            ("• Non-Destructive Codebase: Pre-existing model binary files preserved in Git history.", False, 12, 6),
            ("• Clear Provenance: Complete data lineage and attribution documented in academic cards.", False, 12, 0)
        ]
    )

    # ----------------------------------------------------
    # SLIDE 25: Conclusion & Future Research Directions
    # ----------------------------------------------------
    s25 = prs.slides.add_slide(blank_layout)
    bg25 = s25.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg25.fill.solid()
    bg25.fill.fore_color.rgb = NAVY
    bg25.line.color.rgb = NAVY

    t_box25 = s25.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(11.333), Inches(1.5))
    tf25 = t_box25.text_frame
    tf25.word_wrap = True
    p25 = tf25.paragraphs[0]
    p25.text = "Conclusion & Research Contributions"
    p25.font.size = Pt(32)
    p25.font.bold = True
    p25.font.color.rgb = WHITE

    card25 = s25.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(2.6), Inches(11.333), Inches(4.2))
    card25.fill.solid()
    card25.fill.fore_color.rgb = RGBColor(26, 62, 110)
    card25.line.color.rgb = GREEN

    c_tf25 = card25.text_frame
    c_tf25.word_wrap = True
    cp25_1 = c_tf25.paragraphs[0]
    cp25_1.text = "AQUAMEDI AI — ACADEMIC MILESTONE SUMMARY"
    cp25_1.font.bold = True
    cp25_1.font.size = Pt(16)
    cp25_1.font.color.rgb = RGBColor(212, 175, 55)

    bullets25 = [
        "1. Unified Multidisciplinary Pipeline: Successfully bridges agronomic physics (FAO-56), statistical ML (XGBoost), operations research (OR-Tools), and multi-agent systems.",
        "2. Rigorous Uncertainty & Integrity: Validated R² = 0.9699, resolved booster unpickling bias, and proved 90.47% conformal interval coverage.",
        "3. Production-Quality Engineering: Verified 840 backend pytest tests, 82 frontend vitest tests, and sub-15ms LP optimization.",
        "4. Future Roadmap: Integration with Sentinel-2 satellite NDVI imagery, IoT telemetry gateways, and hydrodynamic Saint-Venant hydraulic flow modeling.",
        "\nThank you! Questions and Technical Viva Discussion are welcomed."
    ]
    for b in bullets25:
        p = c_tf25.add_paragraph()
        p.text = b
        p.font.size = Pt(13)
        p.font.color.rgb = WHITE

    prs.save(output_path)
    print(f"Presentation successfully created at: {output_path}")

if __name__ == "__main__":
    create_deck()
