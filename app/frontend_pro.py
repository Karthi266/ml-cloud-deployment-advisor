import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import streamlit as st
import pandas as pd
import plotly.express as px
import joblib
import os
import inspect
import io
from contextlib import redirect_stdout, redirect_stderr

from streamlit_option_menu import option_menu

from core.model_analyzer import analyze_model
from core.workload_analyzer import analyze_workload
from core.deployment_decision import decide_deployment
from core.cloud_provider_advisor import compare_cloud_providers
from pricing.cost_calculator import run_cost_analysis
from core.break_even_engine import run_break_even_analysis
from core.benchmark_engine import run_benchmark


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart Cloud Deployment Advisor",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 10% 10%,
                rgba(50, 100, 180, 0.16),
                transparent 35%
            ),
            radial-gradient(
                circle at 90% 10%,
                rgba(120, 60, 180, 0.13),
                transparent 35%
            ),
            #07111f;
        color: #f4f7fb;
    }

    section[data-testid="stSidebar"] {
        background: #081321;
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #9aa9bd;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .hero-box {
        background: linear-gradient(
            135deg,
            rgba(24, 61, 104, 0.92),
            rgba(35, 28, 75, 0.92)
        );
        border: 1px solid rgba(120,160,220,0.20);
        border-radius: 18px;
        padding: 28px;
        margin-bottom: 22px;
    }

    .hero-title {
        font-size: 30px;
        font-weight: 800;
    }

    .hero-text {
        color: #b6c3d4;
        font-size: 15px;
        margin-top: 8px;
    }

    .metric-box {
        background: rgba(18,31,50,0.88);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 18px;
        min-height: 120px;
    }

    .metric-title {
        color: #94a6bd;
        font-size: 13px;
    }

    .metric-value {
        font-size: 27px;
        font-weight: 800;
        margin-top: 8px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 750;
        margin-top: 10px;
        margin-bottom: 16px;
    }

    .recommendation-box {
        background: linear-gradient(
            135deg,
            rgba(16, 86, 66, 0.92),
            rgba(15, 57, 83, 0.92)
        );
        border: 1px solid rgba(90,220,170,0.25);
        border-radius: 18px;
        padding: 24px;
        margin: 18px 0;
    }

    .warning-box {
        background: rgba(120,75,20,0.25);
        border: 1px solid rgba(240,180,70,0.25);
        border-radius: 14px;
        padding: 16px;
    }

    .small-muted {
        color: #92a1b5;
        font-size: 13px;
    }

    div[data-testid="stMetric"] {
        background: rgba(18,31,50,0.75);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 14px;
        border-radius: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "model_path" not in st.session_state:
    st.session_state.model_path = "spam_classifier.joblib"

if "model_result" not in st.session_state:
    st.session_state.model_result = None

if "workload" not in st.session_state:
    st.session_state.workload = {
        "traffic_pattern": "steady",
        "request_volume": 100000,
        "latency": "standard",
        "request_duration": 0.2,
        "concurrency": 10,
        "memory_gb": 1.0
    }

if "deployment_result" not in st.session_state:
    st.session_state.deployment_result = None

if "cost_result" not in st.session_state:
    st.session_state.cost_result = None

if "break_even_result" not in st.session_state:
    st.session_state.break_even_result = None

if "benchmark_result" not in st.session_state:
    st.session_state.benchmark_result = None

if "provider_result" not in st.session_state:
    st.session_state.provider_result = None

if "scenario_results" not in st.session_state:
    st.session_state.scenario_results = []


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def money(value, decimals=2):
    try:
        return f"${float(value):,.{decimals}f}"
    except Exception:
        return "$0.00"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def normalize_provider_name(name):
    if not name:
        return ""

    value = str(name).strip().lower()

    mapping = {
        "aws": "AWS Lambda",
        "aws lambda": "AWS Lambda",
        "lambda": "AWS Lambda",

        "azure": "Azure Functions",
        "azure functions": "Azure Functions",
        "azure function": "Azure Functions",

        "google": "Google Cloud Run",
        "google cloud run": "Google Cloud Run",
        "cloud run": "Google Cloud Run",

        "google compute engine": "Google Compute Engine",
        "gce": "Google Compute Engine",

        "azure vm": "Azure VM",
        "vm": "Virtual Machine"
    }

    return mapping.get(value, str(name))


# ============================================================
# IMPORTANT WORKLOAD NORMALIZATION
# ============================================================

def normalize_workload(workload):

    if workload is None:
        workload = {}

    if not isinstance(workload, dict):
        workload = {}

    request_volume = workload.get(
        "request_volume",
        workload.get(
            "monthly_requests",
            workload.get(
                "requests_per_month",
                100000
            )
        )
    )

    concurrency = workload.get(
        "concurrency",
        workload.get(
            "expected_concurrency",
            workload.get(
                "concurrent_requests",
                10
            )
        )
    )

    normalized = {
        "traffic_pattern": str(
            workload.get(
                "traffic_pattern",
                "steady"
            )
        ).strip().lower(),

        "request_volume": safe_int(
            request_volume,
            100000
        ),

        "latency": str(
            workload.get(
                "latency",
                "standard"
            )
        ).strip().lower(),

        "request_duration": safe_float(
            workload.get(
                "request_duration",
                0.2
            ),
            0.2
        ),

        "concurrency": safe_int(
            concurrency,
            10
        ),

        "memory_gb": safe_float(
            workload.get(
                "memory_gb",
                1.0
            ),
            1.0
        )
    }

    if normalized["request_volume"] <= 0:
        normalized["request_volume"] = 100000

    if normalized["concurrency"] <= 0:
        normalized["concurrency"] = 1

    if normalized["request_duration"] <= 0:
        normalized["request_duration"] = 0.1

    if normalized["memory_gb"] <= 0:
        normalized["memory_gb"] = 1.0

    return normalized


# ============================================================
# UI WORKLOAD FORMAT
# ============================================================

def workload_for_ui(workload):

    workload = normalize_workload(workload)

    return {
        "traffic_pattern": workload["traffic_pattern"],
        "monthly_requests": workload["request_volume"],
        "latency": workload["latency"],
        "request_duration": workload["request_duration"],
        "expected_concurrency": workload["concurrency"],
        "memory_gb": workload["memory_gb"]
    }


# ============================================================
# RUN WORKLOAD ANALYSIS
# ============================================================

def run_workload_analysis_safely(workload):

    normalized = normalize_workload(workload)

    return normalized


# ============================================================
# DEPLOYMENT DECISION COMPATIBILITY
# ============================================================

def build_deployment_decision(workload_data):

    workload = normalize_workload(workload_data)

    try:

        result = None

        try:
            result = decide_deployment(workload)

        except TypeError:

            try:
                result = decide_deployment(
                    workload_data=workload
                )

            except TypeError:

                result = decide_deployment()

        if isinstance(result, dict):
            return result

    except Exception as error:

        deployment_error = str(error)

    else:

        deployment_error = None

    # ========================================================
    # FALLBACK DECISION
    # ========================================================

    compatibility = compare_cloud_providers(
        workload
    )

    cost_result = run_cost_analysis(
        workload
    )

    compatible = compatibility.get(
        "compatible_providers",
        []
    )

    serverless = cost_result.get(
        "serverless",
        {}
    )

    vm = cost_result.get(
        "vm",
        {}
    )

    serverless_candidates = {}

    for provider, details in serverless.items():

        provider_name = normalize_provider_name(
            provider
        )

        if provider_name not in compatible:
            continue

        if isinstance(details, dict):

            cost = details.get(
                "monthly_cost",
                details.get(
                    "estimated_monthly_cost",
                    details.get(
                        "cost",
                        0
                    )
                )
            )

        else:

            cost = details

        cost = safe_float(cost)

        if cost > 0:

            serverless_candidates[
                provider_name
            ] = cost

    vm_candidates = {}

    for provider, details in vm.items():

        provider_name = normalize_provider_name(
            provider
        )

        if isinstance(details, dict):

            cost = details.get(
                "monthly_cost",
                details.get(
                    "estimated_monthly_cost",
                    details.get(
                        "cost",
                        0
                    )
                )
            )

        else:

            cost = details

        cost = safe_float(cost)

        if cost > 0:

            vm_candidates[
                provider_name
            ] = cost

    if serverless_candidates:

        selected_provider = min(
            serverless_candidates,
            key=serverless_candidates.get
        )

        selected_cost = serverless_candidates[
            selected_provider
        ]

    else:

        selected_provider = None
        selected_cost = None

    if vm_candidates:

        vm_provider = min(
            vm_candidates,
            key=vm_candidates.get
        )

        vm_cost = vm_candidates[
            vm_provider
        ]

    else:

        vm_provider = None
        vm_cost = None

    if (
        selected_cost is not None
        and vm_cost is not None
    ):

        if selected_cost < vm_cost:

            strategy = "Managed / Serverless"

            reason = (
                "The lowest-cost compatible serverless "
                "option is cheaper than the VM baseline "
                "for this workload."
            )

        else:

            strategy = "Self-Managed VM"

            selected_provider = vm_provider
            selected_cost = vm_cost

            reason = (
                "The VM baseline is economically competitive "
                "with the evaluated serverless options "
                "for this workload."
            )

    elif selected_cost is not None:

        strategy = "Managed / Serverless"

        reason = (
            "A compatible serverless provider has valid "
            "pricing data, while VM pricing is unavailable."
        )

    elif vm_cost is not None:

        strategy = "Self-Managed VM"

        selected_provider = vm_provider
        selected_cost = vm_cost

        reason = (
            "VM pricing is available while no compatible "
            "serverless provider has valid pricing data."
        )

    else:

        strategy = "Unable to determine"

        reason = (
            "Insufficient pricing data was available "
            "to determine a deployment strategy."
        )

    return {
        "strategy": strategy,
        "provider": selected_provider,
        "estimated_monthly_cost": selected_cost,
        "reason": reason,
        "compatibility": compatibility,
        "cost": cost_result,
        "error": deployment_error
    }


# ============================================================
# RUN COST ANALYSIS
# ============================================================

def get_cost_analysis(workload):

    normalized = normalize_workload(
        workload
    )

    try:

        return run_cost_analysis(
            normalized
        )

    except TypeError:

        return run_cost_analysis(
            workload=normalized
        )


# ============================================================
# RUN BREAK EVEN
# ============================================================

def get_break_even_analysis(workload):

    normalized = normalize_workload(
        workload
    )

    try:

        return run_break_even_analysis(
            normalized
        )

    except TypeError:

        return run_break_even_analysis(
            workload=normalized
        )


# ============================================================
# RUN BENCHMARK
# ============================================================

def get_benchmark(model_path):

    try:

        model = joblib.load(
            model_path
        )

        sample_input = [
            "Congratulations! You have won a free prize. "
            "Click this link now to claim your reward."
        ]

        try:

            return run_benchmark(
                model,
                sample_input
            )

        except TypeError:

            return run_benchmark(
                model
            )

    except Exception as error:

        st.error(
            f"Benchmark failed: {error}"
        )

        return None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            font-size:24px;
            font-weight:800;
            margin-bottom:8px;
        ">
        ☁️ Smart Cloud
        </div>

        <div style="
            color:#8fa1b8;
            font-size:13px;
            margin-bottom:20px;
        ">
        ML Deployment Decision Support
        </div>
        """,
        unsafe_allow_html=True
    )

    selected_page = option_menu(
        menu_title=None,
        options=[
            "Dashboard",
            "Model Analysis",
            "Workload Configuration",
            "Workload Analysis",
            "Deployment Decision",
            "Cloud Market & Cost",
            "Provider Comparison",
            "Predictive Scaling",
            "ML Benchmark",
            "Scenario Simulator",
            "Final Recommendation"
        ],
        icons=[
            "speedometer2",
            "cpu",
            "sliders",
            "activity",
            "diagram-3",
            "cloud",
            "bar-chart",
            "graph-up-arrow",
            "lightning",
            "bezier2",
            "check-circle"
        ],
        default_index=0,
        styles={
            "container": {
                "padding": "0!important",
                "background-color": "transparent"
            },
            "icon": {
                "color": "#8ea3bc",
                "font-size": "15px"
            },
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "3px 0",
                "padding": "11px 12px",
                "border-radius": "10px",
                "color": "#b4c0d0"
            },
            "nav-link-selected": {
                "background-color": "#19385e",
                "color": "#ffffff"
            }
        }
    )

    st.divider()

    uploaded_model = st.file_uploader(
        "Upload ML Model",
        type=["joblib", "pkl"]
    )

    if uploaded_model is not None:

        model_dir = "uploaded_models"

        os.makedirs(
            model_dir,
            exist_ok=True
        )

        model_path = os.path.join(
            model_dir,
            uploaded_model.name
        )

        with open(
            model_path,
            "wb"
        ) as file:

            file.write(
                uploaded_model.getbuffer()
            )

        st.session_state.model_path = model_path

        st.success(
            f"Loaded: {uploaded_model.name}"
        )

    st.caption(
        "Supported: Python ML models saved as .joblib or .pkl"
    )


# ============================================================
# PAGE HEADER
# ============================================================

st.markdown(
    '<div class="main-title">Smart Cloud Deployment Advisor</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtitle">
    Analyze an ML model, evaluate workload requirements,
    compare deployment strategies and estimate cloud cost.
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DASHBOARD
# ============================================================

if selected_page == "Dashboard":

    st.markdown(
        """
        <div class="hero-box">
            <div class="hero-title">
                ML → Cloud Deployment Intelligence
            </div>
            <div class="hero-text">
                Evaluate your machine-learning workload and determine
                whether a self-managed VM or managed/serverless
                deployment is more appropriate.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    workload = normalize_workload(
        st.session_state.workload
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "ML Model",
            os.path.basename(
                st.session_state.model_path
            )
        )

    with c2:
        st.metric(
            "Monthly Requests",
            f"{workload['request_volume']:,}"
        )

    with c3:
        st.metric(
            "Concurrency",
            workload["concurrency"]
        )

    with c4:
        st.metric(
            "Memory",
            f"{workload['memory_gb']:.1f} GB"
        )

    st.markdown(
        '<div class="section-title">Decision Pipeline</div>',
        unsafe_allow_html=True
    )

    pipeline = pd.DataFrame(
        {
            "Stage": [
                "Model Analysis",
                "Workload Analysis",
                "Compatibility",
                "Cost Analysis",
                "Break-even",
                "Recommendation"
            ],
            "Status": [
                "Ready",
                "Ready",
                "Ready",
                "Ready",
                "Ready",
                "Ready"
            ]
        }
    )

    st.dataframe(
        pipeline,
        width="stretch",
        hide_index=True
    )

    st.info(
        "Use the sidebar to move through the complete deployment analysis."
    )


# ============================================================
# MODEL ANALYSIS
# ============================================================

elif selected_page == "Model Analysis":

    st.markdown(
        '<div class="section-title">Model Analysis</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Current model:"
    )

    st.code(
        st.session_state.model_path
    )

    if st.button(
        "Analyze ML Model",
        type="primary"
    ):

        try:

            result = analyze_model(
                st.session_state.model_path
            )

            st.session_state.model_result = result

        except TypeError:

            result = analyze_model()

            st.session_state.model_result = result

        except Exception as error:

            st.error(
                f"Model analysis failed: {error}"
            )

    result = st.session_state.model_result

    if result:

        st.success(
            "Model analysis completed."
        )

        if isinstance(result, dict):

            rows = []

            for key, value in result.items():

                if isinstance(
                    value,
                    (dict, list, tuple)
                ):

                    value = str(value)

                rows.append(
                    {
                        "Property": key,
                        "Value": value
                    }
                )

            st.dataframe(
                pd.DataFrame(rows),
                width="stretch",
                hide_index=True
            )

        else:

            st.write(result)


# ============================================================
# WORKLOAD CONFIGURATION
# ============================================================

elif selected_page == "Workload Configuration":

    st.markdown(
        '<div class="section-title">Workload Configuration</div>',
        unsafe_allow_html=True
    )

    current = normalize_workload(
        st.session_state.workload
    )

    col1, col2 = st.columns(2)

    with col1:

        traffic_pattern = st.selectbox(
            "Traffic Pattern",
            [
                "steady",
                "bursty"
            ],
            index=(
                0
                if current["traffic_pattern"] == "steady"
                else 1
            )
        )

        request_volume = st.number_input(
            "Monthly Request Volume",
            min_value=1,
            value=current["request_volume"],
            step=10000
        )

        latency = st.selectbox(
            "Latency Requirement",
            [
                "standard",
                "critical"
            ],
            index=(
                0
                if current["latency"] == "standard"
                else 1
            )
        )

    with col2:

        request_duration = st.number_input(
            "Average Request Duration (seconds)",
            min_value=0.01,
            value=float(
                current["request_duration"]
            ),
            step=0.1
        )

        concurrency = st.number_input(
            "Expected Concurrency",
            min_value=1,
            value=current["concurrency"],
            step=1
        )

        memory_gb = st.number_input(
            "Memory Requirement (GB)",
            min_value=0.25,
            value=float(
                current["memory_gb"]
            ),
            step=0.25
        )

    if st.button(
        "Save Workload Configuration",
        type="primary"
    ):

        st.session_state.workload = normalize_workload(
            {
                "traffic_pattern": traffic_pattern,
                "request_volume": request_volume,
                "latency": latency,
                "request_duration": request_duration,
                "concurrency": concurrency,
                "memory_gb": memory_gb
            }
        )

        st.success(
            "Workload configuration saved."
        )

    st.markdown(
        '<div class="section-title">Current Configuration</div>',
        unsafe_allow_html=True
    )

    saved = normalize_workload(
        st.session_state.workload
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Monthly Requests",
            f"{saved['request_volume']:,}"
        )

    with c2:
        st.metric(
            "Concurrency",
            saved["concurrency"]
        )

    with c3:
        st.metric(
            "Memory",
            f"{saved['memory_gb']:.2f} GB"
        )


# ============================================================
# WORKLOAD ANALYSIS
# ============================================================

elif selected_page == "Workload Analysis":

    st.markdown(
        '<div class="section-title">Workload Analysis</div>',
        unsafe_allow_html=True
    )

    workload = normalize_workload(
        st.session_state.workload
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Traffic",
            workload["traffic_pattern"].title()
        )

    with c2:
        st.metric(
            "Requests",
            f"{workload['request_volume']:,}"
        )

    with c3:
        st.metric(
            "Duration",
            f"{workload['request_duration']:.2f}s"
        )

    with c4:
        st.metric(
            "Concurrency",
            workload["concurrency"]
        )

    st.markdown(
        '<div class="section-title">Workload Interpretation</div>',
        unsafe_allow_html=True
    )

    if workload["traffic_pattern"] == "bursty":

        st.warning(
            "Bursty traffic can benefit from elastic scaling."
        )

    else:

        st.info(
            "Steady traffic provides a predictable workload profile."
        )

    if workload["concurrency"] >= 100:

        st.warning(
            "High concurrency workload detected. "
            "Managed services with strong concurrency/scaling "
            "support should be evaluated carefully."
        )

    if workload["request_duration"] > 10:

        st.warning(
            "Long request duration detected. "
            "Execution-time limits should be checked."
        )

    if workload["latency"] == "critical":

        st.warning(
            "Critical latency requirement detected."
        )

    st.success(
        "Workload analysis completed using the configured workload."
    )


# ============================================================
# DEPLOYMENT DECISION
# ============================================================

elif selected_page == "Deployment Decision":

    st.markdown(
        '<div class="section-title">Deployment Decision</div>',
        unsafe_allow_html=True
    )

    workload = normalize_workload(
        st.session_state.workload
    )

    st.info(
        "The decision engine compares compatible managed/serverless "
        "options against the evaluated VM baseline."
    )

    with st.expander(
        "Workload sent to decision engine",
        expanded=False
    ):

        st.json(workload)

    if st.button(
        "Run Deployment Decision",
        type="primary"
    ):

        with st.spinner(
            "Analyzing deployment strategy..."
        ):

            try:

                result = build_deployment_decision(
                    workload
                )

                st.session_state.deployment_result = result

            except Exception as error:

                st.error(
                    f"Deployment decision failed: {error}"
                )

    result = st.session_state.deployment_result

    if result:

        strategy = result.get(
            "strategy",
            result.get(
                "preferred_strategy",
                "Unknown"
            )
        )

        provider = result.get(
            "provider",
            result.get(
                "recommended_provider",
                "Unknown"
            )
        )

        cost = result.get(
            "estimated_monthly_cost",
            result.get(
                "cost",
                None
            )
        )

        if isinstance(cost, dict):

            cost = cost.get(
                "monthly_cost",
                cost.get(
                    "estimated_monthly_cost",
                    0
                )
            )

        # ====================================================
        # FIXED: NATIVE STREAMLIT RECOMMENDATION DISPLAY
        # Prevents raw HTML source from appearing.
        # ====================================================

        with st.container(
            border=True
        ):

            st.caption(
                "RECOMMENDED DEPLOYMENT"
            )

            st.subheader(
                strategy
            )

            st.write(
                provider
            )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Strategy",
                strategy
            )

        with c2:

            st.metric(
                "Provider",
                provider
            )

        with c3:

            st.metric(
                "Estimated Monthly Cost",
                money(cost)
            )

        reason = result.get(
            "reason"
        )

        if reason:

            st.info(
                reason
            )

        compatibility = result.get(
            "compatibility"
        )

        if compatibility:

            st.markdown(
                '<div class="section-title">Compatibility Evidence</div>',
                unsafe_allow_html=True
            )

            compatible = compatibility.get(
                "compatible_providers",
                []
            )

            incompatible = compatibility.get(
                "incompatible_providers",
                []
            )

            if compatible:

                st.success(
                    "Compatible: "
                    + ", ".join(compatible)
                )

            if incompatible:

                st.error(
                    "Not compatible: "
                    + ", ".join(incompatible)
                )


