"""Trusted infrastructure adapters for the authority boundary."""

from .promoted_runtime import PromotedCodexRuntime, RuntimeAdapterError

__all__ = ["PromotedCodexRuntime", "RuntimeAdapterError"]
