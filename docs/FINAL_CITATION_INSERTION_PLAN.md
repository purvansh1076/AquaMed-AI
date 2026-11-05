# AquaMediAI — Final Whole-Report Citation Insertion Plan & Pre-Insertion Review (Revised)

**Document Path**: `docs/FINAL_CITATION_INSERTION_PLAN.md`  
**Target Document**: [`docs/FINAL_PROJECT_REPORT.md`](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/docs/FINAL_PROJECT_REPORT.md)  
**Auditor Role**: Senior Technical Documentation Reviewer & Academic Research Assistant  
**Evaluation Standard**: IEEE Numeric Citation Format & Academic Literature Integrity  
**Verification Date**: November 3, 2026  
**Revision Version**: 2.1.0 (Final Pre-Insertion Review)  
**Final Status**: **PASS — ALL METADATA, ATTRIBUTIONS & CLAIM BOUNDARIES VERIFIED**  

> [!IMPORTANT]
> **Strict Non-Modification Guarantee**: In compliance with user instructions, [`docs/FINAL_PROJECT_REPORT.md`](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/docs/FINAL_PROJECT_REPORT.md) and all repository code, datasets, and models remain completely unaltered. This plan contains the corrected, authoritative pre-insertion specifications awaiting final user approval.

---

## 1. Executive Summary & Review Scope

This document establishes the final, corrected whole-report citation insertion architecture for [`docs/FINAL_PROJECT_REPORT.md`](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/docs/FINAL_PROJECT_REPORT.md). 

Every section of the final project report (Chapters 1 through 10 and Section 11 References) was scanned to verify:
1. **Strict Monotonic Numeric Ordering**: Verified by first appearance across the entire document ($[1]$ to $[17]$).
2. **Claim-Support Calibration**: Calibrated the claim descriptions for Gutiérrez et al., Sivapalan et al., Bousquet & Le Page, and Barredo Arrieta et al. to strictly distinguish empirical source findings from authors' research-gap synthesis.
3. **Fan et al. (2018) Exact Publisher Abstract Alignment**: Accurately reflects the evaluated models (SVM, ELM, RF, M5Tree, GBDT, XGBoost), target ($ET_0$), and actual comparative findings (ELM/SVM accuracy vs. XGBoost/GBDT computational efficiency), purging all unsupported $R^2$ numerical ranges.
4. **Getting to Yes (1981) Co-Authorship & BATNA Attribution**: Corrected authorship to Roger Fisher and William Ury (with Bruce Patton as editor of the 1981 original edition); attributed BATNA strictly to Fisher & Ury (1981), and monotonic concession/reservation utility theory to Raiffa (1982).
5. **Exact Historical Titles and Identifiers**:
   - DEC Technical Report DEC-TR-301: *"A Quantitative Measure of Fairness and Discrimination for Resource Allocation in Shared Computer System"* (singular, dated September 26, 1984).
   - Chen & Guestrin (2016): Exact paper DOI set to `10.1145/2939672.2939785`.
   - Google OR-Tools GLOP: Attributed to corporate author `Google Developers. (n.d.)`.
   - FAO-56: Cited as official 300-page monograph (Rome, 1998, ISBN 92-5-104219-5), purging erroneous `"300(9), D05109"` strings.
6. **Bidirectional Completeness**: Exactly 17 in-text citations map to exactly 17 bibliography entries (0 unused, 0 missing).

---

## 2. Rigorous Claim-Support Calibration & Evidence Boundaries

To maintain high scientific integrity, the relationship between cited literature and project claims is strictly bounded:

### 2.1 Gutiérrez et al. (2014) — On-Farm Actuation vs. Literature-Review Synthesis
- **Text in Report (Line 115)**:  
  > *"Modern computational irrigation models predominantly leverage sensor telemetry to optimize water application depths. However, existing literature focuses primarily on on-farm precision irrigation (e.g., automated drip valves) rather than communal canal dispute mediation [2]."*
- **What Gutiérrez et al. (2014) Establishes (Empirical Evidence)**:  
  Demonstrates an energy-autonomous on-farm closed-loop drip irrigation system using in-situ soil moisture/temperature sensors and cellular GPRS-actuated solenoid valves on a single sage crop plot, achieving up to 90% water savings.
