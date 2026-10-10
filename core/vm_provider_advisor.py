def compare_vm_providers(workload):

    traffic = workload["traffic_pattern"]
    requests = workload["request_volume"]
    latency = workload["latency"]
    duration = workload["request_duration"]
    concurrency = workload["concurrency"]

    print("\n===== VM PROVIDER COMPARISON =====")

    scores = {
        "AWS EC2": 0,
        "Azure VM": 0,
        "Google Compute Engine": 0
    }

    # 1. Traffic pattern
    if traffic == "steady":
        scores["AWS EC2"] += 2
        scores["Azure VM"] += 2
        scores["Google Compute Engine"] += 2
    else:
        scores["AWS EC2"] += 1
        scores["Azure VM"] += 1
        scores["Google Compute Engine"] += 1

    # 2. Request volume
    if requests < 100_000:
        scores["Google Compute Engine"] += 2
    elif requests < 1_000_000:
        scores["AWS EC2"] += 2
    else:
        scores["Azure VM"] += 2

    # 3. Latency requirement
    if latency == "critical":
        scores["AWS EC2"] += 2
        scores["Azure VM"] += 1
    else:
        scores["Google Compute Engine"] += 1

    # 4. Request duration
    if duration > 1.0:
        scores["AWS EC2"] += 1
        scores["Azure VM"] += 1
    else:
        scores["Google Compute Engine"] += 1

    # 5. Concurrency
    if concurrency < 20:
        scores["Google Compute Engine"] += 1
    elif concurrency < 100:
        scores["AWS EC2"] += 1
    else:
        scores["Azure VM"] += 1

    print("\nVM Provider Scores:")

    for provider, score in scores.items():
        print(f"{provider}: {score}")

    recommended_provider = max(scores, key=scores.get)

    print("\nRecommended VM Provider:", recommended_provider)

    return {
        "scores": scores,
        "recommended_provider": recommended_provider
    }


if __name__ == "__main__":

    test_workload = {
        "traffic_pattern": "steady",
        "request_volume": 100000,
        "latency": "standard",
        "request_duration": 0.2,
        "concurrency": 10
    }

    result = compare_vm_providers(test_workload)

    print("\n===== FINAL RESULT =====")
    print(
        "Recommended provider:",
        result["recommended_provider"]
    )