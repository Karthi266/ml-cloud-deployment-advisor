def analyze_workload(workload=None):

    print("\n===== WORKLOAD ANALYSIS =====")

    # ============================================================
    # STREAMLIT / PROGRAMMATIC MODE
    # ============================================================

    if workload is not None:

        traffic_pattern = workload.get(
            "traffic_pattern",
            "steady"
        )

        request_volume = workload.get(
            "request_volume",
            workload.get(
                "monthly_requests",
                0
            )
        )

        latency = workload.get(
            "latency",
            "standard"
        )

        request_duration = workload.get(
            "request_duration",
            0.0
        )

        concurrency = workload.get(
            "concurrency",
            workload.get(
                "expected_concurrency",
                0
            )
        )

        memory_gb = workload.get(
            "memory_gb",
            1.0
        )

    # ============================================================
    # COMMAND-LINE MODE
    # ============================================================

    else:

        traffic_pattern = input(
            "Enter traffic pattern (steady/bursty): "
        ).strip().lower()

        request_volume = int(
            input(
                "Enter expected monthly request volume: "
            )
        )

        latency = input(
            "Enter latency requirement (critical/standard): "
        ).strip().lower()

        request_duration = float(
            input(
                "Enter average request duration (seconds): "
            )
        )

        concurrency = int(
            input(
                "Enter expected concurrent requests: "
            )
        )

        memory_gb = float(
            input(
                "Enter required memory (GB): "
            )
        )

    # ============================================================
    # BASIC VALIDATION
    # ============================================================

    if traffic_pattern not in (
        "steady",
        "bursty"
    ):

        raise ValueError(
            "Traffic pattern must be 'steady' or 'bursty'."
        )

    if latency not in (
        "critical",
        "standard"
    ):

        raise ValueError(
            "Latency requirement must be 'critical' "
            "or 'standard'."
        )

    if request_volume <= 0:

        raise ValueError(
            "Monthly request volume must be greater than 0."
        )

    if request_duration <= 0:

        raise ValueError(
            "Request duration must be greater than 0."
        )

    if concurrency <= 0:

        raise ValueError(
            "Concurrency must be greater than 0."
        )

    if memory_gb <= 0:

        raise ValueError(
            "Memory must be greater than 0."
        )

    # ============================================================
    # DERIVED WORKLOAD METRICS
    # ============================================================

    monthly_seconds = (
        request_volume
        * request_duration
    )

    average_requests_per_second = (
        request_volume
        / (30 * 24 * 60 * 60)
    )

    estimated_concurrent_load = (
        average_requests_per_second
        * request_duration
    )

    # ============================================================
    # WORKLOAD CLASSIFICATION
    # ============================================================

    if traffic_pattern == "bursty":

        traffic_behavior = (
            "Variable traffic with sudden workload increases"
        )

    else:

        traffic_behavior = (
            "Relatively stable traffic distribution"
        )

    if latency == "critical":

        latency_behavior = (
            "Low-latency response is important"
        )

    else:

        latency_behavior = (
            "Standard latency is acceptable"
        )

    # ============================================================
    # DISPLAY
    # ============================================================

    print("\n===== WORKLOAD DETAILS =====")

    print(
        "Traffic pattern:",
        traffic_pattern
    )

    print(
        "Monthly requests:",
        request_volume
    )

    print(
        "Latency requirement:",
        latency
    )

    print(
        "Average request duration:",
        request_duration,
        "seconds"
    )

    print(
        "Expected concurrency:",
        concurrency
    )

    print(
        "Required memory:",
        memory_gb,
        "GB"
    )

    print(
        "Estimated average requests/second:",
        round(
            average_requests_per_second,
            4
        )
    )

    print(
        "Estimated concurrent load:",
        round(
            estimated_concurrent_load,
            4
        )
    )

    # ============================================================
    # RESULT
    # ============================================================

    return {

        # Original workload fields
        "traffic_pattern":
            traffic_pattern,

        "request_volume":
            request_volume,

        "latency":
            latency,

        "request_duration":
            request_duration,

        "concurrency":
            concurrency,

        "memory_gb":
            memory_gb,

        # Aliases used by the Streamlit application
        "monthly_requests":
            request_volume,

        "expected_concurrency":
            concurrency,

        # Derived metrics
        "monthly_compute_seconds":
            monthly_seconds,

        "average_requests_per_second":
            average_requests_per_second,

        "estimated_concurrent_load":
            estimated_concurrent_load,

        # Interpretation
        "traffic_behavior":
            traffic_behavior,

        "latency_behavior":
            latency_behavior
    }


# ============================================================
# COMMAND-LINE EXECUTION
# ============================================================

if __name__ == "__main__":

    analyze_workload()