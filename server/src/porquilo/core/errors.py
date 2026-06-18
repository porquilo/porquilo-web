from typing import NoReturn

AUTH_ERROR_CODES: dict[str, tuple[int, str]] = {
    "invalid_credentials": (400, "That username and password don't match."),
    "token_revoked":       (401, "You've been logged out. Log in again."),
    "token_expired":       (401, "Your session expired. Log in again."),
    "account_deactivated": (403, "This account has been deactivated."),
    "insufficient_role":   (403, "This action needs an admin account."),
    "too_many_attempts":   (429, "Too many attempts. Try again in a few minutes."),
    "validation_error":    (422, "Validation failed."),
    "internal_error":      (500, "Something went wrong."),
}


class PorquiloError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        details: dict | None = None,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


def raise_auth_error(code: str) -> NoReturn:
    status_code, message = AUTH_ERROR_CODES[code]
    raise PorquiloError(code=code, message=message, status_code=status_code)
