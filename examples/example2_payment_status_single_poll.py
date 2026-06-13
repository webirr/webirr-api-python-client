import os

from webirr import WeBirrClient


def main():
    api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
    merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")

    # api_key = "YOUR_API_KEY"
    # merchant_id = "YOUR_MERCHANT_ID"

    api = WeBirrClient(merchant_id, api_key, True)
    payment_code = "PAYMENT_CODE_YOU_SAVED_AFTER_CREATING_A_NEW_BILL"

    print("\nGetting Payment Status...")
    res = api.get_payment_status(payment_code)

    if not res.error:
        # success
        if res.res and res.res.is_paid:
            payment = res.res.data
            print("\nbill is paid")
            print("\nbill payment detail")
            print(f"\nBank: {payment.bank_id}")
            print(f"\nBank Reference Number: {payment.payment_reference}")
            print(f"\nAmount Paid: {payment.amount}")
            print(f"\nPayment Date: {payment.payment_date}")
        else:
            print("\nbill is pending payment")
    else:
        # fail
        print(f"\nerror: {res.error}")
        print(f"\nerrorCode: {res.error_code}")  # can be used to handle specific business error such as ERROR_INVALID_INPUT


if __name__ == "__main__":
    main()
