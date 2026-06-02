"""Typed exceptions + canonical exit codes."""


class AirtError(Exception):
    """Base error."""


class ConfigError(AirtError):
    """Bad or missing configuration / malformed corpus."""


class AuthorizationError(AirtError):
    """Target not on the ROE allow-list / not authorized."""


class TargetError(AirtError):
    """Transport-level failure talking to the target."""


class JudgeError(AirtError):
    """Judge backend failure."""


# Exit codes used by cli.py
EXIT_OK = 0
EXIT_GATE_FAIL = 1
EXIT_USAGE = 2
EXIT_AUTHORIZATION = 3
EXIT_INTERNAL = 4
