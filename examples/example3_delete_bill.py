import os

from webirr import WeBirrClient


def main():
    api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
    merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")

    # api_key = "YOUR_API_KEY"
    # merchant_id = "YOUR_MERCHANT_ID"

    api = WeBirrClient(merchant_id, api_key, True)
    payment_code = "PAYMENT_CODE_YOU_SAVED_AFTER_CREATING_A_NEW_BILL"

    print("\nDeleting Bill...")
    res = api.delete_bill(payment_code)

    if not res.error:
        # success
        print("\nbill is deleted succesfully")  # res.res will be 'OK'  no need to check here!
    else:
        # fail
        print(f"\nerror: {res.error}")
        print(f"\nerrorCode: {res.error_code}")  # can be used to handle specific business error such as ERROR_INVALID_INPUT


if __name__ == "__main__":
    main()
