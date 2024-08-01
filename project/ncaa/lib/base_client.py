"""
Base class for NCAA client library code that provides session
configuration and NCAA authentication.
"""
import inspect
import os
import typing
import random

import requests
import requests.adapters
import requests.exceptions
import structlog
import urllib3.util.retry

NCAA_HOST_ONE = "https://api.sportsdata.io/v3"
NCAA_HOST_TWO = "https://api.sportradar.com/ncaafb/trial/v7/en/games"

class BaseClient(requests.Session):
    REQUEST_RETRIES = 5
    REQUEST_RETRY_BACKOFF_FACTOR = 0.3
    REQUEST_RETRY_STATUS_FORCELIST = [502, 504]
    REQUEST_METHOD_WHITELIST = [
        "HEAD",
        "GET",
        "PUT",
        "DELETE",
        "OPTIONS",
        "TRACE",
        "POST",
        "PATCH",
    ]

    def __init__(self, access_token: typing.Optional[str] = None, logger=None):
        """Initialize the HTTP request.Session components and authenticate to NCAA"""
        super().__init__()

        if logger is None:
            self.logger = structlog.get_logger()
        else:
            self.logger = logger

        self.logger.debug("BaseClient::__init__()")

        # Setup an HTTPS retry adapter
        retry = urllib3.util.retry.Retry(
            total=self.REQUEST_RETRIES,
            read=self.REQUEST_RETRIES,
            connect=self.REQUEST_RETRIES,
            backoff_factor=self.REQUEST_RETRY_BACKOFF_FACTOR,
            status_forcelist=self.REQUEST_RETRY_STATUS_FORCELIST,
            method_whitelist=self.REQUEST_METHOD_WHITELIST,
        )

        adapter = requests.adapters.HTTPAdapter(max_retries=retry)
        self.mount("https://", adapter)

        if access_token is not None:
            self.access_token = access_token

        else:
            sports_data_api_keys = os.environ["SPORTS_DATA_API_KEY"].split(",")
            random_sports_data_api_key = random.choice(sports_data_api_keys)
            self.access_token = random_sports_data_api_key

        self.headers.update({"Ocp-Apim-Subscription-Key": self.access_token})

    def assert_request(
        self,
        request_type: str,
        route: str,
        host_number: int,
        data: typing.Optional[typing.Union[typing.List, typing.Dict]] = None,
        json: typing.Optional[typing.Union[typing.List, typing.Dict]] = None,
    ) -> requests.Response:
        """Perform a generic HTTP request and log on exception"""
        if host_number == 1:
            NCAA_HOST = NCAA_HOST_ONE
        elif host_number == 2:
            NCAA_HOST = NCAA_HOST_TWO

        # Validate that a supported request type was given
        target_url = f"{NCAA_HOST}/{route}"
        if request_type not in BaseClient.REQUEST_METHOD_WHITELIST:
            self.logger.error(
                "unsupported request type given",
                method="BaseClient::assert_request()",
                request_type=request_type,
                url=target_url,
            )

            raise NotImplementedError

        try:
            if data is not None:
                response = self.request(
                    method=request_type,
                    url=target_url,
                    data=data,
                    headers=self.headers,
                )

            else:
                response = self.request(
                    method=request_type,
                    url=target_url,
                    json=json,
                    headers=self.headers,
                )

            response.raise_for_status()

        except requests.exceptions.ConnectionError:
            # Include the parent caller name that made the failing in the error info
            self.logger.error(
                "request connection error",
                method="BaseClient::assert_request()",
                parent_caller=inspect.stack()[1].function,
                request_type=request_type,
                url=target_url,
            )

            raise

        except requests.exceptions.RequestException as exception:
            # Include the parent caller name that made the failing in the error info
            error_info = {
                "method": "BaseClient::assert_request()",
                "parent_caller": inspect.stack()[1].function,
                "request_type": request_type,
                "url": target_url,
            }

            if hasattr(exception.response, "text"):
                error_info["reason"] = exception.response.text
            else:
                error_info["reason"] = ""

            self.logger.error("request failed", **error_info)
            raise

        return response

