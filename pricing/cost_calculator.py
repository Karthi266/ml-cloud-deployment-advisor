from functools import lru_cache

from pricing.aws_pricing import get_aws_lambda_pricing

from pricing.azure_functions_pricing import (
    get_azure_functions_pricing
)

from pricing.google_cloud_pricing import (
    get_google_cloud_run_pricing
)

from pricing.google_vm_pricing import (
    get_google_vm_pricing
)

from pricing.azure_pricing import (
    get_azure_vm_price
)


# ==========================================================
# PRICING CACHE
# ==========================================================

@lru_cache(maxsize=1)
def get_cached_aws_lambda_pricing():

    return get_aws_lambda_pricing()


@lru_cache(maxsize=1)
def get_cached_azure_functions_pricing():

    return get_azure_functions_pricing()


@lru_cache(maxsize=1)
def get_cached_google_cloud_run_pricing():

    return get_google_cloud_run_pricing()


@lru_cache(maxsize=1)
def get_cached_google_vm_pricing():

    return get_google_vm_pricing()


@lru_cache(maxsize=1)
def get_cached_azure_vm_price():

    return get_azure_vm_price()


def clear_pricing_cache():

    get_cached_aws_lambda_pricing.cache_clear()

    get_cached_azure_functions_pricing.cache_clear()

    get_cached_google_cloud_run_pricing.cache_clear()

    get_cached_google_vm_pricing.cache_clear()

    get_cached_azure_vm_price.cache_clear()


# ==========================================================
# DEFAULT CONFIGURATION
# ==========================================================

DEFAULT_MONTHLY_REQUESTS = 100000
DEFAULT_REQUEST_DURATION = 0.2
DEFAULT_MEMORY_GB = 1

MONTHLY_HOURS = 730


# ==========================================================
# WORKLOAD NORMALIZATION
# ==========================================================

