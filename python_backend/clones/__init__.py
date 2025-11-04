"""
Expert Cognitive Clones - Framework EXTRACT Implementation

This package contains all cognitive clone implementations using the 
20-point Framework EXTRACT methodology for maximum fidelity.

Each clone is a Python class with:
- Story banks (real cases with metrics)
- Iconic callbacks (signature phrases)
- Triggers (behavioral activation)
- Rich system prompts (Framework EXTRACT)

Auto-discovery via CloneRegistry.
"""

from .base import ExpertCloneBase
from .registry import CloneRegistry, clone_registry

__all__ = [
    "ExpertCloneBase",
    "CloneRegistry",
    "clone_registry",
]
