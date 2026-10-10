# ==========================================================
# SMART CLOUD DEPLOYMENT ADVISOR
# WORKLOAD SCENARIO SIMULATOR
#
# Purpose:
# Compare multiple workloads using one pricing refresh.
#
# Pricing is retrieved ONCE and reused across all scenarios.
# ==========================================================

from contextlib import redirect_stdout
from io import StringIO

from pricing.pricing_cache import load_all_pricing
from core.cloud_provider_advisor import compare_cloud_providers


# ==========================================================
# CONFIGURATION
# ==========================================================

MONTHLY_HOURS = 730


# ==========================================================
# PREDEFINED WORKLOAD SCENARIOS
# ==========================================================

SCENARIOS = {

    "Low Traffic": {
        "traffic_pattern": "steady",
        "monthly_requests": 10000,
        "request_duration": 0.2,
        "expected_concurrency": 5,
        "memory_gb": 1.0,
        "latency": "standard"
    },

    "Normal Traffic": {
        "traffic_pattern": "steady",
        "monthly_requests": 100000,
        "request_duration": 0.2,
        "expected_concurrency": 10,
        "memory_gb": 1.0,
        "latency": "standard"
    },

    "High Traffic": {
        "traffic_pattern": "steady",
        "monthly_requests": 1000000,
        "request_duration": 0.5,
        "expected_concurrency": 50,
        "memory_gb": 1.0,
        "latency": "standard"
    },

    "Bursty Traffic": {
        "traffic_pattern": "bursty",
        "monthly_requests": 500000,
        "request_duration": 0.2,
        "expected_concurrency": 50,
        "memory_gb": 1.0,
        "latency": "standard"
    },

    "High Concurrency": {
        "traffic_pattern": "bursty",
        "monthly_requests": 1000000,
        "request_duration": 0.5,
        "expected_concurrency": 200,
        "memory_gb": 2.0,
        "latency": "standard"
    }
}


# ==========================================================
# SAFE NUMBER HELPER
# ==========================================================

def safe_float(value, default=0.0):

    try:
        return float(value)

    except (TypeError, ValueError):

        return float(default)


# ==========================================================
# AWS LAMBDA COST
# ==========================================================

def calculate_aws_lambda_cost(workload, pricing):

    requests = safe_float(
        workload["monthly_requests"]
    )

    duration = safe_float(
        workload["request_duration"]
    )

    memory = safe_float(
        workload["memory_gb"]
    )

    request_price = safe_float(
        pricing["request_price_per_request"]
    )

    compute_price = safe_float(
        pricing["compute_price_per_gb_second"]
    )

    request_cost = (
        requests *
        request_price
    )

    compute_seconds = (
        requests *
        duration
    )

    compute_cost = (
        compute_seconds *
        memory *
        compute_price
    )

    total_cost = (
        request_cost +
        compute_cost
    )

    return total_cost


# ==========================================================
# AZURE FUNCTIONS COST
# ==========================================================

def calculate_azure_functions_cost(
    workload,
    pricing
):

    requests = safe_float(
        workload["monthly_requests"]
    )

    duration = safe_float(
        workload["request_duration"]
    )

    memory = safe_float(
        workload["memory_gb"]
    )

    execution_price = safe_float(
        pricing["execution_price_per_10"]
    )

    execution_time_price = safe_float(
        pricing[
            "execution_time_price_per_gb_second"
        ]
    )

    execution_cost = (
        requests /
        10 *
        execution_price
    )

    execution_seconds = (
        requests *
        duration
    )

    execution_time_cost = (
        execution_seconds *
        memory *
        execution_time_price
    )

    total_cost = (
        execution_cost +
        execution_time_cost
    )

    return total_cost


# ==========================================================
# GOOGLE CLOUD RUN COST
# ==========================================================