# ============================================================
# CLOUD MARKET & COST
# ============================================================

elif selected_page == "Cloud Market & Cost":

    st.markdown(
        '<div class="section-title">Cloud Market & Cost</div>',
        unsafe_allow_html=True
    )

    workload = normalize_workload(
        st.session_state.workload
    )

    if st.button(
        "Run Cost Analysis",
        type="primary"
    ):

        with st.spinner(
            "Calculating cloud deployment costs..."
        ):

            try:

                st.session_state.cost_result = (
                    get_cost_analysis(workload)
                )

            except Exception as error:

                st.error(
                    f"Cost analysis failed: {error}"
                )

    result = st.session_state.cost_result

    if result:

        serverless = result.get(
            "serverless",
            {}
        )

        vm = result.get(
            "vm",
            {}
        )

        rows = []

        for provider, details in serverless.items():

            if isinstance(details, dict):

                cost = details.get(
                    "monthly_cost",
                    details.get(
                        "estimated_monthly_cost",
                        details.get(
                            "cost",
                            0
                        )
                    )
                )

            else:

                cost = details

            rows.append(
                {
                    "Provider": normalize_provider_name(
                        provider
                    ),
                    "Deployment Type": "Managed / Serverless",
                    "Monthly Cost": safe_float(cost)
                }
            )

        for provider, details in vm.items():

            if isinstance(details, dict):

                cost = details.get(
                    "monthly_cost",
                    details.get(
                        "estimated_monthly_cost",
                        details.get(
                            "cost",
                            0
                        )
                    )
                )

            else:

                cost = details

            rows.append(
                {
                    "Provider": normalize_provider_name(
                        provider
                    ),
                    "Deployment Type": "Self-Managed VM",
                    "Monthly Cost": safe_float(cost)
                }
            )

        if rows:

            df = pd.DataFrame(rows)

            st.dataframe(
                df.style.format(
                    {
                        "Monthly Cost": "${:,.4f}"
                    }
                ),
                width="stretch",
                hide_index=True
            )

            chart = px.bar(
                df,
                x="Provider",
                y="Monthly Cost",
                color="Deployment Type",
                title="Estimated Monthly Deployment Cost"
            )

            chart.update_layout(
                yaxis_title="Monthly Cost (USD)"
            )

            st.plotly_chart(
                chart,
                width="stretch"
            )


