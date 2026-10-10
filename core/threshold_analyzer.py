from pricing.cost_calculator import (
    calculate_vm_costs,
    calculate_cloud_costs
)


def analyze_threshold(base_workload):

    print("\n========================================")
    print("        THRESHOLD ANALYSIS")
    print("========================================")

    request_levels = [
        25_000,
        50_000,
        100_000,
        200_000,
        500_000,
        750_000,
        1_000_000,
        2_000_000,
        5_000_000,
        10_000_000
    ]

    results = []

    previous_strategy = None
    threshold_found = False

    print("\nRequest Volume vs Deployment Strategy")
    print("----------------------------------------")

    for requests in request_levels:

        workload = base_workload.copy()

        workload["request_volume"] = requests

        # --------------------------------
        # VM COST
        # --------------------------------

        vm_costs = calculate_vm_costs(
            workload
        )

        cheapest_vm_provider = min(
            vm_costs,
            key=vm_costs.get
        )

        vm_cost = vm_costs[
            cheapest_vm_provider
        ]

        # --------------------------------
        # SERVERLESS COST
        # --------------------------------

        serverless_costs = calculate_cloud_costs(
            workload
        )

        if not serverless_costs:
            print(
                f"{requests:,} requests -> "
                "Serverless pricing unavailable"
            )
            continue

        cheapest_serverless_provider = min(
            serverless_costs,
            key=serverless_costs.get
        )

        serverless_cost = serverless_costs[
            cheapest_serverless_provider
        ]

        # --------------------------------
        # STRATEGY DECISION
        # --------------------------------

        if serverless_cost < vm_cost:

            preferred_strategy = "Serverless"

        elif vm_cost < serverless_cost:

            preferred_strategy = "VM"

        else:

            preferred_strategy = "Tie"

        # --------------------------------
        # STORE RESULT
        # --------------------------------

        result = {
            "request_volume": requests,
            "vm_provider": cheapest_vm_provider,
            "vm_cost": vm_cost,
            "serverless_provider":
                cheapest_serverless_provider,
            "serverless_cost":
                serverless_cost,
            "preferred_strategy":
                preferred_strategy
        }

        results.append(result)

        # --------------------------------
        # DISPLAY
        # --------------------------------

        print(
            f"{requests:>10,} requests | "
            f"VM: ${vm_cost:>8.4f} | "
            f"Serverless: ${serverless_cost:>8.4f} | "
            f"Preferred: {preferred_strategy}"
        )

        # --------------------------------
        # DETECT STRATEGY CHANGE
        # --------------------------------

        if (
            previous_strategy is not None
            and preferred_strategy != previous_strategy
            and not threshold_found
        ):

            print("\n***** STRATEGY CHANGE DETECTED *****")

            print(
                "Previous strategy:",
                previous_strategy
            )

            print(
                "New strategy:",
                preferred_strategy
            )

            print(
                "Approximate threshold is between",
                f"{previous_requests:,}",
                "and",
                f"{requests:,}",
                "requests/month"
            )

            threshold_found = True

        previous_strategy = preferred_strategy
        previous_requests = requests

    # --------------------------------
    # FINAL SUMMARY
    # --------------------------------

    print("\n========================================")
    print("        THRESHOLD SUMMARY")
    print("========================================")

    if threshold_found:

        print(
            "A deployment strategy change was detected."
        )

        print(
            "The exact break-even point will be "
            "refined in the next stage."
        )

    else:

        print(
            "No strategy change was detected "
            "within the tested workload range."
        )

    return results


if __name__ == "__main__":

    base_workload = {

        "traffic_pattern": "steady",

        "request_volume": 100_000,

        "latency": "standard",

        "request_duration": 0.2,

        "concurrency": 10
    }

    results = analyze_threshold(
        base_workload
    )

    print("\n========================================")
    print("       FINAL THRESHOLD RESULTS")
    print("========================================")

    for result in results:

        print(
            f'{result["request_volume"]:>10,} | '
            f'{result["preferred_strategy"]}'
        )