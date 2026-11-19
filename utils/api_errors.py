"""API response error formatting."""


def get_api_error(result):
    """Return a user-facing detail from an API response."""
    if isinstance(result, dict):
        return result.get("detail", str(result))
    return str(result)
