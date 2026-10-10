from core.recommendation_engine import generate_recommendation


# ============================================================
# WORKLOAD SCENARIOS
# ============================================================

WORKLOAD_SCENARIOS = [
    {
        "name": "Low Traffic",
        "traffic_pattern": "steady",
        "request_volume": 25_000,
        "latency": "standard",
        "request_duration": 0.2,
        "concurrency": 5
    },

    {
        "name": "Normal Traffic",
        "traffic_pattern": "steady",
        "request_volume": 100_000,
        "latency": "standard",
        "request_duration": 0.2,
        "concurrency": 10
    },

    {
        "name": "High Traffic",
        "traffic_pattern": "steady",
        "request_volume": 200_000,
        "latency": "standard",
        "request_duration": 0.5,
        "concurrency": 20
    },

    {
        "name": "Sudden Traffic Spike",
        "traffic_pattern": "bursty",
        "request_volume": 500_000,
        "latency": "critical",
        "request_duration": 0.3,
        "concurrency": 50
    },

    {
        "name": "Sustained Heavy Traffic",
        "traffic_pattern": "steady",
        "request_volume": 1_000_000,
        "latency": "standard",
        "request_duration": 1.0,
        "concurrency": 100
    }
]


# ============================================================
# DISPLAY WORKLOAD
# ============================================================

def display_workload(workload):

    print("\n----------------------------------------")
    print("WORKLOAD CONFIGURATION")
    print("----------------------------------------")

    print("Traffic Pattern       :", workload["traffic_pattern"])
    print("Monthly Requests      :", f'{workload["request_volume"]:,}')
    print("Latency Requirement   :", workload["latency"])
    print("Request Duration      :", workload["request_duration"], "seconds")
    print("Expected Concurrency  :", workload["concurrency"])


# ============================================================
# RUN SCENARIO
# ============================================================

def run_scenario(scenario):

    print("\n\n")
    print("=" * 60)
    print("SCENARIO:", scenario["name"])
    print("=" * 60)

    workload = {
        "traffic_pattern": scenario["traffic_pattern"],
        "request_volume": scenario["request_volume"],
        "latency": scenario["latency"],
        "request_duration": scenario["request_duration"],
        "concurrency": scenario["concurrency"]
    }

    display_workload(workload)

    print("\nRunning deployment recommendation...")

    try:

        result = generate_recommendation(workload)

        print("\n----------------------------------------")
        print("SCENARIO RESULT")
        print("----------------------------------------")

        print(
            "Recommended Provider :",
            result.get("recommended_provider", "N/A")
        )

        print(
            "Estimated Cost       : $",
            f'{result.get("recommended_cost", 0):.4f}',
            "/month",
            sep=""
        )

        print(
            "Deployment Type      :",
            result.get("deployment_type", "N/A")
        )

        print(
            "Performance Score    :",
            result.get("performance_score", "N/A")
        )

        return {
            "scenario": scenario["name"],
            "traffic_pattern": scenario["traffic_pattern"],
            "request_volume": scenario["request_volume"],
            "recommended_provider": result.get(
                "recommended_provider",
                "N/A"
            ),
            "recommended_cost": result.get(
                "recommended_cost",
                0
            ),
            "deployment_type": result.get(
                "deployment_type",
                "N/A"
            ),
            "performance_score": result.get(
                "performance_score",
                0
            )
        }

    except Exception as e:

        print("\nERROR while processing scenario:")
        print(e)

        return {
            "scenario": scenario["name"],
            "traffic_pattern": scenario["traffic_pattern"],
            "request_volume": scenario["request_volume"],
            "recommended_provider": "Error",
            "recommended_cost": 0,
            "deployment_type": "Error",
            "performance_score": 0
        }


# ============================================================
# RUN ALL SCENARIOS
# ============================================================

def run_workload_simulation():

    print("\n")
    print("=" * 70)
    print("       CLOUD DEPLOYMENT WORKLOAD SIMULATOR")
    print("=" * 70)

    print("\nNumber of scenarios:", len(WORKLOAD_SCENARIOS))

    results = []

    for scenario in WORKLOAD_SCENARIOS:

        result = run_scenario(scenario)

        results.append(result)


    # ========================================================
    # FINAL COMPARISON
    # ========================================================

    print("\n\n")
    print("=" * 80)
    print("                    SIMULATION SUMMARY")
    print("=" * 80)

    print(
        f'{"Scenario":<25}'
        f'{"Requests":<15}'
        f'{"Provider":<25}'
        f'{"Cost":<15}'
        f'{"Type":<15}'
    )

    print("-" * 80)

    for result in results:

        print(
            f'{result["scenario"]:<25}'
            f'{result["request_volume"]:<15,}'
            f'{result["recommended_provider"]:<25}'
            f'${result["recommended_cost"]:<14.4f}'
            f'{result["deployment_type"]:<15}'
        )


    # ========================================================
    # PROVIDER CHANGES
    # ========================================================

    print("\n")
    print("=" * 70)
    print("                 DYNAMIC RECOMMENDATION")
    print("=" * 70)

    previous_provider = None

    for result in results:

        current_provider = result["recommended_provider"]

        if previous_provider is None:

            print(
                f'\n{result["scenario"]}: '
                f'{current_provider}'
            )

        elif current_provider != previous_provider:

            print(
                f'\nCHANGE DETECTED'
            )

            print(
                f'{previous_provider}  -->  '
                f'{current_provider}'
            )

            print(
                f'Reason: workload conditions changed.'
            )

        else:

            print(
                f'\n{result["scenario"]}: '
                f'No provider change '
                f'({current_provider})'
            )

        previous_provider = current_provider


    print("\n")
    print("=" * 70)
    print("              SIMULATION COMPLETED")
    print("=" * 70)

    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_workload_simulation()