# ============================================================
# PROVIDER COMPARISON
# ============================================================

elif selected_page == "Provider Comparison":

    st.markdown(
        '<div class="section-title">Provider Comparison</div>',
        unsafe_allow_html=True
    )

    workload = normalize_workload(
        st.session_state.workload
    )

    if st.button(
        "Analyze Cloud Providers",
        type="primary"
    ):

        with st.spinner(
            "Checking provider compatibility..."
        ):

            try:

                st.session_state.provider_result = (
                    compare_cloud_providers(
                        workload
                    )
                )

            except Exception as error:

                st.error(
                    f"Provider analysis failed: {error}"
                )

    provider_result = st.session_state.provider_result

    if provider_result:

        compatible = provider_result.get(
            "compatible_providers",
            []
        )

        incompatible = provider_result.get(
            "incompatible_providers",
            []
        )

        st.markdown(
            "### Provider Compatibility"
        )

        if compatible:

            st.success(
                "Compatible providers: "
                + ", ".join(compatible)
            )

        if incompatible:

            st.error(
                "Incompatible providers: "
                + ", ".join(incompatible)
            )

        cost_result = st.session_state.cost_result

        if cost_result is None:

            try:

                cost_result = get_cost_analysis(
                    workload
                )

                st.session_state.cost_result = (
                    cost_result
                )

            except Exception as error:

                st.warning(
                    f"Could not load cost data: {error}"
                )

                cost_result = {}

        serverless = cost_result.get(
            "serverless",
            {}
        )

        provider_costs = {}

        for provider, details in serverless.items():

            name = normalize_provider_name(
                provider
            )

            if isinstance(details, dict):

                cost = details.get(
                    "monthly_cost",
                    details.get(
                        "estimated_monthly_cost",
                        details.get(
                            "cost",
                            0
                        )
                    )
                )

            else:

                cost = details

            provider_costs[name] = safe_float(
                cost
            )

        selected_provider = None

        deployment = st.session_state.deployment_result

        if deployment:

            selected_provider = normalize_provider_name(
                deployment.get(
                    "provider"
                )
            )

        if selected_provider not in compatible:

            compatible_with_cost = {
                p: provider_costs.get(
                    p,
                    float("inf")
                )
                for p in compatible
            }

            if compatible_with_cost:

                selected_provider = min(
                    compatible_with_cost,
                    key=compatible_with_cost.get
                )

        provider_names = [
            "AWS Lambda",
            "Azure Functions",
            "Google Cloud Run"
        ]

        cols = st.columns(3)

        for index, provider in enumerate(
            provider_names
        ):

            with cols[index]:

                is_compatible = (
                    provider in compatible
                )

                is_selected = (
                    provider == selected_provider
                )

                cost = provider_costs.get(
                    provider,
                    0
                )

                with st.container(
                    border=True
                ):

                    st.subheader(
                        provider
                    )

                    if is_selected:

                        st.success(
                            "⭐ Recommended for current workload"
                        )

                    if is_compatible:

                        st.success(
                            "✅ Compatible"
                        )

                    else:

                        st.error(
                            "❌ Not Compatible"
                        )

                    st.metric(
                        "Modeled Monthly Cost",
                        money(cost, 4)
                    )

                    details = (
                        provider_result.get(
                            "providers",
                            {}
                        ).get(
                            provider,
                            {}
                        )
                    )

                    configuration = details.get(
                        "recommended_configuration",
                        {}
                    )

                    if configuration:

                        st.markdown(
                            "**Recommended Configuration**"
                        )

                        for key, value in configuration.items():

                            st.write(
                                f"**{key}:** {value}"
                            )

                    checks = details.get(
                        "checks",
                        {}
                    )

                    if checks:

                        st.markdown(
                            "**Compatibility Checks**"
                        )

                        for key, value in checks.items():

                            icon = (
                                "✅"
                                if value
                                else "❌"
                            )

                            st.write(
                                f"{icon} {key}"
                            )

                    reason = details.get(
                        "reason"
                    )

                    if reason:

                        st.info(
                            reason
                        )

                    limitations = details.get(
                        "limitations",
                        []
                    )

                    if limitations:

                        st.markdown(
                            "**Limitations**"
                        )

                        for item in limitations:

                            st.write(
                                f"• {item}"
                            )

                    warnings = details.get(
                        "warnings",
                        []
                    )

                    if warnings:

                        st.markdown(
                            "**Warnings**"
                        )

                        for item in warnings:

                            st.warning(
                                item
                            )

        if provider_costs:

            cost_df = pd.DataFrame(
                [
                    {
                        "Provider": provider,
                        "Monthly Cost": cost
                    }
                    for provider, cost
                    in provider_costs.items()
                ]
            )

            st.markdown(
                '<div class="section-title">Serverless Cost Comparison</div>',
                unsafe_allow_html=True
            )

            chart = px.bar(
                cost_df,
                x="Provider",
                y="Monthly Cost",
                title="Serverless Provider Cost Comparison"
            )

            chart.update_layout(
                yaxis_title="Monthly Cost (USD)"
            )

            st.plotly_chart(
                chart,
                width="stretch"
            )


