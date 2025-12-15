import streamlit as st
import pandas as pd
import requests
import tempfile
import os

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
)

# ---------------------------
# Hero header
# ---------------------------
st.title("💳 Credit Card Transaction Fraud Detection")
st.markdown(
    """
Estimate fraud risk on credit card transactions using a machine learning model.
Upload PCA-transformed transaction data and receive actionable risk insights.
"""
)
st.markdown("---")

# ---------------------------
# Two-column layout
# ---------------------------
left_col, right_col = st.columns([2, 1])

# ===========================
# LEFT COLUMN
# ===========================
with left_col:

    with st.container():
        st.subheader("📤 Upload Transaction Data")

        uploaded_file = st.file_uploader(
            "Upload CSV file",
            type=["csv"],
            help="CSV must contain Time, V1–V28, and Amount columns",
        )

    if uploaded_file is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            file_size_mb = os.path.getsize(tmp_path) / 1024 / 1024
            df_preview = pd.read_csv(tmp_path)

            st.success("File uploaded successfully")

            with st.expander("🔍 Preview uploaded data", expanded=True):
                st.dataframe(df_preview.head(20), use_container_width=True)
                st.caption(f"File size: {file_size_mb:.2f} MB")

            st.markdown("---")

            # Primary CTA
            if st.button("🚀 Run Fraud Prediction", type="primary"):
                with st.spinner("Running model inference..."):
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
                    st.error("Model API returned an error")
                    st.code(response.text)
                    st.stop()

                result = response.json()
                results = result.get("results", [])

                if not results:
                    st.warning("No prediction results returned")
                    st.stop()

                df_results = df_preview.copy()
                df_results["fraud_probability"] = [r.get("fraud_probability") for r in results]
                df_results["risk_level"] = [r.get("risk_level") for r in results]
                df_results["decision"] = [r.get("decision") for r in results]

                # ===========================
                # Results summary banner
                # ===========================
                total = len(df_results)
                high = (df_results["risk_level"] == "High").sum()
                medium = (df_results["risk_level"] == "Medium").sum()
                low = (df_results["risk_level"] == "Low").sum()
                avg_prob = df_results["fraud_probability"].mean()

                st.markdown("---")
                st.subheader("✅ Prediction Summary")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Transactions", total)
                m2.metric("High Risk", high)
                m3.metric("Medium Risk", medium)
                m4.metric("Avg Fraud Probability", f"{avg_prob:.2f}")

                # ===========================
                # Risk distribution chart
                # ===========================
                st.subheader("📊 Risk Distribution")
                risk_counts = df_results["risk_level"].value_counts()
                st.bar_chart(risk_counts)

                # ===========================
                # Styled results table
                # ===========================
                st.subheader("📋 Prediction Results")

                def highlight_risk(row):
                    if row["risk_level"] == "High":
                        return ["background-color: #fdecea"] * len(row)
                    if row["risk_level"] == "Medium":
                        return ["background-color: #fff4e5"] * len(row)
                    return [""] * len(row)

                styled_df = df_results.head(50).style.apply(highlight_risk, axis=1)
                st.dataframe(styled_df, use_container_width=True)

                st.success("Prediction completed successfully")

                csv_out = df_results.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Results as CSV",
                    data=csv_out,
                    file_name="fraud_predictions.csv",
                    mime="text/csv",
                )

        except Exception as e:
            st.error("Failed to process file")
            st.code(str(e))

        finally:
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)

# ===========================
# RIGHT COLUMN
# ===========================
with right_col:
    with st.container():
        st.subheader("ℹ️ How it works")
        st.markdown(
            """
1. Upload PCA-transformed transaction data  
2. The model evaluates fraud probability  
3. Transactions are classified by risk level  
4. Results can be downloaded for analysis
"""
        )

    with st.container():
        st.subheader("⚠️ Data Requirements")
        st.markdown(
            """
- PCA-transformed credit card data only  
- Required columns: Time, V1–V28, Amount  
- Optional column: Class (ignored if present)  
- All values must be numeric and non-null
"""
        )

# ---------------------------
# Footer
# ---------------------------
st.markdown("---")
st.caption(
    "Credit Card Fraud Detection • Demo application for machine learning risk assessment"
)
