from dataclasses import dataclass


class BasePS3838Error(Exception):
    pass


class ResponseError(BasePS3838Error):
    pass


class AccessBlockedError(ResponseError):
    """
    Raised when the API returns an empty response, likely due to access restrictions.

    This may not be a strict rate limit. In many cases, it indicates that the account
    needs to meet certain behavioral criteria — such as placing $30–$40 in manual bets per day —
    before automated requests are allowed again.
    """

    pass


class WrongEndpoint(ResponseError):
    """405 HTTP Error"""

    pass


@dataclass
class PS3838APIError(ResponseError):
    code: str | None
    message: str | None


class LogicError(BasePS3838Error):
    """Raised when there is a violation of client-side logic or input invariant."""

    pass


class BaseballOnlyArgumentError(LogicError):
    pass
