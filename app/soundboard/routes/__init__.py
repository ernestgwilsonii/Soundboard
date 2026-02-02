"""Soundboard routes package."""

from typing import Any


def register_routes(bp: Any) -> None:
    """Register all routes for the soundboard blueprint."""
    from .board_mgmt import register_board_mgmt_routes
    from .collaborators import register_collaborator_routes
    from .discovery import register_discovery_routes
    from .playlists import register_playlist_routes
    from .social import register_social_routes
    from .sound_mgmt import register_sound_mgmt_routes

    register_board_mgmt_routes(bp)
    register_collaborator_routes(bp)
    register_discovery_routes(bp)
    register_playlist_routes(bp)
    register_social_routes(bp)
    register_sound_mgmt_routes(bp)