def calculate_google_cloud_run_cost(
    workload,
    pricing
):

    requests = safe_float(
        workload["monthly_requests"]
    )

    duration = safe_float(
        workload["request_duration"]
    )

    memory = safe_float(
        workload["memory_gb"]
    )

    cpu_price = safe_float(
        pricing[
            "cpu_price_per_vcpu_second"
        ]
    )

    memory_price = safe_float(
        pricing[
            "memory_price_per_gib_second"
        ]
    )

    request_price = safe_float(
        pricing[
            "request_price_per_million"
        ]
    )

    cpu_seconds = (
        requests *
        duration
    )

    cpu_cost = (
        cpu_seconds *
        cpu_price
    )

    memory_seconds = (
        requests *
        duration
    )

    memory_cost = (
        memory_seconds *
        memory *
        memory_price
    )

    request_cost = (
        requests /
        1000000 *
        request_price
    )

    total_cost = (
        cpu_cost +
        memory_cost +
        request_cost
    )

    return total_cost


# ==========================================================
# AZURE VM COST
# ==========================================================

def calculate_azure_vm_cost(pricing):

    hourly_price = safe_float(
        pricing["price_per_hour"]
    )

    return (
        hourly_price *
        MONTHLY_HOURS
    )


# ==========================================================
# GOOGLE COMPUTE ENGINE COST
# ==========================================================

def calculate_google_vm_cost(pricing):

    hourly_price = safe_float(
        pricing["price_per_hour"]
    )

    return (
        hourly_price *
        MONTHLY_HOURS
    )


# ==========================================================
# SERVERLESS COSTS
# ==========================================================

def calculate_serverless_costs(
    workload,
    pricing
):

    return {

        "AWS Lambda":
            calculate_aws_lambda_cost(
                workload,
                pricing["aws_lambda"]
            ),

        "Azure Functions":
            calculate_azure_functions_cost(
                workload,
                pricing["azure_functions"]
            ),

        "Google Cloud Run":
            calculate_google_cloud_run_cost(
                workload,
                pricing["google_cloud_run"]
            )
    }


# ==========================================================
# VM COSTS
# ==========================================================

def calculate_vm_costs(pricing):

    return {

        "Azure VM":
            calculate_azure_vm_cost(
                pricing["azure_vm"]
            ),

        "Google Compute Engine":
            calculate_google_vm_cost(
                pricing["google_vm"]
            )
    }


# ==========================================================
# FIND CHEAPEST
# ==========================================================

def find_cheapest(costs):

    available = {

        provider: cost

        for provider, cost
        in costs.items()

        if cost is not None
    }

    if not available:

        return None, None

    provider = min(
        available,
        key=available.get
    )

    return (
        provider,
        available[provider]
    )


# ==========================================================
# BREAK-EVEN CALCULATION
#
# Current model:
# fixed VM monthly cost /
# serverless variable cost per request
#
# Task 2 will improve this model.
# ==========================================================

def calculate_break_even(
    workload,
    serverless_pricing,
    vm_monthly_costs
):

    requests = safe_float(
        workload["monthly_requests"]
    )

    duration = safe_float(
        workload["request_duration"]
    )

    memory = safe_float(
        workload["memory_gb"]
    )

    if requests <= 0:

        return {}

    results = {}

    # ------------------------------------------------------
    # AWS
    # ------------------------------------------------------

    aws_request_price = safe_float(
        serverless_pricing["aws_lambda"][
            "request_price_per_request"
        ]
    )

    aws_compute_price = safe_float(
        serverless_pricing["aws_lambda"][
            "compute_price_per_gb_second"
        ]
    )

    aws_cost_per_request = (

        aws_request_price +

        (
            duration *
            memory *
            aws_compute_price
        )
    )

    if aws_cost_per_request > 0:

        results["AWS Lambda"] = (

            vm_monthly_costs[
                "Google Compute Engine"
            ]

            /
            aws_cost_per_request
        )

    # ------------------------------------------------------
    # AZURE
    # ------------------------------------------------------

    azure_execution_price = safe_float(
        serverless_pricing[
            "azure_functions"
        ][
            "execution_price_per_10"
        ]
    )

    azure_time_price = safe_float(
        serverless_pricing[
            "azure_functions"
        ][
            "execution_time_price_per_gb_second"
        ]
    )

    azure_cost_per_request = (

        azure_execution_price / 10

        +

        (
            duration *
            memory *
            azure_time_price
        )
    )

    if azure_cost_per_request > 0:

        results["Azure Functions"] = (

            vm_monthly_costs[
                "Google Compute Engine"
            ]

            /
            azure_cost_per_request
        )

    # ------------------------------------------------------
    # GOOGLE CLOUD RUN
    # ------------------------------------------------------

    google_cpu_price = safe_float(
        serverless_pricing[
            "google_cloud_run"
        ][
            "cpu_price_per_vcpu_second"
        ]
    )

    google_memory_price = safe_float(
        serverless_pricing[
            "google_cloud_run"
        ][
            "memory_price_per_gib_second"
        ]
    )

    google_request_price = safe_float(
        serverless_pricing[
            "google_cloud_run"
        ][
            "request_price_per_million"
        ]
    )

    google_cost_per_request = (

        duration *
        google_cpu_price

        +

        (
            duration *
            memory *
            google_memory_price
        )

        +

        (
            google_request_price /
            1000000
        )
    )

    if google_cost_per_request > 0:

        results["Google Cloud Run"] = (

            vm_monthly_costs[
                "Google Compute Engine"
            ]

            /
            google_cost_per_request
        )

    return results


