<div align="center">

# ⚡ EV Charging Analytics

### Understanding Charging Behavior · Evaluating Station Performance · Forecasting Demand

**IS403 · Business Analyst Capstone Project**

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Pandas-Data%20Analysis-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas"/>
  <img src="https://img.shields.io/badge/Jupyter-Notebooks-F37626?style=for-the-badge&logo=jupyter&logoColor=white" alt="Jupyter"/>
  <img src="https://img.shields.io/badge/Status-In%20Development-orange?style=for-the-badge" alt="Project status"/>
</p>

*An end-to-end analytics project using public EV charging-session data from Palo Alto, California.*

</div>

---

## 📌 Project Overview

Public EV charging infrastructure is a shared resource. A vehicle may remain connected after charging has finished, limiting port availability for other drivers. Understanding **charging time**, **idle time**, and **station utilization** can help operators evaluate operational performance and explore better charging policies.

This project analyzes public charging-session records from Palo Alto to study charging and occupancy behavior, examine differences around a historical pricing-policy change, benchmark station performance, and develop demand-forecasting models. The final goal is to translate analytical findings into practical, evidence-based operational recommendations.

> **Project focus:** data quality → behavioral analysis → policy evaluation → station benchmarking → demand forecasting → decision support.

## 🎯 Objectives

| Workstream | Objective | Planned methods / outputs |
|---|---|---|
| **NV1 · Data Quality** | Validate and prepare raw charging-session records for analysis. | Data-quality rules, anomaly flags, feature engineering, exploratory analysis |
| **NV2 · Behavior Analysis** | Identify distinct charging and occupancy behavior patterns. | K-Means / GMM clustering, behavioral profiles |
| **NV3 · Policy Evaluation** | Compare session behavior before and after the pricing-policy change and explore idle-fee scenarios. | Pre/post comparison, nonparametric tests, effect sizes, scenario analysis |
| **NV4 · Station Benchmarking** | Compare station or site performance using clearly defined operational indicators. | Utilization metrics, quadrant analysis, TOPSIS where appropriate |
| **NV5 · Demand Forecasting** | Forecast charging demand or occupied-port counts over time. | Time-based validation, baseline models, machine-learning models, MAE / RMSE |
| **Decision Support** | Turn results into actionable operational recommendations. | Evidence-based suggestions for idle-fee design, utilization, and capacity planning |

*Methods are planned workstreams; final model choices and conclusions will be documented alongside the completed experiments.*

## 🗂️ Repository Structure

```text
ev-charging-analytics/
├── data/
│   ├── raw/                 # Original source data (not committed)
│   ├── interim/             # Intermediate datasets
│   └── processed/           # Cleaned data and engineered features
├── notebooks/
│   ├── 01_NV1_data_cleaning.ipynb
│   ├── 02_NV2_occupancy_clustering.ipynb
│   ├── 03_NV3_policy_evaluation.ipynb
│   ├── 04_NV4_station_benchmarking.ipynb
│   └── 05_NV5_demand_forecasting.ipynb
├── src/                     # Shared pipeline and analysis utilities
├── outputs/
│   ├── tables/              # Result tables and KPI summaries
│   ├── figures/             # Generated charts
│   ├── metrics/             # Model and experiment metrics
│   └── models/              # Saved models, if needed
├── reports/
│   └── figures/             # Figures prepared for the final report
├── tests/                   # Data-integrity tests, if implemented
├── .gitignore
├── README.md
└── requirements.txt
```

> Generated files and exact filenames may evolve as the project develops. Keep raw data out of version control and document any required local data setup.

## 📊 Dataset

The project uses the **EV Charging Station Usage** dataset for Palo Alto, California, sourced from ChargePoint charging infrastructure.

| Attribute | Current project reference |
|---|---|
| Raw records | 259,415 sessions |
| Coverage | July 2011 – January 2021 |
| Locations / site clusters | 9 |
| Level 2 stations | 46 |
| Physical charging ports | 79 |
| Charging levels represented | Level 1 and Level 2 |

These figures describe the current project dataset reference and should be revalidated against the exact source file used for each experiment.

### Policy context

The project examines a historical pricing change dated **August 1, 2017**. The current project notes describe a post-change energy price of **$0.23/kWh** and an idle fee of **$2/hour after a 20-minute grace period**. These values will be verified against the source documentation before they are treated as policy facts in the final analysis.

