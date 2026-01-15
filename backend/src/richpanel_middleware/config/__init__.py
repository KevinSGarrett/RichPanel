import os


def _to_bool(value: str | None, default: bool = False) -> bool:
    """Parse common truthy strings into a boolean."""
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


# Opt-in flag to allow logging OpenAI response excerpts for debugging only.
# Defaults to False to keep logs free of model output / user content unless
# explicitly enabled via env.
OPENAI_LOG_RESPONSE_EXCERPT_DEFAULT = False


def openai_log_response_excerpt_enabled() -> bool:
    """Return whether response excerpt logging is explicitly enabled."""
    return _to_bool(
        os.environ.get("OPENAI_LOG_RESPONSE_EXCERPT"),
        default=OPENAI_LOG_RESPONSE_EXCERPT_DEFAULT,
    )
