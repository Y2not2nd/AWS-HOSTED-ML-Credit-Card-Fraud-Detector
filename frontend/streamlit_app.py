import streamlit as st
import pandas as pd
import requests
import tempfile
import os
import time

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
# Custom CSS for professional styling
# ---------------------------
st.markdown("""
<style>
    /* Main container styling */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Hero section styling */
    .hero-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    
    .hero-title {
        color: white;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .hero-subtitle {
        color: rgba(255,255,255,0.95);
        font-size: 1.2rem;
        line-height: 1.6;
        max-width: 800px;
    }
    
    /* Card styling */
    .info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        margin-bottom: 1.5rem;
    }
    
    .info-card h3 {
        color: #667eea;
        margin-bottom: 1rem;
        font-size: 1.3rem;
    }
    
    .info-card ul {
        color: #4a5568;
        line-height: 1.8;
    }
    
    /* Success banner animation */
    @keyframes slideInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .success-banner {
        animation: slideInDown 0.5s ease-out;
    }
    
    /* Results section animation */
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    
    .results-section {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Metric card styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Upload section styling */
    .upload-section {
        background: #f8fafc;
        padding: 2rem;
        border-radius: 12px;
        border: 2px dashed #cbd5e0;
        margin-bottom: 1.5rem;
    }
    
    /* Button enhancements */
    .stButton > button {
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }
    
    /* Divider styling */
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border: none;
        margin: 2rem 0;
        border-radius: 2px;
    }
    
    /* Processing animation */
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.6;
        }
    }
    
    .processing {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Risk level badges */
    .risk-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    .risk-high {
        background-color: #fee;
        color: #c33;
    }
    
    .risk-medium {
        background-color: #fff4e5;
        color: #e67700;
    }
    
    .risk-low {
        background-color: #e6ffed;
        color: #22863a;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Hero header
# ---------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">💳 Credit Card Fraud Detection</div>
    <div class="hero-subtitle">
        Leverage advanced machine learning to identify fraudulent transactions in real-time. 
        Upload PCA-transformed transaction data and receive instant risk assessments with actionable insights.
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Main layout
# ---------------------------
main_col, sidebar_col = st.columns([2.5, 1], gap="large")

# ===========================
# SIDEBAR COLUMN (Info)
# ===========================
with sidebar_col:
    st.markdown("""
    <div class="info-card">
        <h3>🚀 Quick Start</h3>
        <ul>
            <li><strong>Step 1:</strong> Upload your CSV file</li>
            <li><strong>Step 2:</strong> Review data preview</li>
            <li><strong>Step 3:</strong> Run prediction</li>
            <li><strong>Step 4:</strong> Download results</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <h3>📋 Data Requirements</h3>
        <ul>
            <li>PCA-transformed credit card data</li>
            <li><strong>Required:</strong> Time, V1–V28, Amount</li>
            <li><strong>Optional:</strong> Class (ignored)</li>
            <li>All numeric, non-null values</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <h3>🎯 Risk Levels</h3>
        <ul>
            <li><span class="risk-badge risk-high">High</span> Probability ≥ 0.7</li>
            <li><span class="risk-badge risk-medium">Medium</span> Probability 0.3-0.7</li>
            <li><span class="risk-badge risk-low">Low</span> Probability < 0.3</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ===========================
# MAIN COLUMN
# ===========================
with main_col:
    # Upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📤 Upload Transaction Data")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="CSV must contain Time, V1–V28, and Amount columns",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            file_size_mb = os.path.getsize(tmp_path) / 1024 / 1024
            df_preview = pd.read_csv(tmp_path)

            # File upload success
            st.markdown('<div class="success-banner">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.success("✅ File uploaded successfully")
            with col2:
                st.info(f"📊 {len(df_preview):,} transactions")
            with col3:
                st.info(f"💾 {file_size_mb:.2f} MB")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            # Data preview
            with st.expander("🔍 Preview Uploaded Data", expanded=True):
                st.caption(f"Showing first 20 of {len(df_preview):,} transactions")
                st.dataframe(
                    df_preview.head(20), 
                    use_container_width=True,
                    height=400
                )
                
                # Quick stats
                st.markdown("##### Quick Statistics")
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                with stat_col1:
                    st.metric("Total Rows", f"{len(df_preview):,}")
                with stat_col2:
                    st.metric("Total Columns", len(df_preview.columns))
                with stat_col3:
                    st.metric("Avg Amount", f"${df_preview['Amount'].mean():.2f}" if 'Amount' in df_preview.columns else "N/A")
                with stat_col4:
                    st.metric("Max Amount", f"${df_preview['Amount'].max():.2f}" if 'Amount' in df_preview.columns else "N/A")

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            # Primary CTA
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
            with col_btn2:
                run_prediction = st.button(
                    "🚀 Run Fraud Prediction", 
                    type="primary",
                    use_container_width=True
                )

            if run_prediction:
                # Processing state with animation
                progress_container = st.container()
                with progress_container:
                    st.markdown('<div class="processing">', unsafe_allow_html=True)
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("⏳ Uploading data to model...")
                    progress_bar.progress(20)
                    time.sleep(0.3)
                    
                    status_text.text("🔄 Running fraud detection model...")
                    progress_bar.progress(40)
                    
                    # Actual API call (unchanged logic)
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
                    
                    progress_bar.progress(80)
                    status_text.text("📊 Processing results...")
                    time.sleep(0.3)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                    time.sleep(0.5)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Clear progress indicators
                    progress_container.empty()

                if response.status_code != 200:
                    st.error("🚨 Model API returned an error")
                    with st.expander("View Error Details"):
                        st.code(response.text)
                    st.stop()

                result = response.json()
                results = result.get("results", [])

                if not results:
                    st.warning("⚠️ No prediction results returned")
                    st.stop()

                df_results = df_preview.copy()
                df_results["fraud_probability"] = [r.get("fraud_probability") for r in results]
                df_results["risk_level"] = [r.get("risk_level") for r in results]
                df_results["decision"] = [r.get("decision") for r in results]

                # ===========================
                # Results section with animation
                # ===========================
                st.markdown('<div class="results-section">', unsafe_allow_html=True)
                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                
                st.markdown("## 📈 Prediction Results")
                
                # Summary metrics banner
                total = len(df_results)
                high = (df_results["risk_level"] == "High").sum()
                medium = (df_results["risk_level"] == "Medium").sum()
                low = (df_results["risk_level"] == "Low").sum()
                avg_prob = df_results["fraud_probability"].mean()
                
                st.markdown("### 📊 Summary Overview")
                metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
                
                with metric_col1:
                    st.metric(
                        "Total Transactions", 
                        f"{total:,}",
                        help="Total number of transactions analyzed"
                    )
                with metric_col2:
                    high_pct = (high / total * 100) if total > 0 else 0
                    st.metric(
                        "🔴 High Risk", 
                        f"{high:,}",
                        delta=f"{high_pct:.1f}%",
                        delta_color="inverse",
                        help="Transactions with fraud probability ≥ 0.7"
                    )
                with metric_col3:
                    medium_pct = (medium / total * 100) if total > 0 else 0
                    st.metric(
                        "🟡 Medium Risk", 
                        f"{medium:,}",
                        delta=f"{medium_pct:.1f}%",
                        delta_color="off",
                        help="Transactions with fraud probability 0.3-0.7"
                    )
                with metric_col4:
                    low_pct = (low / total * 100) if total > 0 else 0
                    st.metric(
                        "🟢 Low Risk", 
                        f"{low:,}",
                        delta=f"{low_pct:.1f}%",
                        delta_color="normal",
                        help="Transactions with fraud probability < 0.3"
                    )
                with metric_col5:
                    st.metric(
                        "Avg Probability", 
                        f"{avg_prob:.1%}",
                        help="Average fraud probability across all transactions"
                    )

                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

                # ===========================
                # Visualizations
                # ===========================
                viz_col1, viz_col2 = st.columns(2, gap="large")
                
                with viz_col1:
                    st.markdown("### 📊 Risk Distribution")
                    risk_counts = df_results["risk_level"].value_counts()
                    st.bar_chart(risk_counts, height=300)
                
                with viz_col2:
                    st.markdown("### 📈 Fraud Probability Distribution")
                    prob_bins = pd.cut(
                        df_results["fraud_probability"], 
                        bins=[0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0],
                        labels=["0-0.1", "0.1-0.3", "0.3-0.5", "0.5-0.7", "0.7-0.9", "0.9-1.0"]
                    ).value_counts().sort_index()
                    st.bar_chart(prob_bins, height=300)

                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

                # ===========================
                # Detailed results table
                # ===========================
                st.markdown("### 📋 Detailed Transaction Results")
                
                # Filter options
                filter_col1, filter_col2 = st.columns([1, 3])
                with filter_col1:
                    risk_filter = st.multiselect(
                        "Filter by Risk Level",
                        options=["High", "Medium", "Low"],
                        default=["High", "Medium", "Low"]
                    )
                
                # Apply filter
                if risk_filter:
                    df_display = df_results[df_results["risk_level"].isin(risk_filter)]
                else:
                    df_display = df_results
                
                st.caption(f"Showing {len(df_display):,} of {len(df_results):,} transactions")

                # Styled table
                def highlight_risk(row):
                    if row["risk_level"] == "High":
                        return ["background-color: #fdecea"] * len(row)
                    if row["risk_level"] == "Medium":
                        return ["background-color: #fff4e5"] * len(row)
                    return [""] * len(row)

                styled_df = df_display.head(100).style.apply(highlight_risk, axis=1)
                st.dataframe(
                    styled_df, 
                    use_container_width=True,
                    height=500
                )

                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

                # ===========================
                # Key insights
                # ===========================
                if high > 0:
                    st.warning(f"⚠️ **Action Required:** {high} high-risk transaction(s) detected and require immediate review.")
                else:
                    st.success("✅ **Good News:** No high-risk transactions detected.")
                
                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

                # ===========================
                # Download section
                # ===========================
                st.markdown("### ⬇️ Export Results")
                
                download_col1, download_col2 = st.columns([1, 2])
                with download_col1:
                    csv_out = df_results.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download Full Results (CSV)",
                        data=csv_out,
                        file_name="fraud_predictions.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with download_col2:
                    # High risk only export
                    if high > 0:
                        csv_high_risk = df_results[df_results["risk_level"] == "High"].to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="🔴 Download High Risk Only (CSV)",
                            data=csv_high_risk,
                            file_name="fraud_predictions_high_risk.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                
                st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error("🚨 Failed to process file")
            with st.expander("View Error Details"):
                st.code(str(e))

        finally:
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)

# ---------------------------
# Footer
# ---------------------------
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #718096; padding: 2rem 0;">
    <p style="font-size: 0.9rem; margin-bottom: 0.5rem;">
        <strong>Credit Card Fraud Detection System</strong>
    </p>
    <p style="font-size: 0.85rem;">
        Powered by Machine Learning • Production-Ready Risk Assessment • Real-Time Detection
    </p>
</div>
""", unsafe_allow_html=True)
