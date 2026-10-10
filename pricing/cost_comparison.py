from pricing.cost_calculator import calculate_cloud_cost
from pricing.vm_cost_calculator import calculate_vm_cost


def compare_costs(workload):

    print("\n===== COST COMPARISON =====")


    # ==========================================
    # CLOUD COST
    # ==========================================

    cloud_costs = calculate_cloud_cost(
        workload
    )


    # ==========================================
    # DEDICATED VM COST
    # ==========================================

    vm_cost = calculate_vm_cost(
        workload
    )


    # ==========================================
    # DISPLAY COSTS
    # ==========================================

    print(
        f"Dedicated VM: "
        f"${vm_cost:.2f} per month"
    )


    for provider, cost in cloud_costs.items():

        print(
            f"{provider}: "
            f"${cost:.2f} per month"
        )


    # ==========================================
    # COMBINE OPTIONS
    # ==========================================

    all_options = {

        "Dedicated VM": vm_cost,

        **cloud_costs

    }


    # ==========================================
    # FIND CHEAPEST OPTION
    # ==========================================

    cheapest_option = min(
        all_options,
        key=all_options.get
    )


    cheapest_cost = (
        all_options[cheapest_option]
    )


    print(
        "\n===== CHEAPEST OPTION ====="
    )

    print(
        "Recommended option:",
        cheapest_option
    )

    print(
        f"Estimated cost: "
        f"${cheapest_cost:.2f} per month"
    )


    return all_options


# ==========================================
# TEST
# ==========================================

if __name__ == "__main__":

    test_workload = {

        "request_volume": 100000,

        "request_duration": 0.2

    }


    costs = compare_costs(
        test_workload
    )


    print(
        "\n===== FINAL COST TABLE ====="
    )


    for option, cost in costs.items():

        print(
            f"{option}: "
            f"${cost:.2f} / month"
        )