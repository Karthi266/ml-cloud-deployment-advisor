def evaluate_strategies(
    workload,
    vm_cost,
    serverless_cost
):
    """
    Evaluate VM, Serverless and Hybrid strategies.

    This is a first-stage strategy model.
    The values are simulation weights and will
    later be replaced/expanded with measured
    performance and threshold data.
    """

    traffic = workload["traffic_pattern"]
    requests = workload["request_volume"]
    duration = workload["request_duration"]
    concurrency = workload["concurrency"]
    latency = workload["latency"]

    print("\n========================================")
    print("       STRATEGY EVALUATION")
    print("========================================")

    # --------------------------------------------------
    # INITIAL SCORES
    # --------------------------------------------------

    scores = {
        "VM": 0,
        "Serverless": 0,
        "Hybrid": 0
    }

    reasons = {
        "VM": [],
        "Serverless": [],
        "Hybrid": []
    }

    # --------------------------------------------------
    # 1. TRAFFIC PATTERN
    # --------------------------------------------------

    if traffic == "bursty":

        scores["Serverless"] += 3
        scores["Hybrid"] += 3

        reasons["Serverless"].append(
            "Bursty traffic benefits from elastic scaling"
        )

        reasons["Hybrid"].append(
            "Hybrid can handle bursts using elastic capacity"
        )

    elif traffic == "steady":

        scores["VM"] += 2
        scores["Serverless"] += 2
        scores["Hybrid"] += 2

        reasons["VM"].append(
            "Steady traffic can use continuously available resources"
        )

        reasons["Serverless"].append(
            "Serverless can handle steady traffic"
        )

        reasons["Hybrid"].append(
            "Hybrid can maintain a baseline capacity"
        )

    # --------------------------------------------------
    # 2. REQUEST VOLUME
    # --------------------------------------------------

    if requests < 100_000:

        scores["Serverless"] += 3
        scores["Hybrid"] += 1

        reasons["Serverless"].append(
            "Lower request volume favors usage-based execution"
        )

    elif requests < 500_000:

        scores["VM"] += 1
        scores["Serverless"] += 2
        scores["Hybrid"] += 2

        reasons["VM"].append(
            "Moderate workload can justify dedicated capacity"
        )

        reasons["Serverless"].append(
            "Serverless remains suitable for moderate workloads"
        )

    elif requests < 1_000_000:

        scores["VM"] += 2
        scores["Serverless"] += 1
        scores["Hybrid"] += 3

        reasons["VM"].append(
            "Higher sustained volume can benefit from dedicated capacity"
        )

        reasons["Hybrid"].append(
            "Higher volume can use a baseline VM with elastic burst capacity"
        )

    else:

        scores["VM"] += 4
        scores["Hybrid"] += 4

        reasons["VM"].append(
            "Very high request volume can benefit from dedicated capacity"
        )

        reasons["Hybrid"].append(
            "Very high volume may benefit from a dedicated baseline"
        )

    # --------------------------------------------------
    # 3. REQUEST DURATION
    # --------------------------------------------------

    if duration <= 0.5:

        scores["Serverless"] += 2
        scores["Hybrid"] += 1

        reasons["Serverless"].append(
            "Short inference duration is suitable for serverless execution"
        )

    elif duration <= 2.0:

        scores["VM"] += 1
        scores["Serverless"] += 1
        scores["Hybrid"] += 2

    else:

        scores["VM"] += 3
        scores["Hybrid"] += 2

        reasons["VM"].append(
            "Long inference duration favors continuously available compute"
        )

        reasons["Hybrid"].append(
            "Long inference duration can benefit from a VM baseline"
        )

    # --------------------------------------------------
    # 4. CONCURRENCY
    # --------------------------------------------------

    if concurrency < 20:

        scores["Serverless"] += 2

        reasons["Serverless"].append(
            "Low concurrency is suitable for elastic execution"
        )

    elif concurrency < 100:

        scores["VM"] += 1
        scores["Serverless"] += 1
        scores["Hybrid"] += 2

    else:

        scores["VM"] += 3
        scores["Hybrid"] += 3

        reasons["VM"].append(
            "High concurrency favors provisioned resources"
        )

        reasons["Hybrid"].append(
            "High concurrency can use a provisioned baseline"
        )

    # --------------------------------------------------
    # 5. LATENCY REQUIREMENT
    # --------------------------------------------------

    if latency == "critical":

        scores["VM"] += 3
        scores["Hybrid"] += 2

        reasons["VM"].append(
            "Critical latency can favor continuously available resources"
        )

        reasons["Hybrid"].append(
            "Hybrid can keep latency-sensitive workloads on baseline capacity"
        )

    else:

        scores["Serverless"] += 1
        scores["VM"] += 1
        scores["Hybrid"] += 1

    # --------------------------------------------------
    # 6. COST INFLUENCE
    # --------------------------------------------------
    #
    # Cost is included as a relative signal.
    # It is NOT allowed to completely determine
    # the recommendation.
    #

    available_costs = {
        "VM": vm_cost,
        "Serverless": serverless_cost
    }

    valid_costs = {
        name: cost
        for name, cost in available_costs.items()
        if cost is not None and cost >= 0
    }

    if valid_costs:

        cheapest_cost = min(
            valid_costs.values()
        )

        for strategy, cost in valid_costs.items():

            if cost == 0:

                cost_score = 3

            else:

                ratio = cheapest_cost / cost

                if ratio >= 0.90:
                    cost_score = 2

                elif ratio >= 0.70:
                    cost_score = 1

                else:
                    cost_score = 0

            scores[strategy] += cost_score

            reasons[strategy].append(
                "Cost considered using the current pricing model"
            )

        # Hybrid currently has no independent cost model.
        # Give it a neutral score rather than pretending
        # we know its actual cost.
        scores["Hybrid"] += 1

        reasons["Hybrid"].append(
            "Hybrid cost is currently treated as neutral"
        )

    # --------------------------------------------------
    # DISPLAY SCORES
    # --------------------------------------------------

    print("\nStrategy Scores:")

    for strategy, score in scores.items():

        print(
            f"{strategy}: {score}"
        )

    # --------------------------------------------------
    # DISPLAY REASONS
    # --------------------------------------------------

    print("\nStrategy Factors:")

    for strategy in scores:

        print(f"\n{strategy}:")

        for reason in reasons[strategy]:

            print(
                "-",
                reason
            )

    # --------------------------------------------------
    # RECOMMENDATION
    # --------------------------------------------------

    highest_score = max(
        scores.values()
    )

    top_strategies = [
        strategy
        for strategy, score in scores.items()
        if score == highest_score
    ]

    if len(top_strategies) > 1:

        recommended_strategy = "Tie"

        print(
            "\nRecommended Strategy: Tie"
        )

        print(
            "Top candidates:",
            ", ".join(top_strategies)
        )

    else:

        recommended_strategy = top_strategies[0]

        print(
            "\nRecommended Strategy:",
            recommended_strategy
        )

    return {
        "scores": scores,
        "recommended_strategy": recommended_strategy,
        "reasons": reasons
    }


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":

    test_workload = {

        "traffic_pattern": "steady",

        "request_volume": 100_000,

        "latency": "standard",

        "request_duration": 0.2,

        "concurrency": 10
    }

    # These are the CURRENT estimated costs
    # used only for testing this strategy engine.
    #
    # They are not claimed to be final real-world
    # provider bills.

    vm_cost = 36.50

    serverless_cost = 0.04

    result = evaluate_strategies(
        test_workload,
        vm_cost,
        serverless_cost
    )

    print("\n========================================")
    print("          FINAL RESULT")
    print("========================================")

    print(
        "Recommended Strategy:",
        result["recommended_strategy"]
    )