# ==========================================================
# PROVIDER COMPATIBILITY
# ==========================================================

def get_compatibility(workload):

    try:

        # The compatibility engine does not require
        # pricing retrieval.

        with redirect_stdout(StringIO()):

            result = compare_cloud_providers(
                workload
            )

        return result

    except Exception as error:

        return {

            "error": str(error),

            "compatible_providers": [],

            "incompatible_providers": [],

            "providers": {}
        }


# ==========================================================
# RUN ONE SCENARIO
# ==========================================================

def run_scenario(
    scenario_name,
    workload,
    pricing
):

    print()
    print("=" * 70)
    print(
        f"SCENARIO: {scenario_name}"
    )
    print("=" * 70)

    # ------------------------------------------------------
    # WORKLOAD
    # ------------------------------------------------------

    print()
    print("WORKLOAD")
    print("-" * 70)

    print(
        "Traffic pattern:",
        workload["traffic_pattern"]
    )

    print(
        "Monthly requests:",
        f"{workload['monthly_requests']:,}"
    )

    print(
        "Request duration:",
        f"{workload['request_duration']} seconds"
    )

    print(
        "Concurrency:",
        workload["expected_concurrency"]
    )

    print(
        "Memory:",
        f"{workload['memory_gb']} GB"
    )

    # ------------------------------------------------------
    # COMPATIBILITY
    # ------------------------------------------------------

    compatibility = get_compatibility(
        workload
    )

    compatible = compatibility.get(
        "compatible_providers",
        []
    )

    # ------------------------------------------------------
    # COSTS
    # ------------------------------------------------------

    serverless_costs = (
        calculate_serverless_costs(
            workload,
            pricing
        )
    )

    vm_costs = (
        calculate_vm_costs(
            pricing
        )
    )

    # ------------------------------------------------------
    # FILTER COMPATIBLE SERVERLESS
    # ------------------------------------------------------

    compatible_serverless = {

        provider: cost

        for provider, cost
        in serverless_costs.items()

        if provider in compatible
    }

    # If compatibility information is unavailable,
    # retain all serverless providers.

    if not compatible:

        compatible_serverless = (
            serverless_costs
        )

    # ------------------------------------------------------
    # CHEAPEST OPTIONS
    # ------------------------------------------------------

    cheapest_serverless, cheapest_serverless_cost = (
        find_cheapest(
            compatible_serverless
        )
    )

    cheapest_vm, cheapest_vm_cost = (
        find_cheapest(
            vm_costs
        )
    )

    # ------------------------------------------------------
    # STRATEGY
    # ------------------------------------------------------

    if (

        cheapest_serverless_cost is not None

        and

        cheapest_vm_cost is not None
    ):

        if (
            cheapest_vm_cost
            <
            cheapest_serverless_cost
        ):

            strategy = "Self-Managed VM"

            provider = cheapest_vm

            recommended_cost = (
                cheapest_vm_cost
            )

        else:

            strategy = "Managed / Serverless"

            provider = cheapest_serverless

            recommended_cost = (
                cheapest_serverless_cost
            )

    elif cheapest_serverless_cost is not None:

        strategy = "Managed / Serverless"

        provider = cheapest_serverless

        recommended_cost = (
            cheapest_serverless_cost
        )

    elif cheapest_vm_cost is not None:

        strategy = "Self-Managed VM"

        provider = cheapest_vm

        recommended_cost = (
            cheapest_vm_cost
        )

    else:

        strategy = "Unavailable"

        provider = None

        recommended_cost = None

    # ------------------------------------------------------
    # BREAK-EVEN
    # ------------------------------------------------------

    break_even = calculate_break_even(
        workload,
        pricing,
        vm_costs
    )

    # ------------------------------------------------------
    # OUTPUT
    # ------------------------------------------------------

    print()
    print("SERVERLESS COST")
    print("-" * 70)

    for provider_name, cost in (
        serverless_costs.items()
    ):

        print(
            f"{provider_name:<25}"
            f"${cost:.4f}/month"
        )

    print()
    print("VM COST")
    print("-" * 70)

    for provider_name, cost in (
        vm_costs.items()
    ):

        print(
            f"{provider_name:<25}"
            f"${cost:.2f}/month"
        )

    print()
    print("RECOMMENDATION")
    print("-" * 70)

    print(
        "Strategy:",
        strategy
    )

    print(
        "Provider:",
        provider
    )

    if recommended_cost is not None:

        print(
            "Monthly cost:",
            f"${recommended_cost:.4f}"
        )

    # ------------------------------------------------------
    # REASON
    # ------------------------------------------------------

    if (

        cheapest_serverless_cost is not None

        and

        cheapest_vm_cost is not None
    ):

        if (
            cheapest_serverless_cost
            <
            cheapest_vm_cost
        ):

            reason = (
                "The lowest-cost compatible "
                "serverless option is cheaper "
                "than the VM baseline for this "
                "workload."
            )

        else:

            reason = (
                "The VM baseline is cheaper "
                "than the compatible serverless "
                "options for this workload."
            )

    else:

        reason = (
            "The recommendation is based on "
            "the available compatible pricing "
            "options."
        )

    print(
        "Reason:",
        reason
    )

    print()
    print("BREAK-EVEN")
    print("-" * 70)

    for provider_name, value in (
        break_even.items()
    ):

        print(
            f"{provider_name:<25}"
            f"{value:,.0f} requests/month"
        )

    return {

        "scenario": scenario_name,

        "workload": workload,

        "compatibility": compatibility,

        "serverless": serverless_costs,

        "vm": vm_costs,

        "break_even": break_even,

        "strategy": strategy,

        "provider": provider,

        "recommended_cost": recommended_cost,

        "reason": reason
    }


