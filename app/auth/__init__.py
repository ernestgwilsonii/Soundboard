"""Authentication blueprint package."""

from flask import Blueprint

bp = Blueprint("auth", __name__, url_prefix="/auth")

from .routes import register_routes  # noqa: E402

register_routes(bp)
