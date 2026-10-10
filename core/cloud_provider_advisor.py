"""
cloud_provider_advisor.py

Evidence-based provider compatibility analysis.

Providers:
    - AWS Lambda
    - Azure Functions
    - Google Cloud Run

This module does NOT assign artificial provider scores.
It checks the workload against documented service capabilities
and limits instead.

The result can later be combined with:
    - real pricing
    - local ML benchmark
    - break-even analysis
    - actual cloud benchmark results
"""

import math


# ============================================================
# PROVIDER LIMITS / CAPABILITIES
# ============================================================

AWS_LAMBDA = {
    "name": "AWS Lambda",
    "min_memory_mb": 128,
    "max_memory_mb": 10240,
    "max_timeout_seconds": 900,
    "short_lived_compute": True,
}


AZURE_FUNCTIONS = {
    "name": "Azure Functions",
    "memory_options_gb": [0.5, 2, 4],
    "max_timeout_seconds": 1800,
    "supports_concurrency_scaling": True,
}


GOOGLE_CLOUD_RUN = {
    "name": "Google Cloud Run",
    "name_short": "Google Cloud Run",
    "max_memory_gb": 32,
    "max_cpu": 8,
    "max_concurrency": 1000,
    "max_timeout_seconds": 3600,
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    """Safely convert a value to float."""

    try:
        number = float(value)

        if not math.isfinite(number):
            return default

        return number

    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    """Safely convert a value to integer."""

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def get_workload_values(workload):
    """
    Extract and validate workload information.

    Expected workload:

    {
        "traffic_pattern": "steady",
        "request_volume": 100000,
        "latency": "standard",
        "request_duration": 0.2,
        "concurrency": 10,
        "memory_gb": 1
    }
    """

    if workload is None:
        workload = {}

    traffic_pattern = str(
        workload.get("traffic_pattern", "steady")
    ).lower()

    request_volume = safe_int(
        workload.get("request_volume", 100000),
        100000
    )

    request_duration = safe_float(
        workload.get("request_duration", 0.2),
        0.2
    )

    concurrency = safe_int(
        workload.get("concurrency", 10),
        10
    )

    memory_gb = safe_float(
        workload.get("memory_gb", 1),
        1
    )

    latency = str(
        workload.get("latency", "standard")
    ).lower()

    # Prevent invalid values
    request_volume = max(request_volume, 0)
    request_duration = max(request_duration, 0.0)
    concurrency = max(concurrency, 1)
    memory_gb = max(memory_gb, 0.001)

    return {
        "traffic_pattern": traffic_pattern,
        "request_volume": request_volume,
        "request_duration": request_duration,
        "concurrency": concurrency,
        "memory_gb": memory_gb,
        "latency": latency
    }


def check_result(passed, value, limit=None, unit=""):
    """
    Create a consistent compatibility check result.
    """

    result = {
        "passed": passed,
        "value": value
    }

    if limit is not None:
        result["limit"] = limit

    if unit:
        result["unit"] = unit

    return result


# ============================================================
# AWS LAMBDA ANALYSIS
# ============================================================

def analyze_aws_lambda(workload):
    """
    Analyze workload compatibility with AWS Lambda.
    """

    memory_gb = workload["memory_gb"]
    duration = workload["request_duration"]
    concurrency = workload["concurrency"]
    traffic = workload["traffic_pattern"]

    memory_mb = memory_gb * 1024

    checks = {}
    limitations = []
    warnings = []

    # --------------------------------------------------------
    # Memory
    # --------------------------------------------------------

    memory_passed = (
        AWS_LAMBDA["min_memory_mb"]
        <= memory_mb
        <= AWS_LAMBDA["max_memory_mb"]
    )

    checks["memory"] = check_result(
        memory_passed,
        round(memory_mb, 2),
        AWS_LAMBDA["max_memory_mb"],
        "MB"
    )

    if not memory_passed:
        limitations.append(
            f"Required memory is {memory_mb:.2f} MB, "
            f"while Lambda supports up to "
            f"{AWS_LAMBDA['max_memory_mb']} MB."
        )

    # --------------------------------------------------------
    # Execution duration
    # --------------------------------------------------------

    duration_passed = (
        duration <= AWS_LAMBDA["max_timeout_seconds"]
    )

    checks["execution_duration"] = check_result(
        duration_passed,
        duration,
        AWS_LAMBDA["max_timeout_seconds"],
        "seconds"
    )

    if not duration_passed:
        limitations.append(
            f"Request duration of {duration:.2f} seconds "
            f"exceeds Lambda's maximum execution time "
            f"of {AWS_LAMBDA['max_timeout_seconds']} seconds."
        )

    # --------------------------------------------------------
    # Concurrency
    # --------------------------------------------------------

    checks["concurrency"] = {
        "passed": True,
        "value": concurrency,
        "note": (
            "Lambda supports concurrent executions, "
            "but concurrency limits and scaling behavior "
            "should be monitored."
        )
    }

    if concurrency >= 1000:
        warnings.append(
            "High concurrency workload. Lambda concurrency "
            "limits and scaling behavior should be evaluated "
            "before production deployment."
        )

    # --------------------------------------------------------
    # Traffic pattern
    # --------------------------------------------------------

    checks["traffic_pattern"] = {
        "passed": True,
        "value": traffic,
        "note": (
            "Lambda is designed for event-driven workloads "
            "and automatically scales with demand."
        )
    }

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    compatible = len(limitations) == 0

    if compatible:
        reason = (
            "The workload is within the evaluated AWS Lambda "
            "memory and execution-time limits."
        )
    else:
        reason = (
            "The workload exceeds one or more evaluated "
            "AWS Lambda limits."
        )

    return {
        "compatible": compatible,
        "checks": checks,
        "limitations": limitations,
        "warnings": warnings,
        "reason": reason,
        "recommended_configuration": {
            "memory_mb": max(128, math.ceil(memory_mb)),
            "timeout_seconds": max(1, math.ceil(duration))
        }
    }


# ============================================================
# AZURE FUNCTIONS ANALYSIS
# ============================================================

def analyze_azure_functions(workload):
    """
    Analyze workload compatibility with Azure Functions.
    """

    memory_gb = workload["memory_gb"]
    duration = workload["request_duration"]
    concurrency = workload["concurrency"]
    traffic = workload["traffic_pattern"]

    checks = {}
    limitations = []
    warnings = []

    # --------------------------------------------------------
    # Memory
    # --------------------------------------------------------

    supported_memory = AZURE_FUNCTIONS["memory_options_gb"]

    suitable_memory_options = [
        memory
        for memory in supported_memory
        if memory >= memory_gb
    ]

    memory_passed = len(suitable_memory_options) > 0

    checks["memory"] = {
        "passed": memory_passed,
        "required_gb": memory_gb,
        "supported_options_gb": supported_memory
    }

    if not memory_passed:
        limitations.append(
            f"Required memory of {memory_gb:.2f} GB "
            f"exceeds the evaluated Azure Functions "
            f"memory options."
        )

    # --------------------------------------------------------
    # Execution duration
    # --------------------------------------------------------

    duration_passed = (
        duration <= AZURE_FUNCTIONS["max_timeout_seconds"]
    )

    checks["execution_duration"] = check_result(
        duration_passed,
        duration,
        AZURE_FUNCTIONS["max_timeout_seconds"],
        "seconds"
    )

    if not duration_passed:
        limitations.append(
            f"Request duration of {duration:.2f} seconds "
            f"exceeds the evaluated Azure Functions "
            f"timeout limit of "
            f"{AZURE_FUNCTIONS['max_timeout_seconds']} seconds."
        )

    # --------------------------------------------------------
    # Concurrency
    # --------------------------------------------------------

    checks["concurrency"] = {
        "passed": True,
        "value": concurrency,
        "note": (
            "Azure Functions supports concurrent event "
            "processing and automatic instance scaling."
        )
    }

    if concurrency >= 1000:
        warnings.append(
            "High concurrency workload. Actual concurrency "
            "behavior should be validated with the selected "
            "Azure Functions hosting plan."
        )

    # --------------------------------------------------------
    # Traffic
    # --------------------------------------------------------

    checks["traffic_pattern"] = {
        "passed": True,
        "value": traffic,
        "note": (
            "Azure Functions supports event-driven workloads "
            "and automatic scaling."
        )
    }

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    if memory_passed:
        recommended_memory = min(suitable_memory_options)
    else:
        recommended_memory = None

    compatible = len(limitations) == 0

    if compatible:
        reason = (
            "The workload fits the evaluated Azure Functions "
            "memory and execution-time requirements."
        )
    else:
        reason = (
            "The workload exceeds one or more evaluated "
            "Azure Functions limits."
        )

    return {
        "compatible": compatible,
        "checks": checks,
        "limitations": limitations,
        "warnings": warnings,
        "reason": reason,
        "recommended_configuration": {
            "memory_gb": recommended_memory,
            "timeout_seconds": max(1, math.ceil(duration))
        }
    }


# ============================================================
# GOOGLE CLOUD RUN ANALYSIS
# ============================================================

def analyze_google_cloud_run(workload):
    """
    Analyze workload compatibility with Google Cloud Run.
    """

    memory_gb = workload["memory_gb"]
    duration = workload["request_duration"]
    concurrency = workload["concurrency"]

    checks = {}
    limitations = []
    warnings = []

    # --------------------------------------------------------
    # Memory
    # --------------------------------------------------------

    memory_passed = (
        memory_gb <= GOOGLE_CLOUD_RUN["max_memory_gb"]
    )

    checks["memory"] = check_result(
        memory_passed,
        memory_gb,
        GOOGLE_CLOUD_RUN["max_memory_gb"],
        "GB"
    )

    if not memory_passed:
        limitations.append(
            f"Required memory of {memory_gb:.2f} GB "
            f"exceeds Cloud Run's evaluated maximum of "
            f"{GOOGLE_CLOUD_RUN['max_memory_gb']} GB."
        )

    # --------------------------------------------------------
    # Concurrency
    # --------------------------------------------------------

    concurrency_passed = (
        concurrency <= GOOGLE_CLOUD_RUN["max_concurrency"]
    )

    checks["concurrency"] = check_result(
        concurrency_passed,
        concurrency,
        GOOGLE_CLOUD_RUN["max_concurrency"],
        "requests/instance"
    )

    if not concurrency_passed:
        limitations.append(
            f"Requested concurrency of {concurrency} "
            f"exceeds the evaluated Cloud Run maximum "
            f"of {GOOGLE_CLOUD_RUN['max_concurrency']}."
        )

    # --------------------------------------------------------
    # Request duration
    # --------------------------------------------------------

    duration_passed = (
        duration <= GOOGLE_CLOUD_RUN["max_timeout_seconds"]
    )

    checks["execution_duration"] = check_result(
        duration_passed,
        duration,
        GOOGLE_CLOUD_RUN["max_timeout_seconds"],
        "seconds"
    )

    if not duration_passed:
        limitations.append(
            f"Request duration of {duration:.2f} seconds "
            f"exceeds the evaluated Cloud Run timeout "
            f"limit of {GOOGLE_CLOUD_RUN['max_timeout_seconds']} seconds."
        )

    # --------------------------------------------------------
    # CPU
    # --------------------------------------------------------

    # A simple deployment configuration for the current
    # project. This is a configuration estimate, NOT a
    # provider performance score.

    if memory_gb <= 2:
        recommended_cpu = 1
    elif memory_gb <= 4:
        recommended_cpu = 2
    elif memory_gb <= 8:
        recommended_cpu = 4
    else:
        recommended_cpu = 8

    cpu_passed = (
        recommended_cpu <= GOOGLE_CLOUD_RUN["max_cpu"]
    )

    checks["cpu"] = check_result(
        cpu_passed,
        recommended_cpu,
        GOOGLE_CLOUD_RUN["max_cpu"],
        "vCPU"
    )

    if not cpu_passed:
        limitations.append(
            "The estimated CPU configuration exceeds "
            "the evaluated Cloud Run CPU limit."
        )

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    checks["container_model"] = {
        "passed": True,
        "note": (
            "Cloud Run deploys containerized applications "
            "and automatically scales service instances."
        )
    }

    compatible = len(limitations) == 0

    if compatible:
        reason = (
            "The workload fits the evaluated Google Cloud Run "
            "memory, concurrency and execution-time limits."
        )
    else:
        reason = (
            "The workload exceeds one or more evaluated "
            "Google Cloud Run limits."
        )

    return {
        "compatible": compatible,
        "checks": checks,
        "limitations": limitations,
        "warnings": warnings,
        "reason": reason,
        "recommended_configuration": {
            "memory_gb": memory_gb,
            "cpu": recommended_cpu,
            "timeout_seconds": max(1, math.ceil(duration)),
            "concurrency": min(
                concurrency,
                GOOGLE_CLOUD_RUN["max_concurrency"]
            )
        }
    }


# ============================================================
# MAIN PROVIDER COMPARISON
# ============================================================

def compare_cloud_providers(workload):
    """
    Compare managed/serverless providers using
    evidence-based compatibility checks.

    No artificial provider scores are generated.
    """

    workload = get_workload_values(workload)

    print("\n==============================================")
    print("     PROVIDER COMPATIBILITY ANALYSIS")
    print("==============================================")

    print("\nWorkload:")
    print(
        "Traffic Pattern      :",
        workload["traffic_pattern"]
    )
    print(
        "Monthly Requests     :",
        f"{workload['request_volume']:,}"
    )
    print(
        "Request Duration     :",
        f"{workload['request_duration']:.2f} seconds"
    )
    print(
        "Expected Concurrency :",
        workload["concurrency"]
    )
    print(
        "Memory Requirement   :",
        f"{workload['memory_gb']:.2f} GB"
    )
    print(
        "Latency Requirement  :",
        workload["latency"]
    )

    # --------------------------------------------------------
    # Analyze each provider
    # --------------------------------------------------------

    providers = {
        "AWS Lambda": analyze_aws_lambda(workload),
        "Azure Functions": analyze_azure_functions(workload),
        "Google Cloud Run": analyze_google_cloud_run(workload)
    }

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    for provider_name, result in providers.items():

        print("\n----------------------------------------------")
        print(provider_name)
        print("----------------------------------------------")

        if result["compatible"]:
            print("Compatibility: COMPATIBLE")
        else:
            print("Compatibility: NOT COMPATIBLE")

        print("\nChecks:")

        for check_name, check in result["checks"].items():

            status = (
                "PASS"
                if check.get("passed", False)
                else "FAIL"
            )

            print(
                f"- {check_name}: {status}"
            )

        print("\nReason:")
        print("-", result["reason"])

        if result["limitations"]:
            print("\nLimitations:")

            for limitation in result["limitations"]:
                print("-", limitation)

        if result["warnings"]:
            print("\nWarnings:")

            for warning in result["warnings"]:
                print("-", warning)

        print("\nRecommended Configuration:")

        for key, value in result[
            "recommended_configuration"
        ].items():

            print(
                f"- {key}: {value}"
            )

    # --------------------------------------------------------
    # Compatible providers
    # --------------------------------------------------------

    compatible_providers = [
        provider
        for provider, result in providers.items()
        if result["compatible"]
    ]

    incompatible_providers = [
        provider
        for provider, result in providers.items()
        if not result["compatible"]
    ]

    print("\n==============================================")
    print("COMPATIBLE PROVIDERS")
    print("==============================================")

    if compatible_providers:
        for provider in compatible_providers:
            print("-", provider)
    else:
        print("No provider passed all compatibility checks.")

    print("\n==============================================")
    print("INCOMPATIBLE PROVIDERS")
    print("==============================================")

    if incompatible_providers:
        for provider in incompatible_providers:
            print("-", provider)
    else:
        print("None")

    # --------------------------------------------------------
    # Important:
    #
    # We do NOT select a final provider here.
    #
    # Cost analysis, break-even analysis and actual benchmark
    # results should participate in the final recommendation.
    # --------------------------------------------------------

    print("\n==============================================")
    print("IMPORTANT")
    print("==============================================")

    print(
        "Provider compatibility does not represent "
        "provider performance."
    )

    print(
        "Final provider selection should combine "
        "compatibility, real pricing, break-even analysis "
        "and benchmark results."
    )

    return {
        "workload": workload,
        "providers": providers,
        "compatible_providers": compatible_providers,
        "incompatible_providers": incompatible_providers
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

    result = compare_cloud_providers(test_workload)

    print("\n==============================================")
    print("FINAL COMPATIBILITY RESULT")
    print("==============================================")

    print(
        "\nCompatible Providers:"
    )

    for provider in result["compatible_providers"]:
        print("-", provider)