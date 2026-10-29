"""Shared public API blueprint; domain modules register existing endpoint names."""

from flask import Blueprint

bp = Blueprint("api", __name__)
