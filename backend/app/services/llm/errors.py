class LlmError(Exception):
    """Base error for LLM provider failures."""


class LlmConfigurationError(LlmError):
    """Raised when LLM provider configuration is incomplete."""


class LlmApiError(LlmError):
    """Raised when the provider returns an unusable response."""


class LlmInvalidJsonError(LlmError):
    """Raised when the model response cannot be parsed as JSON."""
