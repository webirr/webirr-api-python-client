import os

from webirr import WeBirrClient


def main():
    api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
    merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")

    # api_key = "YOUR_API_KEY"
    # merchant_id = "YOUR_MERCHANT_ID"

    api = WeBirrClient(merchant_id, api_key, True)

    date_from = "2025-01-01"  # YYYY-MM-DD
    date_to = "2030-01-31"  # YYYY-MM-DD

    print("\nRetrieving Statistics...")
    print(f"\nDate From: {date_from}")
    print(f"\nDate To: {date_to}")

    response = api.get_stat(date_from, date_to)

    if not response.error:
        # success
        stat = response.res
        print(f"\nNumber of Bills Created: {stat.n_bills}")
        print(f"\nNumber of Paid Bills: {stat.n_bills_paid}")
        print(f"\nNumber of Unpaid Bills: {stat.n_bills_unpaid}")
        print(f"\nAmount of Bills: {stat.amount_bills}")
        print(f"\nAmount Paid: {stat.amount_paid}")
        print(f"\nAmount Unpaid: {stat.amount_unpaid}")
    else:
        # fail
        print(f"\nError: {response.error}")
        print(f"\nError Code: {response.error_code}")


if __name__ == "__main__":
    main()