# ==========================================================
# RUN ALL SCENARIOS
# ==========================================================

def run_all_scenarios():

    print()
    print("=" * 70)
    print("SMART CLOUD DEPLOYMENT ADVISOR")
    print("WORKLOAD SCENARIO SIMULATOR")
    print("=" * 70)

    print()
    print(
        "Initializing pricing..."
    )

    # ======================================================
    # IMPORTANT:
    # PRICING IS LOADED ONLY ONCE
    # ======================================================

    pricing = load_all_pricing()

    results = []

    print()
    print(
        "Running predefined workload scenarios..."
    )

    # ======================================================
    # RUN SCENARIOS
    # ======================================================

    for scenario_name, workload in (
        SCENARIOS.items()
    ):

        result = run_scenario(
            scenario_name,
            workload,
            pricing
        )

        results.append(
            result
        )

    # ======================================================
    # SUMMARY
    # ======================================================

    print()
    print("=" * 70)
    print("SCENARIO COMPARISON")
    print("=" * 70)

    for result in results:

        print()
        print(
            f"{result['scenario']}:"
        )

        print(
            "  Requests:",
            f"{result['workload']['monthly_requests']:,}"
        )

        print(
            "  Strategy:",
            result["strategy"]
        )

        print(
            "  Provider:",
            result["provider"]
        )

        if result["recommended_cost"] is not None:

            print(
                "  Cost:",
                f"${result['recommended_cost']:.4f}/month"
            )

    print()
    print("=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Cloud pricing was retrieved once "
        "and reused across all scenarios."
    )

    return results


# ==========================================================
# PROGRAM ENTRY
# ==========================================================

if __name__ == "__main__":

    run_all_scenarios()