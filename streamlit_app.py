import os
import io
import warnings
import streamlit as st
import pandas as pd
import numpy as np

# Suppress harmless scikit-learn warnings
warnings.filterwarnings("ignore")

# Page configuration
st.set_page_config(
    page_title="p38α MAPK QSAR Predictor",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern scientific look
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .metric-box {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .status-active {
        color: #10b981;
        font-weight: 800;
        font-size: 1.6rem;
    }
    .status-inactive {
        color: #94a3b8;
        font-weight: 800;
        font-size: 1.6rem;
    }
    .ad-inside {
        background-color: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .ad-outside {
        background-color: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Import predictor
from app.predictor import get_predictor

@st.cache_resource(show_spinner="Loading Hybrid Random Forest Model & Descriptors...")
def load_cached_predictor():
    return get_predictor()

try:
    predictor = load_cached_predictor()
except Exception as e:
    st.error(f"Error loading model: {e}")
    st.stop()

# -------------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------------
with st.sidebar:
    st.title("🧬 Model Specifications")
    st.markdown("""
    **Target Enzyme:**
    p38α Mitogen-Activated Protein Kinase (`MAPK14`)

    **Machine Learning Architecture:**
    - **Classifier:** Balanced Random Forest (500 Trees)
    - **Total Features:** 42,106 Descriptors
      - *Morgan Fingerprints:* 2,048 bits
      - *2D Pharmacophore:* 39,972 bits
      - *Graph Embeddings:* 86 continuous descriptors
    
    **Applicability Domain (AD):**
    - **Method:** $k$-Nearest Neighbors ($k=5$)
    - **Empirical Cutoff:** $\le 19.965$
    """)
    st.divider()
    st.markdown("### 🧪 Quick Samples")
    sample_choice = st.selectbox(
        "Choose sample molecule:",
        ["-- Select Sample --", "Active Hit (P38BS0102685)", "Inactive Molecule (P38BS0100001)", "Outside AD (P38BS0103030)"]
    )
    st.caption("Developed for high-throughput virtual screening & QSAR validation.")

# -------------------------------------------------------------------
# HEADER
# -------------------------------------------------------------------
st.markdown('<div class="main-title">p38α MAPK Activity & AD Predictor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Machine Learning Classification with 42,106 Hybrid Descriptors & Applicability Domain Verification</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------
# TABS
# -------------------------------------------------------------------
tab1, tab2 = st.tabs(["🔬 Single Molecule Screening", "📁 Batch Library Screening (.xlsx / .csv)"])

# SAMPLE DICTIONARY
SAMPLES = {
    "Active Hit (P38BS0102685)": {
        "code": "P38BS0102685",
        "smiles": "OCCSc1nc(c([nH]1)c1ccc(cc1)F)c1ccnc(c1)NC(C)C"
    },
    "Inactive Molecule (P38BS0100001)": {
        "code": "P38BS0100001",
        "smiles": "Nc1nc2c([nH]1)cccc2"
    },
    "Outside AD (P38BS0103030)": {
        "code": "P38BS0103030",
        "smiles": "CC(Oc1nccc(n1)c1c(ncn1C1CCNCC1)c1ccc(cc1)F)C"
    }
}

# ===================================================================
# TAB 1: SINGLE PREDICTION
# ===================================================================
with tab1:
    default_code = "COMP-001"
    default_smiles = ""

    if sample_choice in SAMPLES:
        default_code = SAMPLES[sample_choice]["code"]
        default_smiles = SAMPLES[sample_choice]["smiles"]

    col_in1, col_in2 = st.columns([1, 3])
    with col_in1:
        input_code = st.text_input("Compound Identifier", value=default_code)
    with col_in2:
        input_smiles = st.text_input("Canonical or Isomeric SMILES", value=default_smiles, placeholder="e.g. OCCSc1nc(c([nH]1)c1ccc(cc1)F)c1ccnc(c1)NC(C)C")

    predict_clicked = st.button("🚀 Predict Activity & Applicability Domain", type="primary", use_container_width=True)

    if predict_clicked or (sample_choice in SAMPLES and default_smiles):
        if not input_smiles.strip():
            st.warning("Please enter a valid SMILES string.")
        else:
            with st.spinner("Calculating 42,106 descriptors & performing ensemble prediction..."):
                res = predictor.predict_single(smiles=input_smiles.strip(), code=input_code.strip() or "COMP-001")

            if not res.get("success", False):
                st.error(f"❌ {res.get('error', 'Prediction error')}")
            else:
                st.success("✅ Prediction Complete")
                col_res1, col_res2 = st.columns([1, 1])

                with col_res1:
                    st.subheader("2D Chemical Structure")
                    if res.get("svg"):
                        st.image(res["svg"], use_container_width=True)
                    else:
                        st.info("Structure depiction not available.")

                    # Properties table
                    props = res.get("properties", {})
                    if props:
                        st.markdown("##### Physicochemical Properties")
                        prop_df = pd.DataFrame([
                            {"Property": "Formula", "Value": props.get("formula", "N/A")},
                            {"Property": "Molecular Weight", "Value": f"{props.get('mol_wt', 'N/A')} g/mol"},
                            {"Property": "LogP (Lipophilicity)", "Value": props.get("log_p", "N/A")},
                            {"Property": "TPSA", "Value": f"{props.get('tpsa', 'N/A')} Å²"},
                            {"Property": "H-Bond Donors / Acceptors", "Value": f"{props.get('hbd', 0)} / {props.get('hba', 0)}"},
                            {"Property": "Rotatable Bonds", "Value": props.get("rotatable_bonds", "N/A")}
                        ])
                        st.dataframe(prop_df, hide_index=True, use_container_width=True)

                with col_res2:
                    st.subheader("Classification & Domain Verification")
                    
                    # Metrics cards
                    mcol1, mcol2 = st.columns(2)
                    with mcol1:
                        if res["activity"] == "Active":
                            st.markdown(f'<div class="metric-box"><span style="color:#94a3b8;font-size:0.8rem;">PREDICTED ACTIVITY</span><br><span class="status-active">ACTIVE</span></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="metric-box"><span style="color:#94a3b8;font-size:0.8rem;">PREDICTED ACTIVITY</span><br><span class="status-inactive">INACTIVE</span></div>', unsafe_allow_html=True)

                    with mcol2:
                        st.markdown(f'<div class="metric-box"><span style="color:#94a3b8;font-size:0.8rem;">CONFIDENCE LEVEL</span><br><span style="font-size:1.5rem;font-weight:700;">{res["confidence"]}</span></div>', unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"**Active Class Probability:** `{res['probability_percent']}%` ({res['probability']:.4f})")
                    st.progress(res["probability"])

                    st.divider()
                    st.markdown("##### Applicability Domain (AD) Assessment")
                    ad_dist = res.get("ad_distance")
                    ad_thresh = res.get("ad_threshold", 19.965)
                    
                    ad_col1, ad_col2 = st.columns(2)
                    with ad_col1:
                        if res["ad_status"] == "Inside AD":
                            st.markdown(f'<span class="ad-inside">✓ INSIDE AD</span>', unsafe_allow_html=True)
                            st.caption("Reliable interpolation within chemical training space.")
                        else:
                            st.markdown(f'<span class="ad-outside">⚠ OUTSIDE AD</span>', unsafe_allow_html=True)
                            st.caption("Model extrapolation; lower certainty.")

                    with ad_col2:
                        if ad_dist is not None:
                            st.metric(label="k-NN Distance to Training Set", value=f"{ad_dist:.4f}", delta=f"Threshold: {ad_thresh:.4f}")
                        else:
                            st.metric(label="k-NN Distance", value="N/A")


# ===================================================================
# TAB 2: BATCH SCREENING
# ===================================================================
with tab2:
    st.subheader("Upload Screening Compound Library")
    st.markdown("Upload an Excel (`.xlsx`) or CSV (`.csv`) spreadsheet containing compound codes and SMILES.")
    
    uploaded_file = st.file_uploader("Choose a file", type=["xlsx", "xls", "csv"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            
            st.write(f"📁 Loaded **{len(df_upload)}** rows from `{uploaded_file.name}`")
            st.dataframe(df_upload.head(3), use_container_width=True)

            smiles_cols = [c for c in df_upload.columns if "smiles" in str(c).lower()]
            code_cols = [c for c in df_upload.columns if any(k in str(c).lower() for k in ["code", "id", "name", "compound"])]

            if not smiles_cols:
                st.error("Uploaded file must contain a column containing SMILES (e.g. 'SMILES' or 'Ligand SMILES').")
            else:
                smiles_col = smiles_cols[0]
                code_col = code_cols[0] if code_cols else None

                if st.button("🚀 Run Batch Prediction", type="primary"):
                    items = []
                    for idx, row in df_upload.iterrows():
                        c_val = str(row[code_col]) if code_col else f"MOL_{idx+1}"
                        s_val = str(row[smiles_col]) if pd.notna(row[smiles_col]) else ""
                        items.append({"CODE": c_val, "SMILES": s_val})

                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.text("Featurizing compounds & computing 42,106 descriptors...")
                    
                    batch_res = predictor.predict_batch(items)
                    progress_bar.progress(100)
                    status_text.text("Batch processing complete!")

                    # Summary cards
                    s = batch_res["summary"]
                    scol1, scol2, scol3, scol4, scol5 = st.columns(5)
                    scol1.metric("Total Molecules", s["total"])
                    scol2.metric("Valid Structures", s["valid"])
                    scol3.metric("Active Hits", s["active_count"], delta=f"{s['active_percentage']}% Hit Rate")
                    scol4.metric("Inactive Hits", s["inactive_count"])
                    scol5.metric("Inside AD", s["inside_ad_count"], delta=f"{s['inside_ad_percentage']}% Inside")

                    # Display results table
                    res_df = pd.DataFrame(batch_res["results"])
                    if not res_df.empty:
                        st.subheader("Prediction Results")
                        st.dataframe(res_df, use_container_width=True)

                        # Export Excel button
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine="openpyxl") as writer:
                            res_df.to_excel(writer, index=False, sheet_name="Predictions")
                        output.seek(0)

                        st.download_button(
                            label="📥 Download Results as Excel (.xlsx)",
                            data=output,
                            file_name="p38a_Predictions_AD_Result.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                    
                    if batch_res.get("invalid"):
                        st.warning(f"Found {len(batch_res['invalid'])} invalid SMILES entries:")
                        st.dataframe(pd.DataFrame(batch_res["invalid"]))

        except Exception as e:
            st.error(f"Error reading file: {e}")
