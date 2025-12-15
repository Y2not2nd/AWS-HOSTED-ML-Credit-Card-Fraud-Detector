import streamlit as st
import pandas as pd
import requests
import tempfile
import os
import time

# ===========================
# Session state initialisation
# ===========================
if "prediction_complete" not in st.session_state:
    st.session_state.prediction_complete = False

if "df_results" not in st.session_state:
    st.session_state.df_results = None

if "df_ui" not in st.session_state:
    st.session_state.df_ui = None

# ---------------------------
# Backend URL (unchanged)
# ---------------------------
def build_predict_url() -> str:
    base = os.getenv("BACKEND_BASE_URL", "").strip()
    if not base:
        base = "http://localhost:3000"
    base = base.rstrip("/")
    return f"{base}/predict"

PREDICT_URL = build_predict_url()

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="Credit Card Fraud Detection",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------
# (CSS + hero + sidebar unchanged)
# ---------------------------
# ⬆️ keep everything exactly as you pasted above
# ---------------------------

# ===========================
# MAIN COLUMN
# ===========================
main_col, sidebar_col = st.columns([2.5, 1], gap="large")

with main_col:
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            df_preview = pd.read_csv(tmp_path)

            run_prediction = st.button(
                "🚀 Run Fraud Prediction",
                type="primary",
                use_container_width=True
            )

            if run_prediction:
                with st.spinner("Running fraud detection model..."):
                    with open(tmp_path, "rb") as f:
                        response = requests.post(
                            PREDICT_URL,
                            data=f,
                            headers={
                                "Content-Type": "text/csv",
                                "Content-Length": str(os.path.getsize(tmp_path)),
                            },
                            timeout=600,
                        )

                if response.status_code != 200:
                    st.error("Model API error")
                    st.stop()

                result = response.json()
                results = result.get("results", [])

                df_results = df_preview.copy()
                df_results["fraud_probability"] = [r.get("fraud_probability") for r in results]
                df_results["risk_level"] = [r.get("risk_level") for r in results]
                df_results["decision"] = [r.get("decision") for r in results]

                risk_norm = (
                    df_results["risk_level"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                df_ui = df_results.copy()
                df_ui["risk_level_display"] = risk_norm.str.capitalize()

                # ✅ Persist results
                st.session_state.df_results = df_results
                st.session_state.df_ui = df_ui
                st.session_state.prediction_complete = True

        finally:
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)

# ===========================
# Render results from session state
# ===========================
if st.session_state.prediction_complete:
    df_results = st.session_state.df_results
    df_ui = st.session_state.df_ui

    st.markdown("## 📈 Prediction Results")

    available_levels = sorted(df_ui["risk_level_display"].unique())
    risk_filter = st.multiselect(
        "Filter by Risk Level",
        options=available_levels,
        default=available_levels
    )

    df_display = (
        df_ui[df_ui["risk_level_display"].isin(risk_filter)]
        if risk_filter else df_ui
    )

    st.dataframe(df_display.head(100), use_container_width=True)

    st.markdown("### ⬇️ Export Results")

    st.download_button(
        "📥 Download Full Results (CSV)",
        data=df_results.to_csv(index=False).encode("utf-8"),
        file_name="fraud_predictions.csv",
        mime="text/csv"
    )

    high_risk = df_results[
        df_results["risk_level"].astype(str).str.lower() == "high"
    ]

    if not high_risk.empty:
        st.download_button(
            "🔴 Download High Risk Only (CSV)",
            data=high_risk.to_csv(index=False).encode("utf-8"),
            file_name="fraud_predictions_high_risk.csv",
            mime="text/csv"
        )
