"""Application constants."""

# Pagination
DEFAULT_PAGE_SIZE = 10
LARGE_PAGE_SIZE = 20
MAX_ITEMS_PER_PAGE = 50

# Audio Processing
NORMALIZATION_TARGET_DBFS = -20.0

# Display Limits
SIDEBAR_ACTIVITY_LIMIT = 10
SIDEBAR_NOTIFICATION_LIMIT = 5
EXPLORE_BOARD_LIMIT = 6
POPULAR_TAGS_LIMIT = 10

# Rate Limiting
LOGIN_LIMIT = "10 per minute"
UPLOAD_LIMIT = "5 per minute"
REGISTRATION_LIMIT = "5 per hour"
COMMENT_LIMIT = "10 per minute"
RATING_LIMIT = "20 per minute"

# Default UI Values
DEFAULT_SOUNDBOARD_ICON = "fas fa-music"
DEFAULT_SOUNDBOARD_COLOR = "#0d6efd"
DEFAULT_SOUND_ICON = "fas fa-volume-up"