def get_workload_values(workload=None):

    """
    Extract workload values from the workload dictionary.

    Expected structure:

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

    monthly_requests = workload.get(
        "request_volume",
        DEFAULT_MONTHLY_REQUESTS
    )

    request_duration = workload.get(
        "request_duration",
        DEFAULT_REQUEST_DURATION
    )

    memory_gb = workload.get(
        "memory_gb",
        DEFAULT_MEMORY_GB
    )

    # ------------------------------------------------------
    # Validation
    # ------------------------------------------------------

    try:

        monthly_requests = int(
            monthly_requests
        )

    except (TypeError, ValueError):

        monthly_requests = (
            DEFAULT_MONTHLY_REQUESTS
        )

    try:

        request_duration = float(
            request_duration
        )

    except (TypeError, ValueError):

        request_duration = (
            DEFAULT_REQUEST_DURATION
        )

    try:

        memory_gb = float(
            memory_gb
        )

    except (TypeError, ValueError):

        memory_gb = DEFAULT_MEMORY_GB

    # ------------------------------------------------------
    # Prevent invalid values
    # ------------------------------------------------------

    if monthly_requests <= 0:

        monthly_requests = (
            DEFAULT_MONTHLY_REQUESTS
        )

    if request_duration <= 0:

        request_duration = (
            DEFAULT_REQUEST_DURATION
        )

    if memory_gb <= 0:

        memory_gb = DEFAULT_MEMORY_GB

    return (
        monthly_requests,
        request_duration,
        memory_gb
    )


# ==========================================================
# AWS LAMBDA COST
# ==========================================================

def calculate_aws_lambda_cost(
    monthly_requests,
    request_duration,
    memory_gb
):

    print()
    print("=" * 55)
    print("AWS LAMBDA COST")
    print("=" * 55)

    pricing = (
        get_cached_aws_lambda_pricing()
    )

    request_price = pricing[
        "request_price_per_request"
    ]

    compute_price = pricing[
        "compute_price_per_gb_second"
    ]

    request_cost = (
        monthly_requests
        * request_price
    )

    compute_seconds = (
        monthly_requests
        * request_duration
    )

    compute_cost = (
        compute_seconds
        * memory_gb
        * compute_price
    )

    total_cost = (
        request_cost
        + compute_cost
    )

    print(
        "Request cost:",
        f"${request_cost:.4f}"
    )

    print(
        "Compute cost:",
        f"${compute_cost:.4f}"
    )

    print(
        "AWS Lambda monthly cost:",
        f"${total_cost:.4f}"
    )

    return total_cost


# ==========================================================
# AZURE FUNCTIONS COST
# ==========================================================

def calculate_azure_functions_cost(
    monthly_requests,
    request_duration,
    memory_gb
):

    print()
    print("=" * 55)
    print("AZURE FUNCTIONS COST")
    print("=" * 55)

    pricing = (
        get_cached_azure_functions_pricing()
    )

    execution_price = pricing[
        "execution_price_per_10"
    ]

    execution_time_price = pricing[
        "execution_time_price_per_gb_second"
    ]

    execution_cost = (
        monthly_requests
        / 10
        * execution_price
    )

    execution_seconds = (
        monthly_requests
        * request_duration
    )

    execution_time_cost = (
        execution_seconds
        * memory_gb
        * execution_time_price
    )

    total_cost = (
        execution_cost
        + execution_time_cost
    )

    print(
        "Execution cost:",
        f"${execution_cost:.4f}"
    )

    print(
        "Execution time cost:",
        f"${execution_time_cost:.4f}"
    )

    print(
        "Azure Functions monthly cost:",
        f"${total_cost:.4f}"
    )

    return total_cost


# ==========================================================
# GOOGLE CLOUD RUN COST
# ==========================================================

def calculate_google_cloud_run_cost(
    monthly_requests,
    request_duration,
    memory_gb
):

    print()
    print("=" * 55)
    print("GOOGLE CLOUD RUN COST")
    print("=" * 55)

    pricing = (
        get_cached_google_cloud_run_pricing()
    )

    cpu_price = pricing[
        "cpu_price_per_vcpu_second"
    ]

    memory_price = pricing[
        "memory_price_per_gib_second"
    ]

    request_price = pricing[
        "request_price_per_million"
    ]

    cpu_seconds = (
        monthly_requests
        * request_duration
    )

    cpu_cost = (
        cpu_seconds
        * cpu_price
    )

    memory_seconds = (
        monthly_requests
        * request_duration
    )

    memory_cost = (
        memory_seconds
        * memory_gb
        * memory_price
    )

    request_cost = (
        monthly_requests
        / 1_000_000
        * request_price
    )

    total_cost = (
        cpu_cost
        + memory_cost
        + request_cost
    )

    print(
        "CPU cost:",
        f"${cpu_cost:.4f}"
    )

    print(
        "Memory cost:",
        f"${memory_cost:.4f}"
    )

    print(
        "Request cost:",
        f"${request_cost:.4f}"
    )

    print(
        "Google Cloud Run monthly cost:",
        f"${total_cost:.4f}"
    )

    return total_cost


# ==========================================================
# AZURE VM COST
# ==========================================================

def calculate_azure_vm_cost():

    print()
    print("=" * 55)
    print("AZURE VM COST")
    print("=" * 55)

    try:

        pricing = (
            get_cached_azure_vm_price()
        )

        hourly_price = pricing[
            "price_per_hour"
        ]

        monthly_cost = (
            hourly_price
            * MONTHLY_HOURS
        )

        print(
            "Hourly price:",
            f"${hourly_price:.4f}"
        )

        print(
            "Monthly hours:",
            MONTHLY_HOURS
        )

        print(
            "Azure VM monthly cost:",
            f"${monthly_cost:.2f}"
        )

        return monthly_cost

    except Exception as error:

        print(
            "Azure VM pricing unavailable."
        )

        print(
            "Reason:",
            error
        )

        return None


# ==========================================================
# GOOGLE COMPUTE ENGINE COST
# ==========================================================

def calculate_google_compute_engine_cost():

    print()
    print("=" * 55)
    print("GOOGLE COMPUTE ENGINE COST")
    print("=" * 55)

    try:

        pricing = (
            get_cached_google_vm_pricing()
        )

        hourly_price = pricing[
            "price_per_hour"
        ]

        monthly_cost = (
            hourly_price
            * MONTHLY_HOURS
        )

        print(
            "Machine type:",
            pricing[
                "machine_type"
            ]
        )

        print(
            "vCPUs:",
            pricing[
                "vcpus"
            ]
        )

        print(
            "Memory:",
            pricing[
                "memory_gb"
            ],
            "GiB"
        )

        print(
            "Hourly price:",
            f"${hourly_price:.8f}"
        )

        print(
            "Monthly hours:",
            MONTHLY_HOURS
        )

        print(
            "Google Compute Engine monthly cost:",
            f"${monthly_cost:.2f}"
        )

        print(
            "Pricing source:",
            pricing[
                "source_type"
            ]
        )

        print(
            "Refresh status:",
            pricing[
                "refresh_status"
            ]
        )

        return monthly_cost

    except Exception as error:

        print(
            "Google Compute Engine "
            "pricing unavailable."
        )

        print(
            "Reason:",
            error
        )

        return None


# ==========================================================
# FIND CHEAPEST VM
# ==========================================================

def find_cheapest_vm(vm_options):

    available = {

        name: cost

        for name, cost
        in vm_options.items()

        if cost is not None
    }

    if not available:

        return None, None

    cheapest_provider = min(
        available,
        key=available.get
    )

    return (
        cheapest_provider,
        available[
            cheapest_provider
        ]
    )


# ==========================================================
# FIND CHEAPEST SERVERLESS
# ==========================================================

def find_cheapest_serverless(
    serverless_options
):

    available = {

        name: cost

        for name, cost
        in serverless_options.items()

        if cost is not None
    }

    if not available:

        return None, None

    cheapest_provider = min(
        available,
        key=available.get
    )

    return (
        cheapest_provider,
        available[
            cheapest_provider
        ]
    )


# ==========================================================
# MAIN COST ANALYSIS
# ==========================================================

def run_cost_analysis(workload=None):

    (
        monthly_requests,
        request_duration,
        memory_gb
    ) = get_workload_values(
        workload
    )

    print()
    print()
    print("=" * 65)
    print(
        "        ML CLOUD DEPLOYMENT COST ANALYSIS"
    )
    print("=" * 65)

    print()
    print("Workload configuration")
    print("-" * 65)

    print(
        "Monthly requests:",
        f"{monthly_requests:,}"
    )

    print(
        "Average request duration:",
        f"{request_duration} seconds"
    )

    print(
        "Memory:",
        f"{memory_gb} GB"
    )

    print(
        "Monthly hours:",
        MONTHLY_HOURS
    )

    # ======================================================
    # SERVERLESS
    # ======================================================

    aws_lambda_cost = (
        calculate_aws_lambda_cost(
            monthly_requests,
            request_duration,
            memory_gb
        )
    )

    azure_functions_cost = (
        calculate_azure_functions_cost(
            monthly_requests,
            request_duration,
            memory_gb
        )
    )

    google_cloud_run_cost = (
        calculate_google_cloud_run_cost(
            monthly_requests,
            request_duration,
            memory_gb
        )
    )

    serverless_options = {

        "AWS Lambda":
            aws_lambda_cost,

        "Azure Functions":
            azure_functions_cost,

        "Google Cloud Run":
            google_cloud_run_cost
    }

    # ======================================================
    # VIRTUAL MACHINES
    # ======================================================

    azure_vm_cost = (
        calculate_azure_vm_cost()
    )

    google_compute_engine_cost = (
        calculate_google_compute_engine_cost()
    )

    # AWS EC2 is intentionally excluded because
    # AWS credentials / EC2 pricing access is
    # not currently configured.

    vm_options = {

        "Azure VM":
            azure_vm_cost,

        "Google Compute Engine":
            google_compute_engine_cost
    }

    # ======================================================
    # CHEAPEST SERVERLESS
    # ======================================================

    (
        cheapest_serverless,
        cheapest_serverless_cost
    ) = find_cheapest_serverless(
        serverless_options
    )

    # ======================================================
    # CHEAPEST VM
    # ======================================================

    (
        cheapest_vm,
        cheapest_vm_cost
    ) = find_cheapest_vm(
        vm_options
    )

    # ======================================================
    # FINAL COST COMPARISON
    # ======================================================

    print()
    print("=" * 65)
    print(
        "              FINAL COST COMPARISON"
    )
    print("=" * 65)

    print()
    print("SERVERLESS OPTIONS")
    print("-" * 65)

    for provider, cost in (
        serverless_options.items()
    ):

        if cost is not None:

            print(
                f"{provider:<25}"
                f"${cost:.4f}/month"
            )

        else:

            print(
                f"{provider:<25}"
                "Unavailable"
            )

    print()
    print("VIRTUAL MACHINE OPTIONS")
    print("-" * 65)

    for provider, cost in (
        vm_options.items()
    ):

        if cost is not None:

            print(
                f"{provider:<25}"
                f"${cost:.2f}/month"
            )

        else:

            print(
                f"{provider:<25}"
                "Unavailable"
            )

    print()
    print("-" * 65)

    if cheapest_vm is not None:

        print(
            "Cheapest VM:",
            cheapest_vm
        )

        print(
            "VM cost:",
            f"${cheapest_vm_cost:.2f}/month"
        )

    else:

        print(
            "Cheapest VM: None"
        )

    if cheapest_serverless is not None:

        print(
            "Cheapest Serverless:",
            cheapest_serverless
        )

        print(
            "Serverless cost:",
            f"${cheapest_serverless_cost:.4f}/month"
        )

    else:

        print(
            "Cheapest Serverless: None"
        )

    # ======================================================
    # STRATEGY DECISION
    # ======================================================

    print()
    print("=" * 65)
    print(
        "              STRATEGY DECISION"
    )
    print("=" * 65)

    if (
        cheapest_vm_cost is not None
        and cheapest_serverless_cost is not None
    ):

        if (
            cheapest_vm_cost
            < cheapest_serverless_cost
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
                "Managed / Serverless"
            )

            preferred_provider = (
                cheapest_serverless
            )

            preferred_cost = (
                cheapest_serverless_cost
            )

        print()
        print(
            "Preferred Strategy:",
            preferred_strategy
        )

        print(
            "Recommended Provider:",
            preferred_provider
        )

        print(
            "Estimated Monthly Cost:",
            f"${preferred_cost:.4f}"
        )

    elif cheapest_serverless_cost is not None:

        preferred_strategy = (
            "Managed / Serverless"
        )

        preferred_provider = (
            cheapest_serverless
        )

        preferred_cost = (
            cheapest_serverless_cost
        )

        print()
        print(
            "Preferred Strategy:",
            preferred_strategy
        )

        print(
            "Recommended Provider:",
            preferred_provider
        )

        print(
            "Estimated Monthly Cost:",
            f"${preferred_cost:.4f}"
        )

    elif cheapest_vm_cost is not None:

        preferred_strategy = (
            "Self-Managed VM"
        )

        preferred_provider = (
            cheapest_vm
        )

        preferred_cost = (
            cheapest_vm_cost
        )

        print()
        print(
            "Preferred Strategy:",
            preferred_strategy
        )

        print(
            "Recommended Provider:",
            preferred_provider
        )

        print(
            "Estimated Monthly Cost:",
            f"${preferred_cost:.2f}"
        )

    else:

        preferred_strategy = None
        preferred_provider = None
        preferred_cost = None

        print()
        print(
            "Unable to determine "
            "preferred strategy."
        )

    # ======================================================
    # COMPLETE
    # ======================================================

    print()
    print("=" * 65)
    print(
        "                  ANALYSIS COMPLETE"
    )
    print("=" * 65)

    # ======================================================
    # RETURN RESULTS
    # ======================================================

    return {

        "workload": {

            "request_volume":
                monthly_requests,

            "request_duration":
                request_duration,

            "memory_gb":
                memory_gb
        },

        "serverless":
            serverless_options,

        "vm":
            vm_options,

        "cheapest_serverless":
            cheapest_serverless,

        "cheapest_serverless_cost":
            cheapest_serverless_cost,

        "cheapest_vm":
            cheapest_vm,

        "cheapest_vm_cost":
            cheapest_vm_cost,

        "preferred_strategy":
            preferred_strategy,

        "preferred_provider":
            preferred_provider,

        "preferred_cost":
            preferred_cost
    }


# ==========================================================
# PROGRAM ENTRY
# ==========================================================

if __name__ == "__main__":

    test_workload = {

        "traffic_pattern":
            "steady",

        "request_volume":
            100000,

        "latency":
            "standard",

        "request_duration":
            0.2,

        "concurrency":
            10,

        "memory_gb":
            1
    }

    run_cost_analysis(
        test_workload
    )