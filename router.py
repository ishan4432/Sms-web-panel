from providers.providers import PROVIDERS


def select_provider(phone_number):

    for provider_id, provider in PROVIDERS.items():

        for country_code in provider["countries"]:

            if phone_number.startswith(country_code):

                return provider

    return PROVIDERS["backup_provider"]

