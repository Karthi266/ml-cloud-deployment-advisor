import requests


AZURE_PRICING_URL = (
    "https://prices.azure.com/api/retail/prices"
)

REGION = "centralindia"

AZURE_SKU = "Standard_D2s_v5"

MONTHLY_HOURS = 730


def get_azure_vm_price():

    print("\n========================================")
    print("       AZURE VM LIVE PRICING")
    print("========================================")

    print("\nProvider: Azure")
    print("Region:", REGION)
    print("VM SKU:", AZURE_SKU)
    print("OS: Linux")
    print("Pricing: On-Demand")

    try:

        query = (
            "serviceName eq 'Virtual Machines' "
            "and armRegionName eq '" + REGION + "' "
            "and armSkuName eq '" + AZURE_SKU + "' "
            "and priceType eq 'Consumption'"
        )

        response = requests.get(
            AZURE_PRICING_URL,
            params={
                "$filter": query,
                "currencyCode": "USD"
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        items = data.get("Items", [])

        print(
            "\nPricing records received:",
            len(items)
        )

        if not items:

            print(
                "\nNo Azure VM pricing records found."
            )

            return None

        # ==================================================
        # SEARCH FOR EXACT STANDARD ON-DEMAND PRICE
        # ==================================================

        valid_items = []

        for item in items:

            product_name = item.get(
                "productName",
                ""
            )

            sku_name = item.get(
                "skuName",
                ""
            )

            meter_name = item.get(
                "meterName",
                ""
            )

            price = item.get(
                "retailPrice"
            )

            unit = item.get(
                "unitOfMeasure",
                ""
            )

            effective_date = item.get(
                "effectiveStartDate"
            )

            # --------------------------------------------------
            # DISPLAY RECORD FOR DEBUGGING
            # --------------------------------------------------

            print("\n----------------------------------------")

            print(
                "Product:",
                product_name
            )

            print(
                "SKU:",
                sku_name
            )

            print(
                "Meter:",
                meter_name
            )

            print(
                "Unit:",
                unit
            )

            print(
                "Price:",
                price
            )

            # --------------------------------------------------
            # STRICT FILTERING
            # --------------------------------------------------

            # Exact SKU only
            if sku_name != AZURE_SKU:
                continue

            # Linux only
            if "Windows" in product_name:
                continue

            if "Windows" in sku_name:
                continue

            if "Windows" in meter_name:
                continue

            # Reject Low Priority
            if "Low Priority" in sku_name:
                continue

            if "Low Priority" in meter_name:
                continue

            # Reject Spot
            if "Spot" in sku_name:
                continue

            if "Spot" in meter_name:
                continue

            # Hourly price only
            if "Hour" not in unit:
                continue

            # Valid price
            if price is None:
                continue

            if float(price) <= 0:
                continue

            valid_items.append(item)

        # ==================================================
        # CHECK RESULTS
        # ==================================================

        if not valid_items:

            print(
                "\n========================================"
            )

            print(
                "NO STANDARD AZURE VM PRICE FOUND"
            )

            print(
                "========================================"
            )

            print(
                "\nThe Azure API returned records,"
                " but none matched:"
            )

            print(
                "Exact SKU:",
                AZURE_SKU
            )

            print(
                "Linux"
            )

            print(
                "On-Demand / Consumption"
            )

            print(
                "Hourly pricing"
            )

            return None

        # ==================================================
        # SELECT PRICE
        # ==================================================

        item = valid_items[0]

        product_name = item.get(
            "productName",
            ""
        )

        sku_name = item.get(
            "skuName",
            ""
        )

        meter_name = item.get(
            "meterName",
            ""
        )

        price = float(
            item.get("retailPrice")
        )

        unit = item.get(
            "unitOfMeasure",
            ""
        )

        effective_date = item.get(
            "effectiveStartDate"
        )

        # ==================================================
        # DISPLAY FINAL PRICE
        # ==================================================

        print(
            "\n========================================"
        )

        print(
            "       VALID AZURE VM PRICE"
        )

        print(
            "========================================"
        )

        print(
            "Product:",
            product_name
        )

        print(
            "SKU:",
            sku_name
        )

        print(
            "Meter:",
            meter_name
        )

        print(
            "Region:",
            REGION
        )

        print(
            "OS: Linux"
        )

        print(
            "Pricing: On-Demand"
        )

        print(
            "Unit:",
            unit
        )

        print(
            "Hourly price:",
            f"${price:.6f}"
        )

        print(
            "Effective:",
            effective_date
        )

        # ==================================================
        # MONTHLY COST
        # ==================================================

        monthly_cost = (
            price * MONTHLY_HOURS
        )

        print(
            "\nEstimated monthly cost:",
            f"${monthly_cost:.2f}"
        )

        # ==================================================
        # RETURN DATA
        # ==================================================

        return {

            "provider": "Azure",

            "service": "Azure VM",

            "region": REGION,

            "sku": sku_name,

            "os": "Linux",

            "pricing_model": "On-Demand",

            "price_per_hour": price,

            "monthly_hours": MONTHLY_HOURS,

            "estimated_monthly_cost":
                round(monthly_cost, 2),

            "currency": "USD",

            "unit": unit,

            "effective_start_date":
                effective_date
        }

    except requests.exceptions.RequestException as e:

        print(
            "\nAzure pricing API request failed:"
        )

        print(e)

        return None

    except Exception as e:

        print(
            "\nAzure VM pricing error:"
        )

        print(e)

        return None


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    result = get_azure_vm_price()

    if result:

        print(
            "\n========================================"
        )

        print(
            "       AZURE PRICING RESULT"
        )

        print(
            "========================================"
        )

        print(
            "\nProvider:",
            result["provider"]
        )

        print(
            "Service:",
            result["service"]
        )

        print(
            "Region:",
            result["region"]
        )

        print(
            "SKU:",
            result["sku"]
        )

        print(
            "OS:",
            result["os"]
        )

        print(
            "Pricing model:",
            result["pricing_model"]
        )

        print(
            "Hourly price:",
            f"${result['price_per_hour']:.6f}"
        )

        print(
            "Monthly hours:",
            result["monthly_hours"]
        )

        print(
            "Estimated monthly cost:",
            f"${result['estimated_monthly_cost']:.2f}"
        )

        print(
            "Effective date:",
            result["effective_start_date"]
        )

        print(
            "\nAzure VM live pricing retrieved successfully."
        )

    else:

        print(
            "\nAzure VM pricing could not be retrieved."
        )