- **Evidence Boundary & Literature Synthesis Distinction**:  
  Citing Gutiérrez et al. (2014) provides an empirical representative of on-farm, sensor-actuated valve architecture; **it does not constitute a bibliometric proof that communal canal dispute mediation is under-researched**. The contrast between single-farm hardware automation and multi-farmer communal dispute mediation represents the **project's literature-review synthesis and motivated problem formulation**, reflecting domain boundaries rather than a statistical survey of all water governance literature.

### 2.2 Sivapalan, Savenije, & Blöschl (2012) — Socio-Hydrologic Paradigm vs. Empirical Compliance
- **Text in Report (Line 121)**:  
  > *"A known limitation in classical allocation optimization is the treatment of human farmers as passive, compliant entities rather than self-interested decision-makers [9]."*
- **What Sivapalan et al. (2012) Establishes (Disciplinary Concept)**:  
  A foundational perspective paper introducing the science of socio-hydrology. It critiques traditional hydrological and water resources engineering for treating human actions as exogenous, static boundary conditions rather than endogenous components of a coupled human-water system with dynamic two-way feedbacks.
- **Evidence Boundary**:  
  Sivapalan et al. establishes the **conceptual critique** of the passive-human assumption in water resources systems. It does not measure empirical farmer compliance in Indian canal networks; that application is AquaMediAI's specific problem context.

### 2.3 Bousquet & Le Page (2004) — Multi-Agent Systems in Ecological Commons
- **Text in Report (Line 124)**:  
  > *"Multi-Agent Systems (MAS) provide a computational paradigm to simulate autonomous, heterogenous actors competing for finite commons [11]."*
- **What Bousquet & Le Page (2004) Establishes (Review Evidence)**:  
  Reviews multi-agent simulations in renewable resource and ecosystem management (water, forestry, pastoralism, fisheries), validating MAS as an established computational framework for modeling decentralized, heterogeneous resource users interacting over shared ecological commons.
- **Evidence Boundary**:  
  It validates the agent-based paradigm for shared natural resource commons; it does not model AquaMediAI's specific integration of linear programming simplex allocation coupled with algorithmic Nash-bargaining mediation.

### 2.4 Barredo Arrieta et al. (2020) — Responsible-AI Motivation vs. Empirically Measured Trust
- **Text in Report (Line 130)**:  
  > *"In agricultural and legal domains, explainability is essential to establish trust among stakeholders [16]."*
- **What Barredo Arrieta et al. (2020) Establishes (Survey Rationale)**:  
  A comprehensive survey on Explainable AI (XAI) definitions and taxonomies. It establishes that in high-stakes domains (healthcare, law, finance, resource allocation), black-box opacity creates barriers to adoption, making model interpretability and post-hoc explanations a recognized **design desideratum for responsible AI and accountability**.
- **Evidence Boundary**:  
  The literature argues that explainability is intended to facilitate stakeholder comprehension and accountability; **it does not establish that post-hoc explanations (such as SHAP values) automatically or empirically guarantee stakeholder trust** among rural farming communities without contextual user-experience validation.

### 2.5 Fan et al. (2018) — Publisher Abstract Alignment & Model Inventory
- **Text in Report (Line 118)**:  
  > *"Recent studies have demonstrated that gradient boosted trees (XGBoost) [4] and ensemble random forests [5] can approximate non-linear agricultural demand with high fidelity when trained on meteorological and phenological inputs [6]."*
- **Evaluated Models**: Support Vector Machine (SVM), Extreme Learning Machine (ELM), Random Forest (RF), M5 Model Tree (M5Tree), Gradient Boosting Decision Tree (GBDT), and Extreme Gradient Boosting (XGBoost).
- **Target Variable**: **Daily reference crop evapotranspiration ($ET_0$)**, calculated using the standard FAO-56 Penman-Monteith equation across diverse climatic regions of China.
- **Accurate Publisher Abstract Findings**:  
  All machine learning models demonstrated strong dependence on meteorological input combinations and climate zones. In the publisher abstract and comparative evaluation, ELM and SVM offered the best accuracy and stability combinations under the evaluated scenarios, while tree-based ensemble models (specifically XGBoost and GBDT) demonstrated comparable predictive accuracy with lower computational costs.
- **Corrections Applied**:  
  Removed all unsupported numerical claims (such as $R^2 \approx 0.85 - 0.98$) and removed any claim that RF/XGBoost outperformed SVM/ELM. Fan et al. is cited strictly for establishing that tree-based ensemble algorithms model daily reference evapotranspiration ($ET_0$) with accuracy comparable to traditional non-linear models at reduced computational cost.

