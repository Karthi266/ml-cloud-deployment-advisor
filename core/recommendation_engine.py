"""
recommendation_engine.py

Final ML Cloud Deployment Recommendation Engine.

Decision inputs:
    1. Provider compatibility
    2. Real pricing
    3. Break-even analysis
    4. Local ML model benchmark
    5. Deployment strategy

Important:
    The local benchmark measures the ML model itself.
    It does NOT represent cloud-provider performance.

    Provider compatibility is based on documented
    service capabilities/limits.

    Provider cost comes from the project's pricing modules.

    No artificial provider performance score is used
    for provider selection.
"""

import joblib

from core.cloud_provider_advisor import compare_cloud_providers
from pricing.cost_calculator import run_cost_analysis
from core.break_even_engine import run_break_even_analysis
from core.benchmark_engine import run_benchmark


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "spam_classifier.joblib"

DEFAULT_WORKLOAD = {
    "traffic_pattern": "steady",
    "request_volume": 100000,
    "latency": "standard",
    "request_duration": 0.2,
    "concurrency": 10,
    "memory_gb": 1
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    """
    Safely convert a value into float.
    """

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def get_benchmark_value(
    benchmark_result,
    possible_keys,
    default=0.0
):
    """
    Read a benchmark value from one of several possible keys.

    This makes the recommendation engine more tolerant
    of small changes in benchmark_engine.py.
    """

    if not benchmark_result:
        return default

    for key in possible_keys:

        if key in benchmark_result:

            value = benchmark_result.get(key)

            if value is not None:
                return safe_float(
                    value,
                    default
                )

    return default


def extract_serverless_costs(cost_result):
    """
    Extract serverless provider monthly costs.

    Supported providers:
        AWS Lambda
        Azure Functions
        Google Cloud Run
    """

    if not isinstance(cost_result, dict):
        return {}

    serverless = cost_result.get(
        "serverless",
        {}
    )

    if not isinstance(serverless, dict):
        return {}

    result = {}

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

        cost = safe_float(
            cost,
            0
        )

        if cost > 0:
            result[provider] = cost

    return result


def extract_vm_costs(cost_result):
    """
    Extract VM monthly costs.
    """

    if not isinstance(cost_result, dict):
        return {}

    vm = cost_result.get(
        "vm",
        {}
    )

    if not isinstance(vm, dict):
        return {}

    result = {}

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

        cost = safe_float(
            cost,
            0
        )

        if cost > 0:
            result[provider] = cost

    return result


def select_serverless_provider(
    compatibility_result,
    cost_result
):
    """
    Select the lowest-cost provider among
    compatible serverless providers.

    No artificial provider score is used.

    Selection is based on:
        Compatibility
        +
        Evaluated monthly cost
    """

    if not isinstance(
        compatibility_result,
        dict
    ):
        return None, {}

    compatible_providers = compatibility_result.get(
        "compatible_providers",
        []
    )

    if not compatible_providers:
        return None, {}

    cost_data = extract_serverless_costs(
        cost_result
    )

    candidates = {}

    for provider in compatible_providers:

        if provider in cost_data:

            cost = cost_data[provider]

            if cost > 0:
                candidates[provider] = cost

    if not candidates:
        return None, {}

    recommended_provider = min(
        candidates,
        key=candidates.get
    )

    return (
        recommended_provider,
        candidates
    )


def extract_break_even_evidence(
    break_even_result
):
    """
    Extract break-even request thresholds.

    Supports both possible structures:

        Provider -> numeric value

    and:

        Provider -> {
            "break_even_requests": value
        }

    This keeps the recommendation engine
    compatible with the current break-even engine.
    """

    if not isinstance(
        break_even_result,
        dict
    ):
        return {}

    break_even_data = break_even_result.get(
        "break_even",
        {}
    )

    if not isinstance(
        break_even_data,
        dict
    ):
        return {}

    result = {}

    for provider, details in break_even_data.items():

        if isinstance(details, dict):

            break_even_requests = safe_float(
                details.get(
                    "break_even_requests",
                    details.get(
                        "requests",
                        0
                    )
                ),
                0
            )

        else:

            break_even_requests = safe_float(
                details,
                0
            )

        if break_even_requests > 0:

            result[provider] = (
                break_even_requests
            )

    return result


def build_decision_evidence(
    preferred_strategy,
    preferred_provider,
    preferred_cost,
    serverless_candidates,
    cheapest_vm,
    cheapest_vm_cost,
    compatibility_result,
    break_even_result
):
    """
    Build human-readable evidence explaining
    why the recommendation was selected.
    """

    reasons = []
    evidence = []

    compatible_providers = (
        compatibility_result.get(
            "compatible_providers",
            []
        )
        if isinstance(
            compatibility_result,
            dict
        )
        else []
    )

    # --------------------------------------------------------
    # Serverless decision
    # --------------------------------------------------------

    if (
        preferred_strategy == "Managed / Serverless"
        and preferred_provider is not None
    ):

        reasons.append(
            f"{preferred_provider} is compatible "
            f"with the evaluated workload."
        )

        evidence.append(
            "Compatibility: "
            f"{preferred_provider} is listed as "
            "a compatible serverless provider."
        )

        if preferred_cost is not None:

            reasons.append(
                f"{preferred_provider} has the lowest "
                "evaluated monthly cost among "
                "compatible serverless providers."
            )

            evidence.append(
                "Cost: Lowest compatible serverless "
                f"cost: ${preferred_cost:.4f}/month."
            )

        # ----------------------------------------------------
        # Compare with VM
        # ----------------------------------------------------

        if (
            cheapest_vm is not None
            and cheapest_vm_cost is not None
            and preferred_cost is not None
        ):

            savings = (
                cheapest_vm_cost
                - preferred_cost
            )

            if savings > 0:

                reasons.append(
                    "The estimated serverless cost is "
                    f"lower than the cheapest evaluated "
                    f"VM by ${savings:.4f}/month."
                )

                evidence.append(
                    "VM Comparison: "
                    f"{preferred_provider}: "
                    f"${preferred_cost:.4f}/month "
                    f"vs {cheapest_vm}: "
                    f"${cheapest_vm_cost:.2f}/month."
                )

    # --------------------------------------------------------
    # VM decision
    # --------------------------------------------------------

    elif (
        preferred_strategy == "Self-Managed VM"
        and preferred_provider is not None
    ):

        reasons.append(
            f"{preferred_provider} has the lowest "
            "evaluated VM cost."
        )

        evidence.append(
            "VM Cost: "
            f"{preferred_provider}: "
            f"${preferred_cost:.2f}/month."
        )

        if (
            cheapest_vm_cost is not None
            and serverless_candidates
        ):

            cheapest_serverless_provider = min(
                serverless_candidates,
                key=serverless_candidates.get
            )

            cheapest_serverless_cost = (
                serverless_candidates[
                    cheapest_serverless_provider
                ]
            )

            if cheapest_vm_cost < cheapest_serverless_cost:

                savings = (
                    cheapest_serverless_cost
                    - cheapest_vm_cost
                )

                reasons.append(
                    "The VM is cheaper than the "
                    "lowest-cost compatible serverless "
                    f"provider by ${savings:.4f}/month."
                )

                evidence.append(
                    "Serverless Comparison: "
                    f"{cheapest_serverless_provider}: "
                    f"${cheapest_serverless_cost:.4f}/month "
                    f"vs {preferred_provider}: "
                    f"${cheapest_vm_cost:.2f}/month."
                )

    # --------------------------------------------------------
    # Break-even evidence
    # --------------------------------------------------------

    break_even_evidence = (
        extract_break_even_evidence(
            break_even_result
        )
    )

    if preferred_provider in break_even_evidence:

        threshold = break_even_evidence[
            preferred_provider
        ]

        evidence.append(
            f"Break-even: approximately "
            f"{threshold:,.0f} requests/month "
            f"for {preferred_provider}."
        )

    # --------------------------------------------------------
    # Compatibility summary
    # --------------------------------------------------------

    if compatible_providers:

        evidence.append(
            "Compatible providers: "
            + ", ".join(
                compatible_providers
            )
        )

    return {
        "reasons": reasons,
        "evidence": evidence
    }


# ============================================================
# MAIN ANALYSIS
# ============================================================

def run_full_recommendation(
    workload=None,
    model_path=MODEL_PATH
):
    """
    Run the complete recommendation pipeline.
    """

    if workload is None:

        workload = (
            DEFAULT_WORKLOAD.copy()
        )

    print("\n")
    print(
        "===================================================="
    )
    print(
        "       ML CLOUD DEPLOYMENT RECOMMENDATION"
    )
    print(
        "===================================================="
    )

    # ========================================================
    # STEP 1 - LOAD MODEL
    # ========================================================

    print(
        "\n[1] Loading ML model..."
    )

    try:

        model = joblib.load(
            model_path
        )

        print(
            "Model loaded successfully:",
            model_path
        )

    except Exception as error:

        print(
            "ERROR: Unable to load model."
        )

        print(
            "Reason:",
            error
        )

        return {
            "success": False,
            "error": str(error)
        }

    # ========================================================
    # STEP 2 - PROVIDER COMPATIBILITY
    # ========================================================

    print(
        "\n[2] Provider Compatibility Analysis..."
    )

    compatibility_result = (
        compare_cloud_providers(
            workload
        )
    )

    compatible_providers = (
        compatibility_result.get(
            "compatible_providers",
            []
        )
    )

    print(
        "\nCompatible providers:"
    )

    for provider in compatible_providers:

        print(
            "-",
            provider
        )

    # ========================================================
    # STEP 3 - COST ANALYSIS
    # ========================================================

    print(
        "\n[3] Real Pricing Analysis..."
    )

    cost_result = run_cost_analysis(
        workload
    )

    serverless_costs = (
        extract_serverless_costs(
            cost_result
        )
    )

    vm_costs = extract_vm_costs(
        cost_result
    )

    print(
        "\nServerless Costs:"
    )

    for provider, cost in (
        serverless_costs.items()
    ):

        print(
            f"- {provider}: "
            f"${cost:.4f}/month"
        )

    print(
        "\nVM Costs:"
    )

    for provider, cost in (
        vm_costs.items()
    ):

        print(
            f"- {provider}: "
            f"${cost:.2f}/month"
        )

    # ========================================================
    # STEP 4 - SELECT COMPATIBLE SERVERLESS PROVIDER
    # ========================================================

    print(
        "\n[4] Selecting Compatible "
        "Serverless Provider..."
    )

    serverless_provider, candidates = (
        select_serverless_provider(
            compatibility_result,
            cost_result
        )
    )

    if serverless_provider:

        serverless_cost = (
            candidates[
                serverless_provider
            ]
        )

        print(
            "\nLowest-cost compatible "
            "serverless provider:"
        )

        print(
            "-",
            serverless_provider
        )

        print(
            "- Estimated cost: "
            f"${serverless_cost:.4f}/month"
        )

    else:

        serverless_cost = None

        print(
            "\nNo compatible serverless "
            "provider with available "
            "pricing data was found."
        )

    # ========================================================
    # STEP 5 - VM BASELINE
    # ========================================================

    print(
        "\n[5] VM Baseline Analysis..."
    )

    valid_vm_costs = {
        provider: cost
        for provider, cost
        in vm_costs.items()
        if cost > 0
    }

    if valid_vm_costs:

        cheapest_vm = min(
            valid_vm_costs,
            key=valid_vm_costs.get
        )

        cheapest_vm_cost = (
            valid_vm_costs[
                cheapest_vm
            ]
        )

        print(
            "Lowest-cost evaluated VM:"
        )

        print(
            "-",
            cheapest_vm
        )

        print(
            "- Estimated cost: "
            f"${cheapest_vm_cost:.2f}/month"
        )

    else:

        cheapest_vm = None
        cheapest_vm_cost = None

        print(
            "No valid VM pricing data available."
        )

    # ========================================================
    # STEP 6 - BREAK-EVEN ANALYSIS
    # ========================================================

    print(
        "\n[6] Break-even Analysis..."
    )

    break_even_result = (
        run_break_even_analysis(
            workload
        )
    )

    print(
        "\nBreak-even analysis completed."
    )

    # ========================================================
    # STEP 7 - LOCAL ML BENCHMARK
    # ========================================================

    print(
        "\n[7] Local ML Model Benchmark..."
    )

    sample_input = [
        "Congratulations! You have won "
        "a free prize. Click this link now "
        "to claim your reward."
    ]

    try:

        benchmark_result = run_benchmark(
            model,
            sample_input
        )

    except TypeError:

        try:

            benchmark_result = run_benchmark(
                model
            )

        except Exception as error:

            print(
                "Benchmark could not be executed:"
            )

            print(
                error
            )

            benchmark_result = {}

    except Exception as error:

        print(
            "Benchmark could not be executed:"
        )

        print(
            error
        )

        benchmark_result = {}

    # ========================================================
    # STEP 8 - MODEL FEASIBILITY
    # ========================================================

    success_rate = get_benchmark_value(
        benchmark_result,
        [
            "success_rate"
        ],
        0
    )

    throughput = get_benchmark_value(
        benchmark_result,
        [
            "throughput",
            "throughput_rps"
        ],
        0
    )

    p95_latency_seconds = (
        get_benchmark_value(
            benchmark_result,
            [
                "p95_latency",
                "p95_latency_seconds"
            ],
            0
        )
    )

    p95_latency_ms = (
        p95_latency_seconds * 1000
    )

    explicit_p95_ms = (
        get_benchmark_value(
            benchmark_result,
            [
                "p95_latency_ms"
            ],
            0
        )
    )

    if explicit_p95_ms > 0:

        p95_latency_ms = (
            explicit_p95_ms
        )

    benchmark_success_rate = (
        success_rate
    )

    benchmark_throughput = (
        throughput
    )

    benchmark_p95 = (
        p95_latency_ms
    )

    # --------------------------------------------------------
    # Model feasibility calculation
    #
    # Components are calculated as percentages (0-100).
    # At the end they are explicitly converted to a 0-10
    # score.
    # --------------------------------------------------------

    model_feasibility_percentage = 0.0

    if benchmark_result:

        try:

            success_component = min(
                max(
                    benchmark_success_rate,
                    0
                ),
                100
            )

            throughput_component = min(
                (
                    benchmark_throughput
                    / 100
                ) * 100,
                100
            )

            if benchmark_p95 <= 0:

                latency_component = 0

            else:

                latency_component = min(
                    (
                        100
                        / benchmark_p95
                    ) * 100,
                    100
                )

            # ------------------------------------------------
            # Calculate overall percentage
            # ------------------------------------------------

            model_feasibility_percentage = (
                success_component
                + throughput_component
                + latency_component
            ) / 3

        except Exception:

            model_feasibility_percentage = 0.0

    # --------------------------------------------------------
    # FIX:
    #
    # Convert 0-100 percentage into 0-10 score.
    #
    # Example:
    # 100% -> 10/10
    # 90%  -> 9/10
    # 75%  -> 7.5/10
    # --------------------------------------------------------

    model_feasibility = (
        model_feasibility_percentage / 10
    )

    print(
        "\nML Model Feasibility:"
    )

    print(
        f"{model_feasibility:.2f}/10"
    )

    # ========================================================
    # STEP 9 - STRATEGY DECISION
    # ========================================================

    print(
        "\n[8] Deployment Strategy Decision..."
    )

    preferred_strategy = None
    preferred_provider = None
    preferred_cost = None

    if (
        serverless_provider is not None
        and serverless_cost is not None
        and cheapest_vm is not None
        and cheapest_vm_cost is not None
    ):

        if serverless_cost < cheapest_vm_cost:

            preferred_strategy = (
                "Managed / Serverless"
            )

            preferred_provider = (
                serverless_provider
            )

            preferred_cost = (
                serverless_cost
            )

        else:

            preferred_strategy = (
                "Self-Managed VM"
            )

            preferred_provider = (
                cheapest_vm
            )

            preferred_cost = (
                cheapest_vm_cost
            )

    elif (
        serverless_provider is not None
        and serverless_cost is not None
    ):

        preferred_strategy = (
            "Managed / Serverless"
        )

        preferred_provider = (
            serverless_provider
        )

        preferred_cost = (
            serverless_cost
        )

    elif (
        cheapest_vm is not None
        and cheapest_vm_cost is not None
    ):

        preferred_strategy = (
            "Self-Managed VM"
        )

        preferred_provider = (
            cheapest_vm
        )

        preferred_cost = (
            cheapest_vm_cost
        )

    else:

        preferred_strategy = (
            "No clear recommendation"
        )

    # ========================================================
    # STEP 10 - DECISION EVIDENCE
    # ========================================================

    decision_evidence = (
        build_decision_evidence(
            preferred_strategy,
            preferred_provider,
            preferred_cost,
            candidates,
            cheapest_vm,
            cheapest_vm_cost,
            compatibility_result,
            break_even_result
        )
    )

    # ========================================================
    # STEP 11 - FINAL OUTPUT
    # ========================================================

    print("\n")
    print(
        "===================================================="
    )
    print(
        "                 FINAL RECOMMENDATION"
    )
    print(
        "===================================================="
    )

    print(
        "\nDeployment Strategy:"
    )

    print(
        preferred_strategy
    )

    print(
        "\nRecommended Provider:"
    )

    print(
        preferred_provider
    )

    if preferred_cost is not None:

        print(
            "\nEstimated Monthly Cost:"
        )

        print(
            f"${preferred_cost:.4f}"
        )

    print(
        "\nML Model Feasibility:"
    )

    print(
        f"{model_feasibility:.2f}/10"
    )

    print(
        "\nCompatible Serverless Providers:"
    )

    for provider in compatible_providers:

        if provider == preferred_provider:

            print(
                f"- {provider} <-- SELECTED"
            )

        else:

            print(
                f"- {provider}"
            )

    # --------------------------------------------------------
    # Decision Reasons
    # --------------------------------------------------------

    print(
        "\nDecision Reasons:"
    )

    for reason in (
        decision_evidence[
            "reasons"
        ]
    ):

        print(
            "-",
            reason
        )

    # --------------------------------------------------------
    # Decision Evidence
    # --------------------------------------------------------

    print(
        "\nDecision Evidence:"
    )

    for evidence in (
        decision_evidence[
            "evidence"
        ]
    ):

        print(
            "-",
            evidence
        )

    # --------------------------------------------------------
    # Benchmark Evidence
    # --------------------------------------------------------

    print(
        "\nBenchmark Evidence:"
    )

    print(
        "- Success rate: "
        f"{benchmark_success_rate:.2f}%"
    )

    print(
        "- Throughput: "
        f"{benchmark_throughput:.2f} req/s"
    )

    print(
        "- P95 latency: "
        f"{benchmark_p95:.2f} ms"
    )

    print(
        "\nImportant:"
    )

    print(
        "The benchmark measures local ML model "
        "execution, not cloud-provider performance."
    )

    print(
        "No artificial provider performance score "
        "is used in this recommendation."
    )

    print(
        "\nDecision Basis:"
    )

    print(
        "- Provider compatibility"
    )

    print(
        "- Official/available pricing data"
    )

    print(
        "- Break-even analysis"
    )

    print(
        "- VM vs managed/serverless cost"
    )

    print(
        "- Local ML model benchmark as model evidence"
    )

    print(
        "\n"
        "===================================================="
    )

    # ========================================================
    # RETURN COMPLETE RESULT
    # ========================================================

    return {
        "success": True,

        "model": {
            "path": model_path,

            "benchmark": benchmark_result,

            "benchmark_evidence": {
                "success_rate": (
                    benchmark_success_rate
                ),

                "throughput": (
                    benchmark_throughput
                ),

                "p95_latency_ms": (
                    benchmark_p95
                )
            },

            "model_feasibility": (
                model_feasibility
            )
        },

        "workload": workload,

        "compatibility": (
            compatibility_result
        ),

        "cost": cost_result,

        "break_even": (
            break_even_result
        ),

        "benchmark": (
            benchmark_result
        ),

        "decision_evidence": (
            decision_evidence
        ),

        "decision": {
            "strategy": (
                preferred_strategy
            ),

            "provider": (
                preferred_provider
            ),

            "estimated_monthly_cost": (
                preferred_cost
            ),

            "reasons": (
                decision_evidence[
                    "reasons"
                ]
            ),

            "evidence": (
                decision_evidence[
                    "evidence"
                ]
            )
        },

        "serverless": {
            "recommended_provider": (
                serverless_provider
            ),

            "recommended_cost": (
                serverless_cost
            ),

            "candidates": (
                candidates
            )
        },

        "vm": {
            "recommended_provider": (
                cheapest_vm
            ),

            "recommended_cost": (
                cheapest_vm_cost
            ),

            "costs": (
                vm_costs
            )
        }
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    result = run_full_recommendation()

    if not result.get("success", False):

        print(
            "\nRecommendation engine failed."
        )