# ============================================================
# PREDICTIVE SCALING
# ============================================================

elif selected_page == "Predictive Scaling":

    st.markdown(
        '<div class="section-title">Scaling Outlook</div>',
        unsafe_allow_html=True
    )

    st.info(
        "This page visualizes controlled workload scenarios. "
        "It is not a production forecast because historical telemetry "
        "is not yet connected."
    )

    workload = normalize_workload(
        st.session_state.workload
    )

    base_requests = workload[
        "request_volume"
    ]

    volumes = [
        max(1, int(base_requests * 0.25)),
        max(1, int(base_requests * 0.5)),
        max(1, int(base_requests)),
        max(1, int(base_requests * 2)),
        max(1, int(base_requests * 5))
    ]

    rows = []

    for volume in volumes:

        scenario_workload = normalize_workload(
            {
                **workload,
                "request_volume": volume
            }
        )

        try:

            result = get_cost_analysis(
                scenario_workload
            )

            serverless = result.get(
                "serverless",
                {}
            )

            candidates = {}

            for provider, details in serverless.items():

                provider_name = normalize_provider_name(
                    provider
                )

                if isinstance(details, dict):

                    cost = details.get(
                        "monthly_cost",
                        details.get(
                            "estimated_monthly_cost",
                            details.get(
                                "cost",
                                0
                            )
                        )
                    )

                else:

                    cost = details

                cost = safe_float(cost)

                if cost > 0:

                    candidates[
                        provider_name
                    ] = cost

            if candidates:

                provider = min(
                    candidates,
                    key=candidates.get
                )

                cost = candidates[
                    provider
                ]

            else:

                provider = "Unavailable"
                cost = 0

            rows.append(
                {
                    "Requests / Month": volume,
                    "Provider": provider,
                    "Monthly Cost": cost
                }
            )

        except Exception:

            pass

    if rows:

        df = pd.DataFrame(rows)

        chart = px.line(
            df,
            x="Requests / Month",
            y="Monthly Cost",
            color="Provider",
            markers=True,
            title="Scaling Outlook: Request Volume vs Cost"
        )

        chart.update_layout(
            xaxis_title="Monthly Request Volume",
            yaxis_title="Monthly Cost (USD)"
        )

        st.plotly_chart(
            chart,
            width="stretch"
        )

        st.caption(
            "Controlled workload curve using the project's pricing model. "
            "This should not be interpreted as historical or predictive production data."
        )