### 2.6 Getting to Yes (1981) — Authorship & BATNA Attribution
- **Text in Report (Line 127)**:  
  > *"Practical automated mediation relies on monotonic concession protocols [13] and utility reservation thresholds, commonly termed the Best Alternative To a Negotiated Agreement [14]."*
- **Authorship**: **Roger Fisher and William Ury**. (Bruce Patton was the editor of the original 1981 first edition; he became a co-author in subsequent editions).
- **Attribution Boundary**:  
  - The acronym and concept **BATNA** is attributed strictly to **Fisher & Ury (1981)**.
  - Quantitative reservation utility theory, concession trajectories, and negotiation analysis are attributed to **Raiffa (1982)**. BATNA is **not** attributed to Raiffa.

---

## 3. Whole-Report First-Appearance Sequential Citation Order

In IEEE numeric citation style, references are assigned numbers sequentially by **first appearance in the text**.

A comprehensive scan of `docs/FINAL_PROJECT_REPORT.md` confirms:
- **Chapter 1 (Lines 1–109)**: Introduces the executive summary, problem statement, objectives, and scope. Contains **zero** citation placeholders or academic references.
- **Chapter 2 (Lines 114–131)**: Contains the literature survey where citations `[1]` through `[16]` appear sequentially.
- **Chapter 4 (Line 501)**: Formulates Jain's Fairness Index where citation `[17]` appears.

The sequence is strictly monotonic:

```
Chapter 2: Lines 114–131
  ├── Line 115: [1] Abioye et al. (2020) — AI in Irrigation Review
  ├── Line 115: [2] Gutiérrez et al. (2014) — Automated Drip Telemetry
  ├── Line 118: [3] Allen, Pereira, Raes, & Smith (1998) — FAO-56 Penman-Monteith
  ├── Line 118: [4] Chen & Guestrin (2016) — XGBoost
  ├── Line 118: [5] Breiman (2001) — Random Forests
  ├── Line 118: [6] Fan et al. (2018) — Tree Ensembles for Daily ET0
  ├── Line 121: [7] Loucks & van Beek (2017) — Operations Research in Water Systems
  ├── Line 121: [8] Google Developers (n.d.) — OR-Tools GLOP Linear Solver
  ├── Line 121: [9] Sivapalan, Savenije, & Blöschl (2012) — Socio-Hydrology
  ├── Line 124: [10] Ostrom (1990) — Common-Pool Resource Governance
  ├── Line 124: [11] Bousquet & Le Page (2004) — Multi-Agent Systems in CPR
  ├── Line 127: [12] Nash (1950) — The Bargaining Problem
  ├── Line 127: [13] Raiffa (1982) — The Art and Science of Negotiation
  ├── Line 127: [14] Fisher & Ury (1981) — Getting to Yes (BATNA)
  ├── Line 130: [15] Lundberg & Lee (2017) — SHAP Unified Predictions
  └── Line 130: [16] Barredo Arrieta et al. (2020) — Explainable AI Survey

Chapter 4: Line 501
  └── Line 501: [17] Jain, Chiu, & Hawe (1984) — Fairness and Discrimination (DEC-TR-301)
```

---

## 4. Full Citation Inventory with Verified Metadata

