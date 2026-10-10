"""
break_even_engine.py

Deployment strategy break-even analysis.

Purpose:
    Determine when a self-managed VM becomes economically
    competitive with managed/serverless deployment.

The engine uses:
    - Current workload
    - Current pricing modules
    - VM monthly baseline
    - Serverless variable cost

It does NOT:
    - invent provider performance scores
    - claim cloud benchmark performance
    - predict future pricing
    - automatically migrate workloads

Main idea:

    Serverless cost = fixed/request-independent costs
                      + variable request cost

    VM cost = approximately fixed monthly infrastructure cost

The break-even point is the request volume where:

    Serverless Cost = VM Cost
"""


import math

from pricing.cost_calculator import (
    calculate_aws_lambda_cost,
    calculate_azure_functions_cost,
    calculate_google_cloud_run_cost,
    calculate_google_compute_engine_cost
)


# ============================================================
# DEFAULT WORKLOAD
# ============================================================

DEFAULT_MONTHLY_REQUESTS = 100000
DEFAULT_REQUEST_DURATION = 0.2
DEFAULT_MEMORY_GB = 1
MONTHLY_HOURS = 730


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """

    try:
        number = float(value)

        if not math.isfinite(number):
            return default

        return number

    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    """
    Safely convert a value to integer.
    """

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def get_workload_values(workload=None):
    """
    Extract workload values.

    Expected workload:

    {
        "traffic_pattern": "steady",
        "request_volume": 100000,
        "request_duration": 0.2,
        "concurrency": 10,
        "memory_gb": 1
    }
    """

    if workload is None:
        workload = {}

    monthly_requests = safe_int(
        workload.get(
            "request_volume",
            DEFAULT_MONTHLY_REQUESTS
        ),
        DEFAULT_MONTHLY_REQUESTS
    )

    request_duration = safe_float(
        workload.get(
            "request_duration",
            DEFAULT_REQUEST_DURATION
        ),
        DEFAULT_REQUEST_DURATION
    )

    memory_gb = safe_float(
        workload.get(
            "memory_gb",
            DEFAULT_MEMORY_GB
        ),
        DEFAULT_MEMORY_GB
    )

    monthly_requests = max(
        monthly_requests,
        0
    )

    request_duration = max(
        request_duration,
        0.001
    )

    memory_gb = max(
        memory_gb,
        0.001
    )

    return (
        monthly_requests,
        request_duration,
        memory_gb
    )


# ============================================================
# SERVERLESS COST FUNCTIONS
# ============================================================

def calculate_serverless_costs(
    monthly_requests,
    request_duration,
    memory_gb
):
    """
    Calculate current serverless costs using the project's
    existing pricing modules.
    """

    costs = {}

    costs["AWS Lambda"] = safe_float(
        calculate_aws_lambda_cost(
            monthly_requests,
            request_duration,
            memory_gb
        ),
        0
    )

    costs["Azure Functions"] = safe_float(
        calculate_azure_functions_cost(
            monthly_requests,
            request_duration,
            memory_gb
        ),
        0
    )

    costs["Google Cloud Run"] = safe_float(
        calculate_google_cloud_run_cost(
            monthly_requests,
            request_duration,
            memory_gb
        ),
        0
    )

    return costs


# ============================================================
# VM BASELINE
# ============================================================

def calculate_vm_baseline():
    """
    Calculate the monthly VM baseline.

    Currently uses Google Compute Engine because it is the
    cheapest evaluated VM in the project's current pricing
    model.

    This can later be expanded to compare multiple VM types.
    """

    vm_cost = safe_float(
        calculate_google_compute_engine_cost(),
        0
    )

    return {
        "provider": "Google Compute Engine",
        "monthly_cost": vm_cost
    }


# ============================================================
# VARIABLE COST ESTIMATION
# ============================================================

def calculate_variable_cost_per_request(
    cost_function,
    request_duration,
    memory_gb,
    sample_requests=100000
):
    """
    Estimate the variable serverless cost per request.

    We calculate the cost for a reference workload and
    derive a cost/request from that result.

    This is a pricing-model calculation, not a measurement
    of actual cloud execution performance.
    """

    sample_requests = max(
        sample_requests,
        1
    )

    total_cost = safe_float(
        cost_function(
            sample_requests,
            request_duration,
            memory_gb
        ),
        0
    )

    return total_cost / sample_requests


# ============================================================
# BREAK-EVEN CALCULATION
# ============================================================

def calculate_break_even_requests(
    vm_monthly_cost,
    cost_function,
    request_duration,
    memory_gb
):
    """
    Calculate the approximate monthly request volume at which
    serverless cost equals VM cost.

    Formula:

        Break-even requests =
            VM monthly cost /
            Serverless variable cost per request
    """

    vm_monthly_cost = safe_float(
        vm_monthly_cost,
        0
    )

    if vm_monthly_cost <= 0:
        return None

    cost_per_request = (
        calculate_variable_cost_per_request(
            cost_function,
            request_duration,
            memory_gb
        )
    )

    if cost_per_request <= 0:
        return None

    break_even = (
        vm_monthly_cost /
        cost_per_request
    )

    if not math.isfinite(break_even):
        return None

    return int(
        math.ceil(break_even)
    )


# ============================================================
# PROVIDER BREAK-EVEN ANALYSIS
# ============================================================

def calculate_provider_break_even(
    provider_name,
    cost_function,
    vm_monthly_cost,
    request_duration,
    memory_gb
):
    """
    Generate complete break-even information for one provider.
    """

    cost_per_request = (
        calculate_variable_cost_per_request(
            cost_function,
            request_duration,
            memory_gb
        )
    )

    break_even_requests = (
        calculate_break_even_requests(
            vm_monthly_cost,
            cost_function,
            request_duration,
            memory_gb
        )
    )

    return {
        "provider": provider_name,
        "vm_baseline_monthly_cost": round(
            vm_monthly_cost,
            4
        ),
        "estimated_cost_per_request": (
            round(
                cost_per_request,
                12
            )
        ),
        "break_even_requests_per_month": (
            break_even_requests
        )
    }


# ============================================================
# CURRENT WORKLOAD COST
# ============================================================

def calculate_current_costs(
    monthly_requests,
    request_duration,
    memory_gb,
    vm_monthly_cost
):
    """
    Calculate the actual estimated costs for the current
    workload.
    """

    serverless_costs = calculate_serverless_costs(
        monthly_requests,
        request_duration,
        memory_gb
    )

    return {
        "serverless": serverless_costs,
        "vm": vm_monthly_cost
    }


# ============================================================
# STRATEGY INTERPRETATION
# ============================================================

def interpret_strategy(
    current_requests,
    break_even_requests,
    serverless_cost,
    vm_cost
):
    """
    Interpret the current workload relative to the
    break-even threshold.
    """

    if break_even_requests is None:

        return {
            "strategy": "Insufficient pricing data",
            "status": "unknown",
            "message": (
                "A break-even point could not be calculated "
                "from the available pricing data."
            )
        }

    if current_requests < break_even_requests:

        return {
            "strategy": "Serverless",
            "status": "below_break_even",
            "message": (
                "The current workload is below the "
                "serverless-to-VM break-even point. "
                "Under the current pricing model, "
                "serverless is economically preferable."
            )
        }

    elif current_requests > break_even_requests:

        return {
            "strategy": "VM",
            "status": "above_break_even",
            "message": (
                "The current workload is above the "
                "serverless-to-VM break-even point. "
                "Under the current pricing model, "
                "the VM is economically preferable."
            )
        }

    else:

        return {
            "strategy": "Near break-even",
            "status": "at_break_even",
            "message": (
                "The current workload is approximately "
                "at the break-even point."
            )
        }


# ============================================================
# WORKLOAD TRANSITION ANALYSIS
# ============================================================

def generate_transition_points(
    vm_cost,
    request_duration,
    memory_gb
):
    """
    Generate important request-volume thresholds.

    These thresholds are useful for the Scenario Simulator
    and frontend visualization.

    They are calculated from the current pricing model.
    """

    provider_functions = {

        "AWS Lambda":
            calculate_aws_lambda_cost,

        "Azure Functions":
            calculate_azure_functions_cost,

        "Google Cloud Run":
            calculate_google_cloud_run_cost
    }

    transition_points = {}

    for provider, function in provider_functions.items():

        break_even = calculate_break_even_requests(
            vm_cost,
            function,
            request_duration,
            memory_gb
        )

        transition_points[provider] = break_even

    return transition_points


# ============================================================
# MAIN BREAK-EVEN ANALYSIS
# ============================================================

def run_break_even_analysis(workload=None):
    """
    Run complete break-even analysis.
    """

    (
        monthly_requests,
        request_duration,
        memory_gb
    ) = get_workload_values(
        workload
    )

    print("\n")
    print("=" * 70)
    print("              BREAK-EVEN ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # Workload
    # --------------------------------------------------------

    print("\nCurrent workload")
    print("-" * 70)

    print(
        f"Monthly requests: {monthly_requests:,}"
    )

    print(
        f"Average request duration: "
        f"{request_duration} seconds"
    )

    print(
        f"Memory: {memory_gb} GB"
    )

    # --------------------------------------------------------
    # VM baseline
    # --------------------------------------------------------

    vm_baseline = calculate_vm_baseline()

    vm_provider = vm_baseline["provider"]
    vm_monthly_cost = vm_baseline["monthly_cost"]

    print("\n")
    print("=" * 60)
    print("VM PRICING")
    print("=" * 60)

    print(
        f"\n{vm_provider}: "
        f"${vm_monthly_cost:.2f}/month"
    )

    print(
        f"\nCheapest VM: {vm_provider}"
    )

    print(
        f"VM monthly cost: "
        f"${vm_monthly_cost:.2f}"
    )

    # --------------------------------------------------------
    # Provider functions
    # --------------------------------------------------------

    provider_functions = {

        "AWS Lambda":
            calculate_aws_lambda_cost,

        "Azure Functions":
            calculate_azure_functions_cost,

        "Google Cloud Run":
            calculate_google_cloud_run_cost
    }

    # --------------------------------------------------------
    # Break-even values
    # --------------------------------------------------------

    break_even_results = {}

    print("\n")
    print("=" * 70)
    print("BREAK-EVEN REQUEST VOLUME")
    print("=" * 70)

    print(
        f"\nVM baseline: {vm_provider}"
    )

    print(
        f"VM monthly cost: "
        f"${vm_monthly_cost:.2f}"
    )

    for provider, cost_function in provider_functions.items():

        result = calculate_provider_break_even(
            provider,
            cost_function,
            vm_monthly_cost,
            request_duration,
            memory_gb
        )

        break_even_results[provider] = result

        break_even = result[
            "break_even_requests_per_month"
        ]

        print(f"\n{provider}:")

        if break_even is None:

            print(
                "  Break-even: unavailable"
            )

        else:

            print(
                f"  Break-even: "
                f"{break_even:,} requests/month"
            )

    # --------------------------------------------------------
    # Current costs
    # --------------------------------------------------------

    current_costs = calculate_current_costs(
        monthly_requests,
        request_duration,
        memory_gb,
        vm_monthly_cost
    )

    print("\n")
    print("=" * 70)
    print("CURRENT WORKLOAD COST")
    print("=" * 70)

    print(
        f"\nCurrent requests: "
        f"{monthly_requests:,}"
    )

    for provider, cost in (
        current_costs["serverless"].items()
    ):

        print(
            f"\n{provider}: "
            f"${cost:.4f}/month"
        )

    print(
        f"\nVM: "
        f"${vm_monthly_cost:.2f}/month"
    )

    # --------------------------------------------------------
    # Cheapest serverless
    # --------------------------------------------------------

    valid_serverless = {
        provider: cost
        for provider, cost
        in current_costs["serverless"].items()
        if cost > 0
    }

    if valid_serverless:

        cheapest_serverless = min(
            valid_serverless,
            key=valid_serverless.get
        )

        cheapest_serverless_cost = (
            valid_serverless[
                cheapest_serverless
            ]
        )

    else:

        cheapest_serverless = None
        cheapest_serverless_cost = None

    # --------------------------------------------------------
    # Strategy
    # --------------------------------------------------------

    if (
        cheapest_serverless is not None
        and cheapest_serverless_cost is not None
        and vm_monthly_cost > 0
    ):

        if (
            cheapest_serverless_cost
            < vm_monthly_cost
        ):

            current_strategy = (
                "Serverless"
            )

            recommended_provider = (
                cheapest_serverless
            )

            recommended_cost = (
                cheapest_serverless_cost
            )

        else:

            current_strategy = "VM"

            recommended_provider = (
                vm_provider
            )

            recommended_cost = (
                vm_monthly_cost
            )

    else:

        current_strategy = (
            "Insufficient pricing data"
        )

        recommended_provider = None
        recommended_cost = None

    print("\n")
    print("=" * 70)
    print("STRATEGY DECISION")
    print("=" * 70)

    print(
        f"\nCurrent strategy: "
        f"{current_strategy}"
    )

    print(
        f"Recommended provider: "
        f"{recommended_provider}"
    )

    if recommended_cost is not None:

        print(
            f"Estimated monthly cost: "
            f"${recommended_cost:.4f}"
        )

    # --------------------------------------------------------
    # Provider interpretations
    # --------------------------------------------------------

    interpretations = {}

    print("\n")
    print("=" * 70)
    print("BREAK-EVEN INTERPRETATION")
    print("=" * 70)

    for provider, result in (
        break_even_results.items()
    ):

        break_even = result[
            "break_even_requests_per_month"
        ]

        current_provider_cost = (
            current_costs[
                "serverless"
            ].get(
                provider,
                0
            )
        )

        interpretation = interpret_strategy(
            monthly_requests,
            break_even,
            current_provider_cost,
            vm_monthly_cost
        )

        interpretations[provider] = interpretation

        print(f"\n{provider}:")

        print(
            f"  Current strategy: "
            f"{interpretation['strategy']}"
        )

        print(
            f"  Status: "
            f"{interpretation['status']}"
        )

        print(
            f"  {interpretation['message']}"
        )

    # --------------------------------------------------------
    # Transition points
    # --------------------------------------------------------

    transition_points = (
        generate_transition_points(
            vm_monthly_cost,
            request_duration,
            memory_gb
        )
    )

    print("\n")
    print("=" * 70)
    print("DEPLOYMENT TRANSITION THRESHOLDS")
    print("=" * 70)

    for provider, threshold in (
        transition_points.items()
    ):

        if threshold is not None:

            print(
                f"\n{provider}:"
            )

            print(
                f"  Approximately "
                f"{threshold:,} requests/month"
            )

            print(
                "  → Above this threshold, "
                "the VM becomes economically competitive "
                "under the current cost model."
            )

    # --------------------------------------------------------
    # Final explanation
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("THRESHOLD INTERPRETATION")
    print("=" * 70)

    print(
        "\nThe break-even point is not a prediction."
    )

    print(
        "It is a cost-model threshold calculated "
        "from the current workload and pricing assumptions."
    )

    print(
        "\nActual production performance may differ because "
        "of cold starts, autoscaling behavior, networking, "
        "regional pricing, free tiers, traffic patterns "
        "and other infrastructure factors."
    )

    print(
        "\nThe Scenario Simulator can use these thresholds "
        "to evaluate how the deployment recommendation "
        "changes as workload volume increases."
    )

    print("\n")
    print("=" * 70)
    print("           BREAK-EVEN ANALYSIS COMPLETE")
    print("=" * 70)

    # ========================================================
    # RETURN STRUCTURE
    # ========================================================

    return {

        "workload": {
            "request_volume": monthly_requests,
            "request_duration": request_duration,
            "memory_gb": memory_gb
        },

        "vm_baseline": {
            "provider": vm_provider,
            "monthly_cost": vm_monthly_cost
        },

        "serverless_costs": (
            current_costs["serverless"]
        ),

        "break_even": break_even_results,

        "interpretations": interpretations,

        "transition_points": transition_points,

        "current_strategy": current_strategy,

        "recommended_provider": (
            recommended_provider
        ),

        "recommended_cost": (
            recommended_cost
        ),

        "cheapest_serverless": (
            cheapest_serverless
        ),

        "cheapest_serverless_cost": (
            cheapest_serverless_cost
        )
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_workload = {

        "traffic_pattern": "steady",

        "request_volume": 100000,

        "latency": "standard",

        "request_duration": 0.2,

        "concurrency": 10,

        "memory_gb": 1
    }

    result = run_break_even_analysis(
        test_workload
    )

    print("\n")
    print("=" * 70)
    print("FINAL BREAK-EVEN RESULT")
    print("=" * 70)

    print(
        "\nCurrent Strategy:",
        result["current_strategy"]
    )

    print(
        "Recommended Provider:",
        result["recommended_provider"]
    )

    if result["recommended_cost"] is not None:

        print(
            "Estimated Monthly Cost:",
            f"${result['recommended_cost']:.4f}"
        )

    print(
        "\nTransition Points:"
    )

    for provider, threshold in (
        result["transition_points"].items()
    ):

        if threshold is not None:

            print(
                f"- {provider}: "
                f"{threshold:,} requests/month"
            )