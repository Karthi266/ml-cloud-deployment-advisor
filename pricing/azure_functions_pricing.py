import requests

AZURE_PRICING_URL = (
    "https://prices.azure.com/api/retail/prices"
)

REGION = "centralindia"


def get_azure_functions_pricing():

    try:
        query = (
            "serviceName eq 'Functions' "
            "and armRegionName eq '"
            + REGION
            + "' "
            "and priceType eq 'Consumption'"
        )

        response = requests.get(
            AZURE_PRICING_URL,
            params={
                "$filter": query,
                "$top": 100
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()
        items = data.get("Items", [])

        execution_price = None
        execution_time_price = None

        for item in items:

            sku = item.get("skuName", "")
            meter = item.get("meterName", "")
            price = item.get("retailPrice")
            unit = item.get("unitOfMeasure")

            if sku != "Standard":
                continue

            if "Total Executions" in meter:
                if price is not None:
                    execution_price = price

            elif "Execution Time" in meter:
                if price is not None:
                    execution_time_price = price

        print("\n===== AZURE FUNCTIONS PRICING =====")
        print("Region:", REGION)

        if execution_price is not None:
            print(
                "Execution price:",
                execution_price,
                "USD per 10 executions"
            )
        else:
            print("Execution price not found.")

        if execution_time_price is not None:
            print(
                "Execution time price:",
                execution_time_price,
                "USD per GB-second"
            )
        else:
            print("Execution time price not found.")

        if (
            execution_price is not None
            and execution_time_price is not None
        ):
            print("\nAzure Functions pricing retrieved successfully.")

            return {
                "region": REGION,
                "execution_price_per_10": execution_price,
                "execution_time_price_per_gb_second":
                    execution_time_price
            }

        return None

    except Exception as e:

        print("\nAzure Functions pricing error:")
        print(e)

        return None


if __name__ == "__main__":

    result = get_azure_functions_pricing()

    if result:
        print("\n===== FINAL PRICING DATA =====")
        print(result)