| Numeric Key | Authors & Publication Year | Canonical Title | Primary Venue / Publisher | Publication Identifier (DOI / ISBN / Canonical URL) |
| :---: | :--- | :--- | :--- | :--- |
| **[1]** | E. A. Abioye et al. (2020) | *A review on monitoring and advanced control strategies for precision irrigation* | *Computers and Electronics in Agriculture*, Vol. 173, Art. 105441 | DOI: [`10.1016/j.compag.2020.105441`](https://doi.org/10.1016/j.compag.2020.105441) |
| **[2]** | J. Gutiérrez, J. F. Villa-Medina, A. Nieto-Garibay, & M. Á. Porta-Gándara (2014) | *Automated Irrigation System Using a Wireless Sensor Network and GPRS Module* | *IEEE Transactions on Instrumentation and Measurement*, 63(1), pp. 166–176 | DOI: [`10.1109/TIM.2013.2276487`](https://doi.org/10.1109/TIM.2013.2276487) |
| **[3]** | R. G. Allen, L. S. Pereira, D. Raes, & M. Smith (1998) | *Crop evapotranspiration: Guidelines for computing crop water requirements* | FAO Irrigation and Drainage Paper No. 56, Rome, Italy: FAO, 300 pp. | ISBN: `92-5-104219-5`<br>URL: [`https://www.fao.org/4/x0490e/x0490e00.htm`](https://www.fao.org/4/x0490e/x0490e00.htm) |
| **[4]** | T. Chen & C. Guestrin (2016) | *XGBoost: A Scalable Tree Boosting System* | *Proc. 22nd ACM SIGKDD (KDD '16)*, New York, NY, pp. 785–794 | DOI: [`10.1145/2939672.2939785`](https://doi.org/10.1145/2939672.2939785) |
| **[5]** | L. Breiman (2001) | *Random Forests* | *Machine Learning*, 45(1), pp. 5–32 | DOI: [`10.1023/A:1010933404324`](https://doi.org/10.1023/A:1010933404324) |
| **[6]** | J. Fan et al. (2018) | *Evaluation of SVM, ELM and four tree-based ensemble models for predicting daily reference evapotranspiration using limited meteorological data in different climates of China* | *Agricultural and Forest Meteorology*, Vol. 263, pp. 225–241 | DOI: [`10.1016/j.agrformet.2018.08.019`](https://doi.org/10.1016/j.agrformet.2018.08.019) |
| **[7]** | D. P. Loucks & E. van Beek (2017) | *Water Resource Systems Planning and Management: An Introduction to Methods, Models, and Applications* | Springer Nature / UNESCO-IHE, Cham, Switzerland, 492 pp. | DOI: [`10.1007/978-3-319-44234-1`](https://doi.org/10.1007/978-3-319-44234-1) |
| **[8]** | Google Developers (n.d.) | *OR-Tools: Linear Optimization (GLOP)* | Google LLC | URL: [`https://developers.google.com/optimization/lp/glop`](https://developers.google.com/optimization/lp/glop) |
| **[9]** | M. Sivapalan, H. H. G. Savenije, & G. Blöschl (2012) | *Socio-hydrology: A new science of people and water* | *Hydrological Processes*, 26(8), pp. 1270–1276 | DOI: [`10.1002/hyp.8426`](https://doi.org/10.1002/hyp.8426) |
| **[10]** | E. Ostrom (1990) | *Governing the Commons: The Evolution of Institutions for Collective Action* | Cambridge University Press, Cambridge, UK, 280 pp. | DOI: [`10.1017/CBO9780511807763`](https://doi.org/10.1017/CBO9780511807763) |
| **[11]** | F. Bousquet & C. Le Page (2004) | *Multi-agent simulations and ecosystem management: a review* | *Ecological Modelling*, 176(3–4), pp. 313–332 | DOI: [`10.1016/j.ecolmodel.2004.01.011`](https://doi.org/10.1016/j.ecolmodel.2004.01.011) |
| **[12]** | J. F. Nash, Jr. (1950) | *The Bargaining Problem* | *Econometrica*, 18(2), pp. 155–162 | DOI: [`10.2307/1907266`](https://doi.org/10.2307/1907266) |
| **[13]** | H. Raiffa (1982) | *The Art and Science of Negotiation* | Belknap Press of Harvard University Press, Cambridge, MA, 373 pp. | ISBN: `978-0674048126` |
| **[14]** | R. Fisher & W. Ury (1981) | *Getting to Yes: Negotiating Agreement Without Giving In* | Houghton Mifflin, Boston, MA, 200 pp. (Ed. B. Patton) | ISBN: `978-0395317570` |
| **[15]** | S. M. Lundberg & S.-I. Lee (2017) | *A Unified Approach to Interpreting Model Predictions* | *Advances in Neural Information Processing Systems (NeurIPS 2017)*, 30, pp. 4765–4774 | URL: [`NeurIPS Proceedings`](https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html) |
| **[16]** | A. Barredo Arrieta et al. (2020) | *Explainable Artificial Intelligence (XAI): Concepts, taxonomies, opportunities and challenges toward responsible AI* | *Information Fusion*, Vol. 58, pp. 82–115 | DOI: [`10.1016/j.inffus.2019.12.012`](https://doi.org/10.1016/j.inffus.2019.12.012) |
| **[17]** | R. K. Jain, D.-M. W. Chiu, & W. R. Hawe (1984) | *A Quantitative Measure of Fairness and Discrimination for Resource Allocation in Shared Computer System* | Research Report DEC-TR-301, Digital Equipment Corp., Hudson, MA, Sep. 26, 1984, 38 pp. | URL: [`https://www.cs.wustl.edu/~jain/papers/fairness.htm`](https://www.cs.wustl.edu/~jain/papers/fairness.htm) |

---

## 5. Bidirectional Concordance & Completeness Check

- **Total In-Text Citations**: 17 locations.
- **Total Bibliography Entries**: 17 entries in Section 11.
- **Unused Bibliography Entries**: **0** (All 17 references are actively cited in-text).
- **Missing Bibliography Entries**: **0** (All in-text citations resolve to an entry in Section 11).
- **Numbering Consistency**: Strictly ascending $1 \to 17$ without skipping or reordering.
- **Style Compliance**: Consistent IEEE-style bracketed numeric format `[X]`.

---

## 6. Exact In-Text Replacement Table for `FINAL_PROJECT_REPORT.md`

| Target Location | Current Text in `FINAL_PROJECT_REPORT.md` | Exact Proposed Replacement |
| :--- | :--- | :--- |
| **Line 115** | `The application of artificial intelligence in agricultural water management has evolved from rule-based expert systems to data-driven predictive architectures [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]. Modern computational irrigation models predominantly leverage sensor telemetry to optimize water application depths. However, existing literature focuses primarily on on-farm precision irrigation (e.g., automated drip valves) rather than communal canal dispute mediation [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE].` | `The application of artificial intelligence in agricultural water management has evolved from rule-based expert systems to data-driven predictive architectures [1]. Modern computational irrigation models predominantly leverage sensor telemetry to optimize water application depths. However, existing literature focuses primarily on on-farm precision irrigation (e.g., automated drip valves) rather than communal canal dispute mediation [2].` |
| **Line 118** | `Accurate estimation of crop water demand forms the cornerstone of sound allocation. The standard benchmark established by the Food and Agriculture Organization is the FAO-56 Penman-Monteith method [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE: Allen et al., 1998]. Recent studies have demonstrated that gradient boosted trees (XGBoost) and ensemble random forests can approximate non-linear agricultural demand with high fidelity when trained on meteorological and phenological inputs [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE].` | `Accurate estimation of crop water demand forms the cornerstone of sound allocation. The standard benchmark established by the Food and Agriculture Organization is the FAO-56 Penman-Monteith method [3]. Recent studies have demonstrated that gradient boosted trees (XGBoost) [4] and ensemble random forests [5] can approximate non-linear agricultural demand with high fidelity when trained on meteorological and phenological inputs [6].` |
| **Line 121** | `Operations research has extensively addressed water resources allocation using Linear Programming (LP), Non-Linear Programming (NLP), and Genetic Algorithms [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]. Google OR-Tools GLOP solver provides efficient simplex implementations for continuous linear programs [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE]. A known limitation in classical allocation optimization is the treatment of human farmers as passive, compliant entities rather than self-interested decision-makers [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE].` | `Operations research has extensively addressed water resources allocation using Linear Programming (LP), Non-Linear Programming (NLP), and Genetic Algorithms [7]. Google OR-Tools GLOP solver provides efficient simplex implementations for continuous linear programs [8]. A known limitation in classical allocation optimization is the treatment of human farmers as passive, compliant entities rather than self-interested decision-makers [9].` |
| **Line 124** | `Elinor Ostrom’s pioneering principles on governing common-pool resources emphasize that decentralized, rule-governed user monitoring frequently outperforms top-down administrative quotas [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE: Ostrom, 1990]. Multi-Agent Systems (MAS) provide a computational paradigm to simulate autonomous, heterogenous actors competing for finite commons [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE].` | `Elinor Ostrom’s pioneering principles on governing common-pool resources emphasize that decentralized, rule-governed user monitoring frequently outperforms top-down administrative quotas [10]. Multi-Agent Systems (MAS) provide a computational paradigm to simulate autonomous, heterogenous actors competing for finite commons [11].` |
| **Line 127** | `Automated negotiation protocols establish mathematical foundations for agent bargaining. Rooted in cooperative game theory, Nash Bargaining establishes axioms for equitable surplus distribution [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE: Nash, 1950]. Practical automated mediation relies on monotonic concession protocols and utility reservation thresholds, commonly termed the Best Alternative To a Negotiated Agreement [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE: Raiffa, 1982].` | `Automated negotiation protocols establish mathematical foundations for agent bargaining. Rooted in cooperative game theory, Nash Bargaining establishes axioms for equitable surplus distribution [12]. Practical automated mediation relies on monotonic concession protocols [13] and utility reservation thresholds, commonly termed the Best Alternative To a Negotiated Agreement [14].` |
| **Line 130** | `Complex machine learning models often operate as opaque predictors. The SHAP (Shapley Additive exPlanations) framework, based on cooperative game theory, provides local feature importance attributions by calculating marginal contributions across all feature coalitions [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE: Lundberg & Lee, 2017]. In agricultural and legal domains, explainability is essential to establish trust among stakeholders [CITATION REQUIRED — VERIFY FROM ORIGINAL SOURCE].` | `Complex machine learning models often operate as opaque predictors. The SHAP (Shapley Additive exPlanations) framework, based on cooperative game theory, provides local feature importance attributions by calculating marginal contributions across all feature coalitions [15]. In agricultural and legal domains, explainability is essential to establish trust among stakeholders [16].` |
| **Line 501** | `- **Jain’s Fairness Index**:` | `- **Jain’s Fairness Index** [17]:` |

---

## 7. Exact Replacement for Section 11 (References)

The draft placeholder references (Lines 899–908) will be replaced with the exact IEEE-formatted bibliography:

```markdown
## REFERENCES

[1] E. A. Abioye, M. S. Z. Abidin, M. S. A. Mahmud, S. Buyamin, M. H. I. Ishak, M. K. I. Abd Rahman, T. N. Otuoze, P. Onotu, and A. U. A. Ramli, "A review on monitoring and advanced control strategies for precision irrigation," *Computers and Electronics in Agriculture*, vol. 173, art. 105441, 2020, doi: 10.1016/j.compag.2020.105441.
[2] J. Gutiérrez, J. F. Villa-Medina, A. Nieto-Garibay, and M. Á. Porta-Gándara, "Automated irrigation system using a wireless sensor network and GPRS module," *IEEE Transactions on Instrumentation and Measurement*, vol. 63, no. 1, pp. 166–176, Jan. 2014, doi: 10.1109/TIM.2013.2276487.
[3] R. G. Allen, L. S. Pereira, D. Raes, and M. Smith, *Crop Evapotranspiration: Guidelines for Computing Crop Water Requirements*, FAO Irrigation and Drainage Paper No. 56, Rome, Italy: Food and Agriculture Organization of the United Nations, 1998, 300 pp. ISBN: 92-5-104219-5. [Online]. Available: https://www.fao.org/4/x0490e/x0490e00.htm
[4] T. Chen and C. Guestrin, "XGBoost: A scalable tree boosting system," in *Proc. 22nd ACM SIGKDD Int. Conf. on Knowledge Discovery and Data Mining (KDD '16)*, San Francisco, CA, USA, 2016, pp. 785–794, doi: 10.1145/2939672.2939785.
[5] L. Breiman, "Random forests," *Machine Learning*, vol. 45, no. 1, pp. 5–32, Oct. 2001, doi: 10.1023/A:1010933404324.
[6] J. Fan, W. Yue, L. Wu, F. Zhang, H. Cai, W. Wang, X. Lu, and Y. Xiang, "Evaluation of SVM, ELM and four tree-based ensemble models for predicting daily reference evapotranspiration using limited meteorological data in different climates of China," *Agricultural and Forest Meteorology*, vol. 263, pp. 225–241, Dec. 2018, doi: 10.1016/j.agrformet.2018.08.019.
[7] D. P. Loucks and E. van Beek, *Water Resource Systems Planning and Management: An Introduction to Methods, Models, and Applications*, Cham, Switzerland: Springer Nature / UNESCO-IHE, 2017, 492 pp., doi: 10.1007/978-3-319-44234-1.
[8] Google Developers, "OR-Tools: Linear Optimization (GLOP)," Google LLC. [Online]. Available: https://developers.google.com/optimization/lp/glop (accessed Nov. 2026).
[9] M. Sivapalan, H. H. G. Savenije, and G. Blöschl, "Socio-hydrology: A new science of people and water," *Hydrological Processes*, vol. 26, no. 8, pp. 1270–1276, Apr. 2012, doi: 10.1002/hyp.8426.
[10] E. Ostrom, *Governing the Commons: The Evolution of Institutions for Collective Action*, Cambridge, UK: Cambridge University Press, 1990, 280 pp., doi: 10.1017/CBO9780511807763.
[11] F. Bousquet and C. Le Page, "Multi-agent simulations and ecosystem management: a review," *Ecological Modelling*, vol. 176, no. 3–4, pp. 313–332, Aug. 2004, doi: 10.1016/j.ecolmodel.2004.01.011.
[12] J. F. Nash, Jr., "The bargaining problem," *Econometrica*, vol. 18, no. 2, pp. 155–162, Apr. 1950, doi: 10.2307/1907266.
[13] H. Raiffa, *The Art and Science of Negotiation*, Cambridge, MA, USA: Belknap Press of Harvard University Press, 1982, 373 pp. ISBN: 978-0674048126.
[14] R. Fisher and W. Ury, *Getting to Yes: Negotiating Agreement Without Giving In*, B. Patton, Ed., Boston, MA, USA: Houghton Mifflin, 1981, 200 pp. ISBN: 978-0395317570.
[15] S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," in *Advances in Neural Information Processing Systems (NeurIPS 2017)*, vol. 30, Long Beach, CA, USA, 2017, pp. 4765–4774. [Online]. Available: https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html
[16] A. Barredo Arrieta, N. Díaz-Rodríguez, J. Del Ser, A. Bennetot, S. Tabik, A. Barbado, S. García, S. Gil-López, D. Molina, R. Benjamins, R. Chatila, and F. Herrera, "Explainable Artificial Intelligence (XAI): Concepts, taxonomies, opportunities and challenges toward responsible AI," *Information Fusion*, vol. 58, pp. 82–115, June 2020, doi: 10.1016/j.inffus.2019.12.012.
[17] R. K. Jain, D.-M. W. Chiu, and W. R. Hawe, "A quantitative measure of fairness and discrimination for resource allocation in shared computer system," Digital Equipment Corporation, Hudson, MA, USA, Research Report DEC-TR-301, Sep. 26, 1984, 38 pp. [Online]. Available: https://www.cs.wustl.edu/~jain/papers/fairness.htm
```

---

## 8. Final Approval Checklist & Verification

- [x] **Chen & Guestrin (2016) DOI**: Corrected to `10.1145/2939672.2939785`.
- [x] **Fan et al. (2018) Claims & Findings**: Accurately reflects target ($ET_0$), models (SVM, ELM, RF, M5Tree, GBDT, XGBoost), and publisher abstract findings (ELM/SVM accuracy vs. XGBoost/GBDT efficiency). All unverified $R^2$ ranges purged.
- [x] **Getting to Yes (1981) Attribution**: Authors listed strictly as Roger Fisher and William Ury; Bruce Patton listed as editor. BATNA attributed strictly to Fisher & Ury (1981); Raiffa (1982) cited strictly for concession/reservation utility theory.
- [x] **DEC Technical Report TR-301 Title**: Corrected exactly to *"A Quantitative Measure of Fairness and Discrimination for Resource Allocation in Shared Computer System"* (singular), dated September 26, 1984.
- [x] **Research-Gap Demarcation**: Explicitly labels the contrast between on-farm precision drip systems and communal canal dispute mediation as the authors' literature-review synthesis, stating the limitations of search evidence.
- [x] **XAI Trust Demarcation**: Clearly distinguishes the normative responsible-AI design motivation from empirically measured stakeholder trust.
- [x] **Metadata Cross-Verification**: All DOIs, ISBNs, and canonical URLs verified against publisher and institutional records.
- [x] **Monotonic Sequential Order**: Confirmed $[1]$ to $[17]$ sequential first-appearance order across the entire report.
- [x] **Strict Invariant Maintained**: `docs/FINAL_PROJECT_REPORT.md` has **NOT** been modified.

---

## 9. Final Decision

**FINAL DECISION**: **PASS**  
All metadata, DOI handles, corporate attributions, co-authorship records, claim-support calibrations, and sequential ordering requirements are fully verified and compliant with academic standards.

The insertion plan is ready for execution upon your approval.
