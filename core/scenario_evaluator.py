from simulation.workload_simulator import generate_workload_scenarios
from core.deployment_decision import decide_deployment
from core.cloud_provider_advisor import compare_cloud_providers
from pricing.cost_comparison import compare_costs


def evaluate_scenarios(base_workload, model_info):

    scenarios = generate_workload_scenarios(
        base_workload
    )

    results = []

    print("\n========================================")
    print("       SCENARIO EVALUATION ENGINE")
    print("========================================")

    for scenario in scenarios:

        print("\n")
        print("========================================")
        print(
            "SCENARIO:",
            scenario["name"]
        )
        print("========================================")

        # ----------------------------------------
        # 1. DEPLOYMENT DECISION
        # ----------------------------------------

        deployment_type = decide_deployment(
            scenario,
            model_info
        )

        # ----------------------------------------
        # 2. PROVIDER COMPARISON
        # ----------------------------------------

        if deployment_type == "Cloud":

            provider_result = compare_cloud_providers(
                scenario
            )

        else:

            # VM provider comparison will be connected
            # in a later step.
            provider_result = {
                "scores": {},
                "recommended_provider": "VM"
            }

        # ----------------------------------------
        # 3. COST COMPARISON
        # ----------------------------------------

        cost_result = compare_costs(
            scenario,
            deployment_type
        )

        # ----------------------------------------
        # 4. STORE RESULT
        # ----------------------------------------

        result = {
            "scenario": scenario["name"],
            "request_volume": scenario["request_volume"],
            "concurrency": scenario["concurrency"],
            "traffic_pattern": scenario["traffic_pattern"],
            "deployment_type": deployment_type,
            "provider": provider_result[
                "recommended_provider"
            ],
            "cost_result": cost_result
        }

        results.append(result)

        # ----------------------------------------
        # 5. DISPLAY SUMMARY
        # ----------------------------------------

        print("\n----- SCENARIO SUMMARY -----")

        print(
            "Scenario:",
            scenario["name"]
        )

        print(
            "Deployment:",
            deployment_type
        )

        print(
            "Provider:",
            provider_result[
                "recommended_provider"
            ]
        )

        if cost_result:

            print(
                "Cheapest option:",
                cost_result[
                    "cheapest_option"
                ]
            )

            print(
                "Estimated cost:",
                f'${cost_result["cheapest_cost"]:.4f}/month'
            )

    return results


if __name__ == "__main__":

    # ----------------------------------------
    # BASE WORKLOAD
    # ----------------------------------------

    base_workload = {

        "traffic_pattern": "steady",

        "request_volume": 100_000,

        "latency": "standard",

        "request_duration": 0.2,

        "concurrency": 10
    }

    # ----------------------------------------
    # MODEL INFORMATION
    # ----------------------------------------
    #
    # This uses the current spam classifier
    # only as a test model.
    #
    # Later the actual uploaded model information
    # from model_analyzer.py will be passed here.
    #

    model_info = {

        "model_size_kb": 376.95,

        "features": 8713
    }

    # ----------------------------------------
    # RUN EVALUATION
    # ----------------------------------------

    results = evaluate_scenarios(
        base_workload,
        model_info
    )

    # ----------------------------------------
    # FINAL TABLE
    # ----------------------------------------

    print("\n")
    print("========================================")
    print("       FINAL SCENARIO SUMMARY")
    print("========================================")

    for result in results:

        print(
            f'{result["scenario"]:<25} '
            f'{result["deployment_type"]:<10} '
            f'{result["provider"]}'
        )