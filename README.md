# p38α MAPK Activity & Applicability Domain Predictor 🧬

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![RDKit](https://img.shields.io/badge/RDKit-Cheminformatics-green.svg)](https://www.rdkit.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-RandomForest-orange.svg)](https://scikit-learn.org/)

An automated Machine Learning QSAR platform to predict the biological activity of small molecule inhibitors against **p38α MAP Kinase (`MAPK14`)**, complete with real-time **Applicability Domain (AD)** verification.

---

## 🔬 Model & Scientific Methodology

- **Machine Learning Architecture:** Balanced Random Forest Classifier (500 estimators).
- **Descriptor Hybrid Space (42,106 Features):**
  1. **Morgan Fingerprints (2,048 bits):** Captures circular topological atom environments ($r=2$).
  2. **2D Pharmacophore Fingerprints (39,972 bits):** Evaluates distance-constrained chemical pharmacophores (`Gobbi_Pharm2D`).
  3. **Graph Molecular Embeddings (86 features):** Graph convolutions extracting mean & standard deviation of atom and bond features (`MolGraphConvFeaturizer`).
- **Applicability Domain (AD) Engine:**
  - Evaluated using $k$-Nearest Neighbors ($k=5$) against training space embeddings.
  - Empirical Cutoff: $h^* \le 19.965$ (**Inside AD** = high reliability interpolation; **Outside AD** = extrapolation).

---

## 🚀 Instant Deployment on Streamlit Community Cloud (100% Free)

You can deploy this repository to **Streamlit Community Cloud** in 3 simple steps:

1. **Push this Repository to your GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit for Streamlit Cloud"
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
   git push -u origin main
   ```
2. **Deploy on Streamlit**:
   - Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
   - Click **"New app"**.
   - Select your repository, branch (`main`), and set **Main file path** to `streamlit_app.py`.
   - Click **"Deploy!"**.
3. **Done!** Your QSAR prediction web application will be live globally with a shareable public URL.

---

## 💻 Running Locally

### 1. Clone the repository
```bash
git clone https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
cd <YOUR_REPO_NAME>
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Streamlit
```bash
streamlit run streamlit_app.py
```

---

## 📁 Repository Structure

```text
├── streamlit_app.py          # Main Streamlit web application
├── requirements.txt          # Python dependencies for Streamlit Cloud
├── packages.txt              # Debian system libraries for Streamlit Cloud
├── Hybrid_RF_Final_Model.pkl # Trained 500-tree Random Forest model
├── app/
│   ├── predictor.py          # Core feature engineering & inference engine
│   ├── ad_model.joblib       # Precomputed indexed AD model (5.6 MB)
│   ├── main.py               # Alternative FastAPI server
│   ├── run_server.py         # Standalone FastAPI runner
│   └── static/index.html     # Minimalist HTML Web UI
├── sample_input_smiles.xlsx  # Sample compound library for testing batch mode
├── sample_input_smiles.csv   # Sample CSV compound library
└── README.md                 # Project documentation
```

---

## 📄 License
This project is open-source under the MIT License.
