"""Check modules, grouped A/B/C/G.

Importing this package populates the implementation registry (IMPLS) as a
side effect of importing each group module.
"""

from .base import IMPLS, Module, get_impl, has_impl  # noqa: F401
from . import group_b  # noqa: F401  (registers B-group implementations)
from . import group_g  # noqa: F401  (registers G-group implementations)
from . import group_n  # noqa: F401  (registers N-group implementations)
