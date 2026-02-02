"""Soundboard discovery routes."""

from typing import Any

from flask import render_template, request

from app.models import Soundboard


def register_discovery_routes(bp: Any) -> None:
    """Register discovery routes on the blueprint."""

    @bp.route("/gallery")  # type: ignore
    def gallery() -> Any:
        """
        Render the public gallery of soundboards.

        Query Args:
            sort (str): Sorting criteria ('recent', 'top', etc.).
        """
        sort_criteria = request.args.get("sort", "recent")
        public_soundboards = Soundboard.get_public(order_by=sort_criteria)
        return render_template(
            "soundboard/gallery.html",
            title="Public Gallery",
            soundboards=public_soundboards,
            current_sort=sort_criteria,
        )

    @bp.route("/search")  # type: ignore
    def search() -> Any:
        """
        Perform a global search for soundboards.

        Query Args:
            q (str): Search query.
            sort (str): Sorting criteria.
        """
        query_string = request.args.get("q", "")
        sort_criteria = request.args.get("sort", "recent")
        if query_string:
            matching_soundboards = Soundboard.search(
                query_string, order_by=sort_criteria
            )
        else:
            matching_soundboards = []
        return render_template(
            "soundboard/search.html",
            title="Search Results",
            soundboards=matching_soundboards,
            query=query_string,
            current_sort=sort_criteria,
        )

    @bp.route("/tag/<tag_name>")  # type: ignore
    def tag_search(tag_name: str) -> Any:
        """
        Search soundboards by tag.

        Args:
            tag_name (str): The tag name.
        """
        assert tag_name is not None
        soundboards = Soundboard.get_by_tag(tag_name)

        return render_template(
            "soundboard/search.html",
            title=f"Tag: {tag_name}",
            soundboards=soundboards,
            query=tag_name,
        )
