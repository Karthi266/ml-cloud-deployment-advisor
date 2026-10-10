import boto3
import json


# ---------------------------------------------------------
# AWS EC2 PRICING CONFIGURATION
# ---------------------------------------------------------

PRICING_REGION = "us-east-1"

# EC2 region whose price we want to retrieve.
# ap-south-1 = Mumbai
EC2_REGION = "ap-south-1"

# Comparable small Linux instance.
INSTANCE_TYPE = "t3.micro"

OPERATING_SYSTEM = "Linux"

TENANCY = "Shared"

PREINSTALLED_SOFTWARE = "NA"

CAPACITY_STATUS = "Used"


# ---------------------------------------------------------
# GET EC2 ON-DEMAND PRICE
# ---------------------------------------------------------

def get_aws_ec2_price():

    try:

        pricing_client = boto3.client(
            "pricing",
            region_name=PRICING_REGION
        )

        filters = [

            {
                "Type": "TERM_MATCH",
                "Field": "ServiceCode",
                "Value": "AmazonEC2"
            },

            {
                "Type": "TERM_MATCH",
                "Field": "location",
                "Value": "Asia Pacific (Mumbai)"
            },

            {
                "Type": "TERM_MATCH",
                "Field": "instanceType",
                "Value": INSTANCE_TYPE
            },

            {
                "Type": "TERM_MATCH",
                "Field": "operatingSystem",
                "Value": OPERATING_SYSTEM
            },

            {
                "Type": "TERM_MATCH",
                "Field": "tenancy",
                "Value": TENANCY
            },

            {
                "Type": "TERM_MATCH",
                "Field": "preInstalledSw",
                "Value": PREINSTALLED_SOFTWARE
            },

            {
                "Type": "TERM_MATCH",
                "Field": "capacitystatus",
                "Value": CAPACITY_STATUS
            },

            {
                "Type": "TERM_MATCH",
                "Field": "productFamily",
                "Value": "Compute Instance"
            }
        ]

        response = pricing_client.get_products(
            ServiceCode="AmazonEC2",
            Filters=filters,
            FormatVersion="aws_v1",
            MaxResults=10
        )

        products = response.get(
            "PriceList",
            []
        )

        if not products:

            print(
                "\nNo matching AWS EC2 pricing found."
            )

            return None

        for product_json in products:

            product = json.loads(
                product_json
            )

            terms = product.get(
                "terms",
                {}
            )

            on_demand = terms.get(
                "OnDemand",
                {}
            )

            for term in on_demand.values():

                price_dimensions = term.get(
                    "priceDimensions",
                    {}
                )

                for dimension in price_dimensions.values():

                    price = dimension.get(
                        "pricePerUnit",
                        {}
                    ).get(
                        "USD"
                    )

                    if price is not None:

                        attributes = product.get(
                            "product",
                            {}
                        ).get(
                            "attributes",
                            {}
                        )

                        return {
                            "provider":
                                "AWS EC2",

                            "region":
                                EC2_REGION,

                            "location":
                                attributes.get(
                                    "location"
                                ),

                            "instance_type":
                                attributes.get(
                                    "instanceType"
                                ),

                            "vcpu":
                                attributes.get(
                                    "vcpu"
                                ),

                            "memory":
                                attributes.get(
                                    "memory"
                                ),

                            "operating_system":
                                attributes.get(
                                    "operatingSystem"
                                ),

                            "tenancy":
                                attributes.get(
                                    "tenancy"
                                ),

                            "price_per_hour":
                                float(price),

                            "currency":
                                "USD"
                        }

        print(
            "\nAWS EC2 On-Demand price "
            "could not be extracted."
        )

        return None

    except Exception as e:

        print(
            "\nAWS EC2 pricing error:"
        )

        print(e)

        return None


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    result = get_aws_ec2_price()

    print(
        "\n========================================"
    )

    print(
        "       AWS EC2 LIVE PRICING"
    )

    print(
        "========================================"
    )

    if result:

        print(
            "Provider:",
            result["provider"]
        )

        print(
            "Region:",
            result["region"]
        )

        print(
            "Location:",
            result["location"]
        )

        print(
            "Instance:",
            result["instance_type"]
        )

        print(
            "vCPU:",
            result["vcpu"]
        )

        print(
            "Memory:",
            result["memory"]
        )

        print(
            "Operating System:",
            result["operating_system"]
        )

        print(
            "Price:",
            result["price_per_hour"],
            "USD/hour"
        )

        print(
            "\nAWS EC2 pricing retrieved successfully."
        )

    else:

        print(
            "\nAWS EC2 pricing retrieval failed."
        )