# ============================================================
# ML BENCHMARK
# ============================================================

elif selected_page == "ML Benchmark":

    st.markdown(
        '<div class="section-title">ML Model Benchmark</div>',
        unsafe_allow_html=True
    )

    st.info(
        "The benchmark measures local ML model execution. "
        "It does not represent cloud-provider performance."
    )

    if st.button(
        "Run ML Benchmark",
        type="primary"
    ):

        st.session_state.benchmark_result = (
            get_benchmark(
                st.session_state.model_path
            )
        )

    result = st.session_state.benchmark_result

    if result:

        if isinstance(result, dict):

            success_rate = result.get(
                "success_rate",
                0
            )

            throughput = result.get(
                "throughput",
                0
            )

            p95 = result.get(
                "p95_latency",
                result.get(
                    "p95_latency_ms",
                    0
                )
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "Success Rate",
                    f"{safe_float(success_rate):.2f}%"
                )

            with c2:

                st.metric(
                    "Throughput",
                    f"{safe_float(throughput):,.2f} req/s"
                )

            with c3:

                st.metric(
                    "P95 Latency",
                    f"{safe_float(p95):,.2f}"
                )

            rows = []

            for key, value in result.items():

                if isinstance(
                    value,
                    (dict, list, tuple)
                ):

                    value = str(value)

                rows.append(
                    {
                        "Metric": key,
                        "Value": value
                    }
                )

            st.dataframe(
                pd.DataFrame(rows),
                width="stretch",
                hide_index=True
            )


