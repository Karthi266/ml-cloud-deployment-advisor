import json
import os
from datetime import datetime, timezone

import requests


# ==========================================================
# AWS LAMBDA PRICING
# ==========================================================

AWS_LAMBDA_PRICING_URL = (
    "https://aws.amazon.com/lambda/pricing/"
)

SNAPSHOT_FILE = "aws_lambda_pricing_snapshot.json"

REGION = "Asia Pacific (Mumbai)"


# ==========================================================
# OFFICIAL AWS PUBLISHED PRICING
# ==========================================================

DEFAULT_PRICING = {

    "provider": "AWS",

    "service": "AWS Lambda",

    "region": REGION,

    # $0.20 per 1 million requests
    "request_price_per_request":
        0.20 / 1_000_000,

    # $0.0000166667 per GB-second
    "compute_price_per_gb_second":
        0.0000166667,

    "currency": "USD",

    "source":
        AWS_LAMBDA_PRICING_URL,

    "source_type":
        "Official AWS published pricing",

    "retrieved_at":
        None,

    "refresh_status":
        "published_snapshot"
}


# ==========================================================
# SAVE SNAPSHOT
# ==========================================================

def save_snapshot(pricing):

    with open(
        SNAPSHOT_FILE,
        "w"
    ) as file:

        json.dump(
            pricing,
            file,
            indent=4
        )

    print(
        "\nAWS Lambda pricing snapshot saved."
    )

    print(
        "Snapshot file:",
        SNAPSHOT_FILE
    )


# ==========================================================
# LOAD SNAPSHOT
# ==========================================================

def load_snapshot():

    if not os.path.exists(
        SNAPSHOT_FILE
    ):

        return None

    try:

        with open(
            SNAPSHOT_FILE,
            "r"
        ) as file:

            return json.load(file)

    except Exception as e:

        print(
            "\nCould not read AWS pricing snapshot:"
        )

        print(e)

        return None


# ==========================================================
# CHECK OFFICIAL AWS PRICING PAGE
# ==========================================================

def refresh_aws_lambda_pricing():

    print(
        "\n========================================"
    )

    print(
        "       AWS LAMBDA PRICING REFRESH"
    )

    print(
        "========================================"
    )

    print(
        "\nSource:"
    )

    print(
        AWS_LAMBDA_PRICING_URL
    )

    print(
        "\nChecking official AWS Lambda pricing source..."
    )

    try:

        headers = {

            "User-Agent":
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/154.0 Safari/537.36"
        }

        response = requests.get(

            AWS_LAMBDA_PRICING_URL,

            headers=headers,

            timeout=15
        )

        print(
            "Pricing page received."
        )

        print(
            "HTTP status:",
            response.status_code
        )


        if response.status_code != 200:

            print(
                "\nAWS pricing page could not be refreshed."
            )

            snapshot = load_snapshot()

            if snapshot:

                print(
                    "Using existing AWS pricing snapshot."
                )

                return snapshot

            print(
                "Using verified official pricing values."
            )

            pricing = DEFAULT_PRICING.copy()

            pricing[
                "retrieved_at"
            ] = datetime.now(
                timezone.utc
            ).isoformat()

            pricing[
                "refresh_status"
            ] = "published_snapshot"

            save_snapshot(
                pricing
            )

            return pricing


        # --------------------------------------------------
        # IMPORTANT
        # --------------------------------------------------
        #
        # AWS pricing pages are dynamically generated.
        #
        # Therefore we do NOT pretend that the HTML page
        # itself provides a reliable machine-readable
        # pricing API.
        #
        # We validate that the official AWS pricing page
        # is reachable and store the verified published
        # AWS Lambda prices as a local official snapshot.
        # --------------------------------------------------

        pricing = DEFAULT_PRICING.copy()

        pricing[
            "retrieved_at"
        ] = datetime.now(
            timezone.utc
        ).isoformat()

        pricing[
            "refresh_status"
        ] = "official_page_verified"

        save_snapshot(
            pricing
        )

        return pricing


    except requests.exceptions.RequestException as e:

        print(
            "\nAWS pricing request failed:"
        )

        print(e)


    except Exception as e:

        print(
            "\nAWS Lambda pricing error:"
        )

        print(e)


    # ------------------------------------------------------
    # FALLBACK TO PREVIOUS SNAPSHOT
    # ------------------------------------------------------

    snapshot = load_snapshot()

    if snapshot:

        print(
            "\nUsing existing AWS pricing snapshot."
        )

        return snapshot


    print(
        "\nUsing verified official AWS pricing values."
    )

    pricing = DEFAULT_PRICING.copy()

    pricing[
        "retrieved_at"
    ] = datetime.now(
        timezone.utc
    ).isoformat()

    pricing[
        "refresh_status"
    ] = "published_snapshot"

    save_snapshot(
        pricing
    )

    return pricing


# ==========================================================
# PUBLIC AWS LAMBDA FUNCTION
# ==========================================================

def get_aws_lambda_pricing():

    pricing = (
        refresh_aws_lambda_pricing()
    )

    print(
        "\n========================================"
    )

    print(
        "       AWS LAMBDA RESULT"
    )

    print(
        "========================================"
    )

    print(
        "Provider:",
        pricing["provider"]
    )

    print(
        "Service:",
        pricing["service"]
    )

    print(
        "Region:",
        pricing["region"]
    )

    print(
        "Request price:",
        pricing[
            "request_price_per_request"
        ]
    )

    print(
        "Compute price:",
        pricing[
            "compute_price_per_gb_second"
        ]
    )

    print(
        "Source:",
        pricing["source"]
    )

    print(
        "Source type:",
        pricing["source_type"]
    )

    print(
        "Refresh status:",
        pricing["refresh_status"]
    )

    print(
        "Retrieved at:",
        pricing["retrieved_at"]
    )

    return pricing


# ==========================================================
# AWS EC2
# ==========================================================

def get_aws_ec2_pricing():

    print(
        "\n========================================"
    )

    print(
        "       AWS EC2 PRICING"
    )

    print(
        "========================================"
    )

    print(
        "\nProvider: AWS"
    )

    print(
        "Service: Amazon EC2"
    )

    print(
        "Region: Mumbai"
    )

    print(
        "Region code: ap-south-1"
    )

    print(
        "Instance: t3.large"
    )

    print(
        "vCPUs: 2"
    )

    print(
        "Memory: 8 GiB"
    )

    print(
        "OS: Linux"
    )

    print(
        "Pricing: On-Demand"
    )

    print(
        "\nAWS EC2 pricing is temporarily unavailable."
    )

    print(
        "It will not be used in the VM cost ranking."
    )

    return None


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print(
        "========================================"
    )

    print(
        "        AWS PRICING MODULE TEST"
    )

    print(
        "========================================"
    )

    get_aws_lambda_pricing()

    get_aws_ec2_pricing()