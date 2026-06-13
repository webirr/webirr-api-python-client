import os
from datetime import datetime

from webirr import Bill, WeBirrClient


def main():
    api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
    merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")

    # api_key = "YOUR_API_KEY"
    # merchant_id = "YOUR_MERCHANT_ID"

    api = WeBirrClient(merchant_id, api_key, True)

    bill = Bill()
    bill.amount = "270.90"
    bill.customer_code = "cc01"  # it can be email address or phone number if you dont have customer code
    bill.customer_name = "Elias Haileselassie"
    bill.customer_phone = "0911000000"  # optional; used for SMS notification when enabled for the merchant
    bill.time = "2021-07-22 22:14"  # your bill time, always in this format
    bill.description = "hotel booking"
    bill.bill_reference = "python/example/" + datetime.now().strftime("%Y%m%d%H%M%S")  # your unique reference number

    print("\nCreating Bill...")
    res = api.create_bill(bill)

    if not res.error:
        # success
        payment_code = res.res  # returns paymentcode such as 429 723 975
        print(f"\nPayment Code = {payment_code}")  # we may want to save payment code in local db.
    else:
        # fail
        print(f"\nerror: {res.error}")
        print(f"\nerrorCode: {res.error_code}")  # can be used to handle specific business error such as ERROR_INVALID_INPUT_DUP_REF

    # Update existing bill if it is not paid
    bill.amount = "278.00"
    bill.customer_name = "Elias python"
    # bill.bill_reference = "WE CAN NOT CHANGE THIS"

    print("\nUpdating Bill...")
    res = api.update_bill(bill)

    if not res.error:
        # success
        print("\nbill is updated succesfully")  # res.res will be 'OK'  no need to check here!
    else:
        # fail
        print(f"\nerror: {res.error}")
        print(f"\nerrorCode: {res.error_code}")  # can be used to handle specific business error such as ERROR_INVALID_INPUT


if __name__ == "__main__":
    main()
