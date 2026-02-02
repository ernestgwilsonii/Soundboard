"""Auth routes package."""

from typing import Any


def register_routes(bp: Any) -> None:
    """Register all routes for the auth blueprint."""
    from .auth_flow import register_auth_flow_routes
    from .profile import register_profile_routes
    from .social import register_social_routes
    from .verification import register_verification_routes

    register_auth_flow_routes(bp)
    register_profile_routes(bp)
    register_social_routes(bp)
    register_verification_routes(bp)
