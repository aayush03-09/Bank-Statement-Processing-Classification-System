"""Classification engine wrapper.

Provides a stable import path for the hybrid classifier used by tests and
other modules.
"""

from .hybrid_classifier import classify_transaction  # noqa: F401
