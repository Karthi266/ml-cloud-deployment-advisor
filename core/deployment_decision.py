def decide_deployment(workload, model_info):

    traffic = workload["traffic_pattern"]
    requests = workload["request_volume"]
    latency = workload["latency"]
    duration = workload["request_duration"]
    concurrency = workload["concurrency"]

    model_size = model_info["model_size_kb"]
    features = model_info["features"]

    print("\n==============================================")
    print("        DEPLOYMENT MODEL DECISION")
    print("==============================================")

    print("\nWorkload:")
    print("Traffic Pattern      :", traffic)
    print("Monthly Requests     :", f"{requests:,}")
    print("Request Duration     :", f"{duration:.2f}", "seconds")
    print("Expected Concurrency :", concurrency)
    print("Latency Requirement  :", latency)

    print("\nModel:")
    print("Model Size           :", f"{model_size:.2f}", "KB")
    print("Features             :", f"{features:,}")

    # ---------------------------------------------------------
    # Transparent workload indicators
    # ---------------------------------------------------------

    cloud_indicators = []
    vm_indicators = []

    # 1. Traffic pattern
    if traffic == "bursty":
        cloud_indicators.append(
            "Bursty traffic benefits from elastic cloud scaling."
        )
    elif traffic == "steady":
        vm_indicators.append(
            "Steady traffic can make continuously running VM capacity practical."
        )

    # 2. Request volume
    if requests >= 1_000_000:
        vm_indicators.append(
            "High request volume may favor continuously available compute."
        )
    else:
        cloud_indicators.append(
            "Lower request volume can benefit from usage-based managed services."
        )

    # 3. Latency requirement
    if latency == "critical":
        vm_indicators.append(
            "Critical latency requirements favor predictable dedicated compute."
        )
    else:
        cloud_indicators.append(
            "Standard latency requirements are suitable for managed cloud execution."
        )

    # 4. Request duration
    if duration > 1.0:
        vm_indicators.append(
            "Long-running requests increase the importance of continuously available compute."
        )
    else:
        cloud_indicators.append(
            "Short request duration is suitable for request-driven cloud execution."
        )

    # 5. Concurrency
    if concurrency >= 100:
        vm_indicators.append(
            "High concurrency can require more predictable compute capacity."
        )
    else:
        cloud_indicators.append(
            "Moderate concurrency is suitable for managed cloud scaling."
        )

    # 6. Model size
    if model_size > 100_000:
        vm_indicators.append(
            "Large model size may require dedicated memory and resource control."
        )
    else:
        cloud_indicators.append(
            "The model size is relatively small for managed cloud deployment."
        )

    # 7. Feature count
    if features > 10_000:
        vm_indicators.append(
            "High feature dimensionality can increase inference resource requirements."
        )
    else:
        cloud_indicators.append(
            "The model complexity is suitable for managed cloud execution."
        )

    # ---------------------------------------------------------
    # Transparent decision rule
    # ---------------------------------------------------------
    #
    # The decision is intentionally not presented as an
    # artificial numerical score.
    #
    # Strong VM characteristics:
    # - high request volume
    # - critical latency
    # - long requests
    # - high concurrency
    # - very large model
    #
    # Strong cloud characteristics:
    # - bursty traffic
    # - lower request volume
    # - standard latency
    # - short requests
    # - moderate concurrency
    # - smaller model
    # ---------------------------------------------------------

    strong_vm_conditions = 0
    strong_cloud_conditions = 0

    if requests >= 1_000_000:
        strong_vm_conditions += 1

    if latency == "critical":
        strong_vm_conditions += 1

    if duration > 1.0:
        strong_vm_conditions += 1

    if concurrency >= 100:
        strong_vm_conditions += 1

    if model_size > 100_000:
        strong_vm_conditions += 1

    if traffic == "bursty":
        strong_cloud_conditions += 1

    if requests < 1_000_000:
        strong_cloud_conditions += 1

    if latency != "critical":
        strong_cloud_conditions += 1

    if duration <= 1.0:
        strong_cloud_conditions += 1

    if concurrency < 100:
        strong_cloud_conditions += 1

    if model_size <= 100_000:
        strong_cloud_conditions += 1

    # ---------------------------------------------------------
    # Final deployment classification
    # ---------------------------------------------------------

    if strong_vm_conditions > strong_cloud_conditions:
        deployment_type = "VM"

        reason = (
            "The workload has stronger characteristics for self-managed "
            "VM deployment, including higher resource demand or the need "
            "for more predictable continuously available compute."
        )

    else:
        deployment_type = "Cloud"

        reason = (
            "The workload has stronger characteristics for managed cloud "
            "deployment, including elastic scaling suitability, moderate "
            "resource requirements, and request-driven execution."
        )

    # ---------------------------------------------------------
    # Display analysis
    # ---------------------------------------------------------

    print("\n----------------------------------------------")
    print("CLOUD-SUITABLE CHARACTERISTICS")
    print("----------------------------------------------")

    if cloud_indicators:
        for item in cloud_indicators:
            print("- " + item)

    print("\n----------------------------------------------")
    print("VM-SUITABLE CHARACTERISTICS")
    print("----------------------------------------------")

    if vm_indicators:
        for item in vm_indicators:
            print("- " + item)

    print("\n----------------------------------------------")
    print("DEPLOYMENT CLASSIFICATION")
    print("----------------------------------------------")

    print("Cloud indicators:", strong_cloud_conditions)
    print("VM indicators   :", strong_vm_conditions)

    print("\nRecommended deployment model:", deployment_type)
    print("Reason:", reason)

    print("\n==============================================")
    print("IMPORTANT")
    print("==============================================")
    print(
        "This classification evaluates workload and model characteristics."
    )
    print(
        "Final deployment selection should also consider real pricing, "
        "provider compatibility, break-even analysis and benchmarking."
    )

    return deployment_type


if __name__ == "__main__":

    test_workload = {
        "traffic_pattern": "steady",
        "request_volume": 100000,
        "latency": "standard",
        "request_duration": 0.2,
        "concurrency": 10
    }

    test_model = {
        "model_size_kb": 376.95,
        "features": 8713
    }

    result = decide_deployment(test_workload, test_model)

    print("\nFinal decision:", result)