# ============================================================
# SCENARIO SIMULATOR
# ============================================================

elif selected_page == "Scenario Simulator":

    st.markdown(
        '<div class="section-title">Scenario Simulator</div>',
        unsafe_allow_html=True
    )

    st.info(
        "Evaluate predefined workload conditions and observe "
        "how the recommendation changes."
    )

    scenarios = {

        "Low Traffic": {
            "traffic_pattern": "steady",
            "monthly_requests": 10000,
            "latency": "standard",
            "request_duration": 0.2,
            "expected_concurrency": 5,
            "memory_gb": 1.0
        },

        "Normal Traffic": {
            "traffic_pattern": "steady",
            "monthly_requests": 100000,
            "latency": "standard",
            "request_duration": 0.2,
            "expected_concurrency": 10,
            "memory_gb": 1.0
        },

        "High Traffic": {
            "traffic_pattern": "steady",
            "monthly_requests": 1000000,
            "latency": "standard",
            "request_duration": 0.5,
            "expected_concurrency": 50,
            "memory_gb": 1.0
        },

        "Bursty Traffic": {
            "traffic_pattern": "bursty",
            "monthly_requests": 500000,
            "latency": "standard",
            "request_duration": 0.2,
            "expected_concurrency": 50,
            "memory_gb": 1.0
        },

        "High Concurrency": {
            "traffic_pattern": "steady",
            "monthly_requests": 1000000,
            "latency": "critical",
            "request_duration": 0.5,
            "expected_concurrency": 200,
            "memory_gb": 2.0
        }
    }

    selected_scenario = st.selectbox(
        "Select Scenario",
        list(scenarios.keys())
    )

    if st.button(
        "Run Scenario",
        type="primary"
    ):

        ui_scenario = scenarios[
            selected_scenario
        ]

        scenario_workload = normalize_workload(
            ui_scenario
        )

        try:

            cost_result = get_cost_analysis(
                scenario_workload
            )

            compatibility = compare_cloud_providers(
                scenario_workload
            )

            compatible = compatibility.get(
                "compatible_providers",
                []
            )

            serverless = cost_result.get(
                "serverless",
                {}
            )

            candidates = {}

            for provider, details in serverless.items():

                provider_name = normalize_provider_name(
                    provider
                )

                if provider_name not in compatible:
                    continue

                if isinstance(details, dict):

                    cost = details.get(
                        "monthly_cost",
                        details.get(
                            "estimated_monthly_cost",
                            details.get(
                                "cost",
                                0
                            )
                        )
                    )

                else:

                    cost = details

                cost = safe_float(cost)

                if cost > 0:

                    candidates[
                        provider_name
                    ] = cost

            if candidates:

                provider = min(
                    candidates,
                    key=candidates.get
                )

                recommended_cost = candidates[
                    provider
                ]

                strategy = "Managed / Serverless"

            else:

                provider = "Unavailable"
                recommended_cost = 0
                strategy = "Unable to determine"

            st.session_state.scenario_results.append(
                {
                    "Scenario": selected_scenario,
                    "Requests / Month": scenario_workload[
                        "request_volume"
                    ],
                    "Provider": provider,
                    "Strategy": strategy,
                    "Monthly Cost": recommended_cost
                }
            )

            st.success(
                "Scenario completed."
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "Strategy",
                    strategy
                )

            with c2:

                st.metric(
                    "Provider",
                    provider
                )

            with c3:

                st.metric(
                    "Monthly Cost",
                    money(
                        recommended_cost,
                        4
                    )
                )

        except Exception as error:

            st.error(
                f"Scenario simulation failed: {error}"
            )

    if st.session_state.scenario_results:

        df = pd.DataFrame(
            st.session_state.scenario_results
        )

        st.markdown(
            '<div class="section-title">Scenario Results</div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            df.style.format(
                {
                    "Monthly Cost": "${:,.4f}"
                }
            ),
            width="stretch",
            hide_index=True
        )

        valid = df[
            df["Monthly Cost"] > 0
        ].copy()

        if not valid.empty:

            trend = valid.sort_values(
                "Requests / Month"
            ).copy()

            trend_chart = px.line(
                trend,
                x="Requests / Month",
                y="Monthly Cost",
                color="Provider",
                markers=True,
                text="Scenario",
                custom_data=[
                    "Scenario",
                    "Provider",
                    "Strategy"
                ],
                title=(
                    "Request Volume vs "
                    "Recommended Monthly Cost"
                )
            )

            trend_chart.update_traces(
                mode="lines+markers+text",
                textposition="top center",
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Requests: %{x:,}<br>"
                    "Recommended Cost: $%{y:.2f}/month<br>"
                    "Provider: %{customdata[1]}<br>"
                    "Strategy: %{customdata[2]}"
                    "<extra></extra>"
                )
            )

            trend_chart.update_layout(
                xaxis_title="Monthly Request Volume",
                yaxis_title=(
                    "Recommended Monthly Cost (USD)"
                ),
                hovermode="x unified"
            )

            st.plotly_chart(
                trend_chart,
                width="stretch"
            )

            st.caption(
                "The connected line shows how the recommended "
                "monthly cost changes as request volume increases. "
                "Scenario labels identify the evaluated workloads. "
                "This is scenario analysis, not a production forecast."
            )


