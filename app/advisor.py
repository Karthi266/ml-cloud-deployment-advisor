from core.model_analyzer import analyze_model
from core.workload_analyzer import analyze_workload
from core.deployment_decision import decide_deployment
from core.cloud_provider_advisor import compare_cloud_providers
from pricing.cost_comparison import compare_costs


def main():

    print("\n===================================")
    print("     SMART CLOUD DEPLOYMENT ADVISOR")
    print("===================================")

    # ==========================================
    # STEP 1: GET ML MODEL PATH
    # ==========================================

    print("\n[1] ML MODEL INPUT")

    model_path = input(
        "Enter ML model path (.joblib/.pkl): "
    ).strip()

    if not model_path:

        print(
            "Model path cannot be empty."
        )

        return

    # ==========================================
    # STEP 2: ANALYZE ML MODEL
    # ==========================================

    print("\n[2] Analyzing ML model...")

    model_info = analyze_model(
        model_path
    )

    if model_info is None:

        print(
            "Unable to analyze the ML model."
        )

        return

    # ==========================================
    # CHECK MODEL COMPATIBILITY
    # ==========================================

    if not model_info["supported"]:

        print(
            "\nThe uploaded model type is currently "
            "not supported by the deployment advisor."
        )

        print(
            "Model type:",
            model_info["model_type"]
        )

        print(
            "\nThe advisor currently supports "
            "common scikit-learn models."
        )

        return

    # ==========================================
    # DISPLAY MODEL INFORMATION
    # ==========================================

    print("\n===== MODEL ANALYSIS =====")

    print(
        "Model path:",
        model_info["model_path"]
    )

    print(
        "Model type:",
        model_info["model_type"]
    )

    print(
        "Model size:",
        model_info["model_size_kb"],
        "KB"
    )

    print(
        "Number of features:",
        model_info["features"]
    )

    print(
        "Number of classes:",
        model_info["classes"]
    )

    print(
        "Vectorizer:",
        model_info["vectorizer"]
    )

    print(
        "Classifier:",
        model_info["classifier"]
    )

    print(
        "Supported:",
        model_info["supported"]
    )

    print("Components:")

    for component in model_info["components"]:

        print(
            "-",
            component
        )

    # ==========================================
    # STEP 3: ANALYZE WORKLOAD
    # ==========================================

    print("\n[3] Analyzing workload...")

    workload = analyze_workload()

    # ==========================================
    # STEP 4: DECIDE VM OR CLOUD
    # ==========================================

    print("\n[4] Selecting deployment type...")

    deployment = decide_deployment(
        workload,
        model_info
    )

    # ==========================================
    # STEP 5: CALCULATE COSTS
    # ==========================================

    print("\n[5] Calculating deployment costs...")

    costs = compare_costs(
        workload
    )

    # ==========================================
    # STEP 6: COMPARE CLOUD PROVIDERS
    # ==========================================

    provider = None

    if deployment == "Cloud":

        print(
            "\n[6] Comparing cloud providers..."
        )

        provider = compare_cloud_providers(
            workload
        )

    # ==========================================
    # STEP 7: FINAL RECOMMENDATION
    # ==========================================

    print("\n===================================")
    print("       FINAL RECOMMENDATION")
    print("===================================")

    print(
        "Model:",
        model_path
    )

    print(
        "Deployment type:",
        deployment
    )

    if deployment == "Cloud":

        print(
            "Recommended provider:",
            provider
        )

        print(
            "Estimated cost:",
            f"${costs[provider]:.2f}",
            "per month"
        )

    else:

        print(
            "Recommended option:",
            "Dedicated VM"
        )

        print(
            "Estimated VM cost:",
            f"${costs['Dedicated VM']:.2f}",
            "per month"
        )

    # ==========================================
    # DISPLAY ALL COST OPTIONS
    # ==========================================

    print("\n===== ALL COST OPTIONS =====")

    for option, cost in costs.items():

        print(
            f"{option}: ${cost:.2f} per month"
        )

    print(
        "\nDeployment analysis completed successfully."
    )


if __name__ == "__main__":

    main()