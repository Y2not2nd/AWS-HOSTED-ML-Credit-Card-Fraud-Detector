import streamlit as st
import pandas as pd
import requests
import tempfile
import os

def build_predict_url() -> str:
    """
    Frontend calls backend via a single URL.
    In hardened mode, this will be the internal NLB DNS name, plus /predict.
    Example:
      BACKEND_BASE_URL=http://internal-xxxx.eu-west-1.elb.amazonaws.com
    """
    base = os.getenv("BACKEND_BASE_URL", "").strip()

    if not base:
        # Safe default for local dev only
        base = "http://localhost:3000"

    # Ensure no trailing slash to avoid double slashes
    base = base.rstrip("/")

    # We lock contract to /predict
    return f"{base}/predict"


PREDICT_URL = build_predict_url()

st.set_page_config(
    page_title="Credit Card Fraud Detection",
    layout="wide",
)

st.title("💳 Credit Card Transaction Fraud Detection")

st.markdown(
    """
This application evaluates credit card transactions using a machine learning model
to estimate fraud risk.

Upload a CSV file containing PCA-transformed transaction data.
"""
)

with st.sidebar:
    st.subheader("Backend Configuration")
    st.write("Predict URL")
    st.code(PREDICT_URL)

uploaded_file = st.file_uploader(
    "Upload CSV file",
    type=["csv"],
)

if uploaded_file is not None:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        file_size_mb = os.path.getsize(tmp_path) / 1024 / 1024

        df_preview = pd.read_csv(tmp_path)

        st.subheader("🔍 Input Data Preview")
        st.write(df_preview.head(20))
        st.markdown(f"**File size:** {file_size_mb:.2f} MB")

        st.markdown("---")

        if st.button("🚀 Run Fraud Prediction"):
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
                st.error(f"Model API error: {response.status_code}")
                st.text(response.text)
                st.stop()

            result = response.json()
            results = result.get("results", [])

            if not results:
                st.warning("No prediction results returned.")
                st.stop()

            df_results = df_preview.copy()
            df_results["fraud_probability"] = [r.get("fraud_probability") for r in results]
            df_results["risk_level"] = [r.get("risk_level") for r in results]
            df_results["decision"] = [r.get("decision") for r in results]

            st.subheader("✅ Prediction Results")
            st.write(df_results.head(50))

            st.success("Prediction completed successfully.")

            csv_out = df_results.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Results as CSV",
                data=csv_out,
                file_name="fraud_predictions.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Failed to process file: {e}")

    finally:
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

st.markdown("---")

st.markdown(
    """
### ⚠️ Data Requirements

- PCA-transformed credit card transaction data only
- Required columns: Time, V1–V28, Amount
- Optional column: Class (ignored if present)
- All values must be numeric and non-null
"""
)
