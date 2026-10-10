import time
import statistics
from concurrent.futures import ThreadPoolExecutor


# ==========================================================
# BENCHMARK CONFIGURATION
# ==========================================================

DEFAULT_REQUESTS = 1000
DEFAULT_CONCURRENCY = 10


# ==========================================================
# SAMPLE MODEL INFERENCE
# ==========================================================

def sample_inference(model, sample_input):

    """
    Runs one ML model prediction.

    The benchmark accepts a single input such as:

        "Congratulations! You won a prize."

    The input is converted into the format expected by
    scikit-learn models:

        ["Congratulations! You won a prize."]
    """

    # ------------------------------------------------------
    # If a list/tuple is already provided, normalize it.
    # ------------------------------------------------------

    if isinstance(sample_input, (list, tuple)):

        if len(sample_input) == 0:

            raise ValueError(
                "sample_input cannot be empty."
            )

        # If it is already a list containing strings,
        # use it directly.
        model_input = list(sample_input)

    else:

        # Normal case:
        # Convert a single input into a list.
        model_input = [sample_input]


    return model.predict(
        model_input
    )


# ==========================================================
# PERCENTILE CALCULATION
# ==========================================================

def calculate_percentile(
    values,
    percentile
):

    if not values:

        return 0.0


    sorted_values = sorted(
        values
    )


    index = (
        (len(sorted_values) - 1)
        * percentile
        / 100
    )


    lower = int(index)

    upper = min(
        lower + 1,
        len(sorted_values) - 1
    )


    weight = (
        index - lower
    )


    return (
        sorted_values[lower]
        * (1 - weight)
        +
        sorted_values[upper]
        * weight
    )


# ==========================================================
# SINGLE REQUEST
# ==========================================================

def execute_request(
    model,
    sample_input
):

    start_time = time.perf_counter()


    try:

        sample_inference(
            model,
            sample_input
        )


        end_time = (
            time.perf_counter()
        )


        latency = (
            end_time
            - start_time
        )


        return {

            "success":
                True,

            "latency":
                latency,

            "error":
                None
        }


    except Exception as error:

        end_time = (
            time.perf_counter()
        )


        latency = (
            end_time
            - start_time
        )


        return {

            "success":
                False,

            "latency":
                latency,

            "error":
                str(error)
        }


# ==========================================================
# BENCHMARK ENGINE
# ==========================================================

