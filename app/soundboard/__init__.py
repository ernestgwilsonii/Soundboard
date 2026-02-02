"""Soundboard blueprint package."""

from flask import Blueprint

bp = Blueprint("soundboard", __name__, url_prefix="/soundboard")

from .routes import register_routes  # noqa: E402

register_routes(bp)