A before-and-after comparison can identify associations, but it does not by itself establish that the policy caused observed changes. Results will be interpreted with attention to other time-related factors, including the unusual changes in 2020.

## 🔬 Analytical Workflow

### NV1 — Data Quality & Preparation
- Validate record structure, timestamps, duration relationships, energy values, and physical plausibility.
- Preserve data-quality flags so questionable records remain auditable.
- Engineer charging duration, connection duration, idle duration, idle ratio, and time-based features where supported by the source fields.
- Produce a documented clean dataset and exploratory summaries.

### NV2 — Charging and Occupancy Behavior
- Build interpretable features describing charging and post-charge connection behavior.
- Compare candidate clustering methods and document parameter selection and validation.
- Profile clusters using behavior summaries rather than relying on cluster labels alone.

### NV3 — Pricing Policy & Idle-Fee Scenarios
- Compare selected metrics before and after the historical policy change.
- Report effect sizes alongside statistical significance.
- Simulate alternative grace periods or fee scenarios as **what-if analyses**, clearly separating simulated outcomes from observed historical data.

### NV4 — Station / Site Performance
- Define the evaluation unit explicitly: site, station, or physical port.
- Compare utilization and other operational indicators using consistent definitions.
- Use quadrant analysis and, if justified, TOPSIS to support transparent performance comparisons.

### NV5 — Demand Forecasting
- Define the forecast target explicitly before model training—for example, occupied ports per 15-minute interval or energy demand.
- Establish simple baselines before evaluating machine-learning models.
- Use chronological train/validation/test splits and lagged features that do not use future information.
- Report appropriate metrics such as MAE and RMSE; use MAPE only when its handling of zero or near-zero actual values is justified.

For the complete workflow, see the [Vietnamese NV1–NV5 team run guide](docs/HUONG_DAN_CHAY_NV1_DEN_NV5.md). The [NV5 guide](docs/HUONG_DAN_CHAY_NV5.md) adds details on its mapping, split configuration, and output checks.

## 🧰 Tech Stack

- **Language:** Python
- **Analysis:** pandas, NumPy, scikit-learn
- **Environment:** Jupyter Notebook
- **Visualization:** Matplotlib / Seaborn and other project-selected plotting tools
- **Data storage:** CSV and Parquet, where appropriate
- **Testing:** pytest, if implemented

The definitive dependency list is maintained in `requirements.txt`. The stack above describes the intended workflow; packages should be considered project dependencies only when they are actually listed and used.

## 🚀 Getting Started

### 1. Clone the repository

```powershell
git clone https://github.com/mkn67/ev-charging-analytics---IS403.git
cd ev-charging-analytics---IS403
```

If the GitHub repository uses a different name or URL, replace the clone URL and directory accordingly.

### 2. Create and activate a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Add the source dataset

Place the source CSV in the expected local path under `data/raw/`. The raw dataset is intentionally excluded from Git. Check notebook paths and project configuration if your local filename or directory differs.

### 5. Run the notebooks

Start Jupyter:

```bash
jupyter lab
```

Run notebooks in sequence, beginning with `01_NV1_data_cleaning.ipynb`. Later notebooks should consume the documented outputs from NV1 so results remain consistent across workstreams.

If `src/run_pipeline.py` is implemented and configured, the NV1 pipeline may also be run with:

```bash
python -m src.run_pipeline
```

## ✅ Reproducibility & Data Integrity

- Keep raw data immutable; write cleaned and derived data to separate locations.
- Document exclusion rules and retain flags for records that need review.
- Fix random seeds for stochastic methods where applicable.
- Use chronological splits for forecasting.
- Record model parameters, evaluation metrics, and key outputs.
- Validate that transformations preserve expected row counts and aggregate totals where appropriate.
- Avoid committing raw data, virtual environments, credentials, or large generated artifacts.

## 📁 Expected Outputs

Depending on the final implementation, the repository may contain:

- Cleaned session-level data and engineered features.
- Data-quality audit tables and exploratory visualizations.
- Cluster profiles and station/site performance comparisons.
- Policy comparison and scenario-analysis results.
- Forecast evaluation tables and prediction plots.
- Figures and tables prepared for the final academic report.

## 👥 Project Information

- **Course:** IS403 — Business Analyst
- **Project:** EV Charging Analytics
- **Case study:** Public EV charging infrastructure in Palo Alto, California
- **Status:** In development

---

<div align="center">

**Built for reproducible analysis and evidence-based operational decision support.**

</div>