def run_benchmark(
    model,
    sample_input,
    total_requests=DEFAULT_REQUESTS,
    concurrency=DEFAULT_CONCURRENCY
):

    print()
    print("=" * 65)
    print("                 ML MODEL BENCHMARK")
    print("=" * 65)


    print()
    print(
        "Benchmark configuration"
    )

    print("-" * 65)


    print(
        "Total requests:",
        f"{total_requests:,}"
    )

    print(
        "Concurrency:",
        concurrency
    )


    # ======================================================
    # VALIDATION
    # ======================================================

    if total_requests <= 0:

        raise ValueError(
            "total_requests must be greater than zero."
        )


    if concurrency <= 0:

        raise ValueError(
            "concurrency must be greater than zero."
        )


    if model is None:

        raise ValueError(
            "Model cannot be None."
        )


    if sample_input is None:

        raise ValueError(
            "sample_input cannot be None."
        )


    # ======================================================
    # BENCHMARK START
    # ======================================================

    benchmark_start = (
        time.perf_counter()
    )


    results = []


    # ======================================================
    # PARALLEL REQUEST EXECUTION
    # ======================================================

    with ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:

        futures = [

            executor.submit(
                execute_request,
                model,
                sample_input
            )

            for _ in range(
                total_requests
            )
        ]


        for future in futures:

            results.append(
                future.result()
            )


    # ======================================================
    # BENCHMARK END
    # ======================================================

    benchmark_end = (
        time.perf_counter()
    )


    total_time = (
        benchmark_end
        - benchmark_start
    )


    # ======================================================
    # SEPARATE RESULTS
    # ======================================================

    successful_results = [

        result

        for result in results

        if result["success"]
    ]


    failed_results = [

        result

        for result in results

        if not result["success"]
    ]


    latencies = [

        result["latency"]

        for result in successful_results
    ]


    # ======================================================
    # BASIC METRICS
    # ======================================================

    successful_requests = len(
        successful_results
    )


    failed_requests = len(
        failed_results
    )


    if successful_requests > 0:

        average_latency = (
            statistics.mean(
                latencies
            )
        )


        minimum_latency = (
            min(latencies)
        )


        maximum_latency = (
            max(latencies)
        )


        p50_latency = (
            calculate_percentile(
                latencies,
                50
            )
        )


        p95_latency = (
            calculate_percentile(
                latencies,
                95
            )
        )

    else:

        average_latency = 0.0

        minimum_latency = 0.0

        maximum_latency = 0.0

        p50_latency = 0.0

        p95_latency = 0.0


    # ======================================================
    # THROUGHPUT
    # ======================================================

    if total_time > 0:

        throughput = (
            successful_requests
            / total_time
        )

    else:

        throughput = 0.0


    # ======================================================
    # SUCCESS RATE
    # ======================================================

    success_rate = (

        successful_requests
        / total_requests
        * 100
    )


    # ======================================================
    # ERROR RATE
    # ======================================================

    error_rate = (

        failed_requests
        / total_requests
        * 100
    )


    # ======================================================
    # DISPLAY RESULTS
    # ======================================================

    print()
    print("=" * 65)
    print("                 BENCHMARK RESULTS")
    print("=" * 65)


    print()
    print(
        "Total requests:",
        f"{total_requests:,}"
    )


    print(
        "Successful requests:",
        f"{successful_requests:,}"
    )


    print(
        "Failed requests:",
        f"{failed_requests:,}"
    )


    print()
    print(
        "Benchmark duration:",
        f"{total_time:.4f} seconds"
    )


    print()
    print(
        "Average latency:",
        f"{average_latency * 1000:.3f} ms"
    )


    print(
        "P50 latency:",
        f"{p50_latency * 1000:.3f} ms"
    )


    print(
        "P95 latency:",
        f"{p95_latency * 1000:.3f} ms"
    )


    print(
        "Minimum latency:",
        f"{minimum_latency * 1000:.3f} ms"
    )


    print(
        "Maximum latency:",
        f"{maximum_latency * 1000:.3f} ms"
    )


    print()
    print(
        "Throughput:",
        f"{throughput:.2f} requests/sec"
    )


    print(
        "Success rate:",
        f"{success_rate:.2f}%"
    )


    print(
        "Error rate:",
        f"{error_rate:.2f}%"
    )


    # ======================================================
    # SHOW FIRST ERROR IF SOMETHING FAILED
    # ======================================================

    if failed_requests > 0:

        print()
        print("=" * 65)
        print("                 ERROR INFORMATION")
        print("=" * 65)


        first_error = failed_results[0].get(
            "error",
            "Unknown error"
        )


        print()
        print(
            "First benchmark error:"
        )

        print(
            first_error
        )


        print()
        print(
            "Failed requests are not included "
            "in latency and throughput calculations."
        )


    # ======================================================
    # PERFORMANCE INTERPRETATION
    # ======================================================

    print()
    print("=" * 65)
    print("              PERFORMANCE INTERPRETATION")
    print("=" * 65)


    # ------------------------------------------------------
    # LATENCY
    # ------------------------------------------------------

    if successful_requests == 0:

        latency_rating = "Unavailable"

    elif p95_latency <= 0.100:

        latency_rating = "Excellent"

    elif p95_latency <= 0.300:

        latency_rating = "Good"

    elif p95_latency <= 1.000:

        latency_rating = "Moderate"

    else:

        latency_rating = "High"


    # ------------------------------------------------------
    # THROUGHPUT
    # ------------------------------------------------------

    if successful_requests == 0:

        throughput_rating = "Unavailable"

    elif throughput >= 1000:

        throughput_rating = "High"

    elif throughput >= 100:

        throughput_rating = "Moderate"

    else:

        throughput_rating = "Low"


    # ------------------------------------------------------
    # RELIABILITY
    # ------------------------------------------------------

    if success_rate >= 99.9:

        reliability_rating = "Excellent"

    elif success_rate >= 99:

        reliability_rating = "Good"

    elif success_rate >= 95:

        reliability_rating = "Moderate"

    else:

        reliability_rating = "Poor"


    print()
    print(
        "Latency rating:",
        latency_rating
    )


    print(
        "Throughput rating:",
        throughput_rating
    )


    print(
        "Reliability rating:",
        reliability_rating
    )


    # ======================================================
    # PERFORMANCE SCORE
    # ======================================================

    performance_score = 0


    # ------------------------------------------------------
    # Latency score
    # Maximum: 4
    # ------------------------------------------------------

    if successful_requests == 0:

        latency_score = 0

    elif p95_latency <= 0.100:

        latency_score = 4

    elif p95_latency <= 0.300:

        latency_score = 3

    elif p95_latency <= 1.000:

        latency_score = 2

    else:

        latency_score = 1


    # ------------------------------------------------------
    # Throughput score
    # Maximum: 3
    # ------------------------------------------------------

    if successful_requests == 0:

        throughput_score = 0

    elif throughput >= 1000:

        throughput_score = 3

    elif throughput >= 100:

        throughput_score = 2

    else:

        throughput_score = 1


    # ------------------------------------------------------
    # Reliability score
    # Maximum: 3
    # ------------------------------------------------------

    if success_rate >= 99.9:

        reliability_score = 3

    elif success_rate >= 99:

        reliability_score = 2

    elif success_rate >= 95:

        reliability_score = 1

    else:

        reliability_score = 0


    performance_score = (

        latency_score
        + throughput_score
        + reliability_score
    )


    print()
    print(
        "Performance score:",
        f"{performance_score}/10"
    )


    print()
    print("=" * 65)
    print("              BENCHMARK COMPLETE")
    print("=" * 65)


    # ======================================================
    # RETURN RESULTS
    # ======================================================

    return {

        "total_requests":
            total_requests,

        "successful_requests":
            successful_requests,

        "failed_requests":
            failed_requests,

        "benchmark_duration":
            total_time,

        "average_latency":
            average_latency,

        "p50_latency":
            p50_latency,

        "p95_latency":
            p95_latency,

        "minimum_latency":
            minimum_latency,

        "maximum_latency":
            maximum_latency,

        "throughput":
            throughput,

        "success_rate":
            success_rate,

        "error_rate":
            error_rate,

        "latency_rating":
            latency_rating,

        "throughput_rating":
            throughput_rating,

        "reliability_rating":
            reliability_rating,

        "performance_score":
            performance_score
    }


# ==========================================================
# TEST BENCHMARK
# ==========================================================

if __name__ == "__main__":

    import joblib


    MODEL_FILE = (
        "spam_classifier.joblib"
    )


    print()
    print(
        "Loading ML model..."
    )


    model = joblib.load(
        MODEL_FILE
    )


    # ------------------------------------------------------
    # Test input for the spam classifier
    # ------------------------------------------------------

    sample_input = (
        "Congratulations! "
        "You have won a free prize. "
        "Click now to claim your reward."
    )


    print(
        "Model loaded successfully."
    )


    results = run_benchmark(

        model=model,

        sample_input=sample_input,

        total_requests=1000,

        concurrency=10
    )