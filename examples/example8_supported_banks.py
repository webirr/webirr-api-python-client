"""List banks enabled for the configured merchant checkout."""

import os

from webirr import WeBirrClient


def main():
    api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
    merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")

    api = WeBirrClient(merchant_id, api_key, True)

    print("\nGetting supported banks...")
    response = api.get_supported_banks()

    if not response.error:
        for bank in response.res or []:
            print(f"{bank.bank_id} - {bank.name}")
        print("\nUse only these merchant-specific banks when showing checkout payment instructions.")
    else:
        print(f"\nerror: {response.error}")
        print(f"\nerrorCode: {response.error_code}")


if __name__ == "__main__":
    main()
