"""Load public API domains while preserving api.* endpoint identities."""

from .blueprint import bp as bp
from . import players, teams_venues, records, matches, metadata, predictions  # noqa: F401
