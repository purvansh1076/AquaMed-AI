# AQUAMEDI AI — AGRICULTURAL SCIENCE & HYDROLOGICAL REPORT
**Document Reference**: `AQUA-AGRI-SCI-2026-V1`  
**Focus Region**: Ahmednagar District, Maharashtra, India (Semi-Arid Deccan Plateau)  
**Lead Evaluators**: Agricultural Scientist, Agronomist, and Hydrologist  

---

## 1. Agro-Ecological Context of Central Maharashtra

Ahmednagar is located in the rain-shadow zone of the Western Ghats (Godavari and Krishna sub-basins). Mean annual rainfall is $500\text{--}650\text{ mm}$, highly erratic and concentrated in the monsoon months (June–September). 
- **Major Crops**: Sugarcane (*Saccharum officinarum*), Bt Cotton (*Gossypium hirsutum*), Soybean (*Glycine max*), Rabi Wheat (*Triticum aestivum*), and Gram/Chickpea (*Cicer arietinum*).
- **Major Soils**: Deep Black Cotton Soils (Vertisols, high WHC $200\text{ mm/m}$), Medium Black Soils, and Coarse Shallow Soils (Entisols, low WHC $80\text{ mm/m}$).
- **Hydrological Conflict Core**: Sugarcane occupies only ~12% of the cultivated area but consumes over 65% of canal irrigation releases, severely starving downstream pulse and oilseed farmers during the critical Rabi season.

---

## 2. Mathematical FAO-56 Penman-Monteith Formulation

Reference evapotranspiration $ET_0$ represents the evapotranspiration rate from an extensive surface of 0.12 m tall green grass cover of uniform height, actively growing, completely shading the ground, and with adequate water supply.

$$\text{ET}_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$

### Parameter Implementation Verification in Code:
1. **Saturation Vapor Pressure ($e_s$)**:
   $$e_s = \frac{e^0(T_{max}) + e^0(T_{min})}{2} = \frac{0.6108 \exp\left(\frac{17.27 T_{max}}{T_{max} + 237.3}\right) + 0.6108 \exp\left(\frac{17.27 T_{min}}{T_{min} + 237.3}\right)}{2}$$
2. **Actual Vapor Pressure ($e_a$)**:
   $$e_a = e_s \times \frac{RH_{mean}}{100}$$
3. **Slope of Saturation Vapor Pressure Curve ($\Delta$)**:
   $$\Delta = \frac{4098 [0.6108 \exp(\frac{17.27 T}{T + 237.3})]}{(T + 237.3)^2}$$
4. **Psychrometric Constant ($\gamma$)**:
   $$\gamma = 0.665 \times 10^{-3} P = 0.665 \times 10^{-3} \left[ 101.3 \left(\frac{293 - 0.0065 z}{293}\right)^{5.26} \right]$$
   For Ahmednagar elevation $z = 540\text{ m}$, $P \approx 95.1\text{ kPa}$ and $\gamma \approx 0.0632\text{ kPa/}^\circ\text{C}$.

---

## 3. Crop Evapotranspiration & Stage-Specific Coefficients ($K_c$)

Crop water demand under standard conditions is:
$$ET_c = K_c \times ET_0$$

| Crop | Initial Stage ($K_{c, ini}$) | Mid-Season ($K_{c, mid}$) | Late Season ($K_{c, end}$) | Total Duration | Critical Growth Stage |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Sugarcane** | 0.40 | 1.25 | 0.75 | 360 days | Grand growth & Formative |
| **Cotton** | 0.35 | 1.15 | 0.65 | 165 days | Flowering & Boll development |
| **Soybean** | 0.30 | 1.10 | 0.50 | 105 days | Pod initiation & filling |
| **Wheat** | 0.30 | 1.15 | 0.40 | 120 days | Crown root initiation & Flowering |
| **Gram** | 0.30 | 1.00 | 0.35 | 110 days | Pre-flowering & Pod development |

---

## 4. Effective Rainfall & Net Irrigation Requirement

Effective rainfall ($P_{eff}$) is calculated using the empirical USDA Soil Conservation Service method:
$$P_{eff} = \begin{cases} 
\frac{P_{total} (125 - 0.2 P_{total})}{125} & \text{for } P_{total} \le 250\text{ mm} \\
125 + 0.1 P_{total} & \text{for } P_{total} > 250\text{ mm}
\end{cases}$$

Net Irrigation Requirement ($I_n$):
$$I_n = \max(0.0, ET_c - P_{eff})$$

Volumetric crop water requirement for farm area $A$ (ha):
$$V_{irr} = I_n (\text{mm}) \times 10 \times A (\text{ha}) \quad [\text{m}^3]$$
This matches the verified target calculation in [synthetic_generator.py](file:///c:/Users/lenovo/OneDrive/Attachments/Desktop/Technical%20Seminar/aquamedi-ai/backend/app/data/synthetic_generator.py).