# ============================================================
# FINAL RECOMMENDATION
# ============================================================

elif selected_page == "Final Recommendation":

    st.markdown(
        '<div class="section-title">Final Recommendation</div>',
        unsafe_allow_html=True
    )

    workload = normalize_workload(
        st.session_state.workload
    )

    if st.session_state.deployment_result is None:

        with st.spinner(
            "Building final recommendation..."
        ):

            try:

                st.session_state.deployment_result = (
                    build_deployment_decision(
                        workload
                    )
                )

            except Exception as error:

                st.error(
                    f"Recommendation failed: {error}"
                )

    result = st.session_state.deployment_result

    if result:

        strategy = result.get(
            "strategy",
            "Unknown"
        )

        provider = result.get(
            "provider",
            "Unknown"
        )

        cost = result.get(
            "estimated_monthly_cost",
            0
        )

        if isinstance(cost, dict):

            cost = cost.get(
                "monthly_cost",
                cost.get(
                    "estimated_monthly_cost",
                    0
                )
            )

        # ====================================================
        # FIXED: NATIVE STREAMLIT RECOMMENDATION DISPLAY
        # Prevents raw HTML source from appearing.
        # ====================================================

        with st.container(
            border=True
        ):

            st.caption(
                "FINAL DEPLOYMENT RECOMMENDATION"
            )

            st.subheader(
                strategy
            )

            st.write(
                provider
            )

            st.write(
                f"Estimated monthly cost: {money(cost, 4)}"
            )

        reason = result.get(
            "reason"
        )

        if reason:

            st.markdown(
                "### Why this deployment?"
            )

            st.write(
                reason
            )

        compatibility = result.get(
            "compatibility",
            {}
        )

        if compatibility:

            compatible = compatibility.get(
                "compatible_providers",
                []
            )

            if compatible:

                st.markdown(
                    "### Compatible Providers"
                )

                for item in compatible:

                    if item == provider:

                        st.success(
                            f"⭐ {item} — Selected"
                        )

                    else:

                        st.write(
                            f"• {item}"
                        )

        cost_data = result.get(
            "cost",
            {}
        )

        if cost_data:

            serverless = cost_data.get(
                "serverless",
                {}
            )

            vm = cost_data.get(
                "vm",
                {}
            )

            rows = []

            for name, details in serverless.items():

                if isinstance(details, dict):

                    value = details.get(
                        "monthly_cost",
                        details.get(
                            "estimated_monthly_cost",
                            details.get(
                                "cost",
                                0
                            )
                        )
                    )

                else:

                    value = details

                rows.append(
                    {
                        "Provider": normalize_provider_name(
                            name
                        ),
                        "Deployment Type": "Serverless",
                        "Monthly Cost": safe_float(
                            value
                        )
                    }
                )

            for name, details in vm.items():

                if isinstance(details, dict):

                    value = details.get(
                        "monthly_cost",
                        details.get(
                            "estimated_monthly_cost",
                            details.get(
                                "cost",
                                0
                            )
                        )
                    )

                else:

                    value = details

                rows.append(
                    {
                        "Provider": normalize_provider_name(
                            name
                        ),
                        "Deployment Type": "VM",
                        "Monthly Cost": safe_float(
                            value
                        )
                    }
                )

            if rows:

                df = pd.DataFrame(rows)

                st.markdown(
                    "### Cost Evidence"
                )

                st.dataframe(
                    df.style.format(
                        {
                            "Monthly Cost": "${:,.4f}"
                        }
                    ),
                    width="stretch",
                    hide_index=True
                )

                chart = px.bar(
                    df,
                    x="Provider",
                    y="Monthly Cost",
                    color="Deployment Type",
                    title="Deployment Cost Evidence"
                )

                chart.update_layout(
                    yaxis_title="Monthly Cost (USD)"
                )

                st.plotly_chart(
                    chart,
                    width="stretch"
                )

        st.markdown(
            """
            <div class="warning-box">
            <b>Important:</b>
            The recommendation is based on provider compatibility,
            available pricing data, workload assumptions, break-even
            analysis and local ML model evidence. The local benchmark
            does not represent cloud-provider performance.
            </div>
            """,
            unsafe_allow_html=True
        )