import os

from webirr import WeBirrClient


def main():
    api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
    merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")

    api = WeBirrClient(merchant_id, api_key, True)

    bill_reference = os.getenv("WEBIRR_TEST_BILL_REFERENCE", "YOUR_BILL_REFERENCE")
    payment_code = os.getenv("WEBIRR_TEST_PAYMENT_CODE", "YOUR_PAYMENT_CODE")

    print("\nGetting bill by reference...")
    response = api.get_bill_by_reference(bill_reference)
    if not response.error:
        # success
        print("\nBill found by reference.")
        print(response.res)
    else:
        # fail
        print(f"\nError: {response.error}")
        print(f"\nError Code: {response.error_code}")

    print("\nGetting bill by payment code...")
    response = api.get_bill_by_payment_code(payment_code)
    if not response.error:
        # success
        print("\nBill found by payment code.")
        print(response.res)
    else:
        # fail
        print(f"\nError: {response.error}")
        print(f"\nError Code: {response.error_code}")

    print("\nListing bills...")
    payment_status = -1  # -1 all, 0 pending, 1 unconfirmed payment, 2 paid.
    last_time_stamp = "20251231"  # Date-only cursor; use "20251231235959" when you need time precision.
    limit = 10

    response = api.get_bills(payment_status, last_time_stamp, limit)
    if not response.error:
        # success
        print(f"\nBills returned: {len(response.res)}")
        for bill in response.res:
            print("\n-----------------------------")
            print(bill)
    else:
        # fail
        print(f"\nError: {response.error}")
        print(f"\nError Code: {response.error_code}")


if __name__ == "__main__":
    main()
