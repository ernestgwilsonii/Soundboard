"""Soundboard forms."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import BooleanField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class SoundboardForm(FlaskForm):
    """Form to create or edit a soundboard."""

    name = StringField(
        "Soundboard Name", validators=[DataRequired(), Length(min=1, max=64)]
    )
    icon = StringField("Icon (Font Awesome class or URL)", validators=[Length(max=255)])
    icon_image = FileField(
        "Custom Icon Image (optional)",
        validators=[FileAllowed(["png", "jpg", "jpeg", "gif"], "Images only!")],
    )
    is_public = BooleanField("Public (Shared with everyone)")
    tags = StringField("Tags (comma separated)", validators=[Length(max=255)])
    theme_color = StringField("Theme Color", default="#0d6efd")
    theme_preset = SelectField(
        "Theme Style",
        choices=[
            ("default", "Classic (Bootstrap)"),
            ("dark", "Dark Mode"),
            ("neon", "Cyber Neon"),
            ("minimalist", "Minimalist"),
        ],
        default="default",
    )
    submit = SubmitField("Save")


class SoundForm(FlaskForm):
    """Form to upload a sound."""

    name = StringField("Sound Name", validators=[DataRequired(), Length(min=1, max=64)])
    audio_file = FileField(
        "Audio File",
        validators=[
            FileRequired(),
            FileAllowed(["mp3", "wav", "ogg"], "Audio files only!"),
        ],
    )
    icon = StringField("Icon (Font Awesome class)", validators=[Length(max=255)])
    icon_image = FileField(
        "Custom Icon Image (optional)",
        validators=[FileAllowed(["png", "jpg", "jpeg", "gif"], "Images only!")],
    )
    submit = SubmitField("Upload")


class CommentForm(FlaskForm):
    """Form to post a comment."""

    text = StringField("Comment", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Post Comment")


class PlaylistForm(FlaskForm):
    """Form to create or edit a playlist."""

    name = StringField(
        "Playlist Name", validators=[DataRequired(), Length(min=1, max=64)]
    )
    description = StringField("Description", validators=[Length(max=255)])
    is_public = BooleanField("Public (Shared with everyone)")
    submit = SubmitField("Save Playlist")


class ImportPackForm(FlaskForm):
    """Form to import a soundboard pack."""

    pack_file = FileField(
        "Soundboard Pack (.sbp)",
        validators=[
            FileRequired(),
            FileAllowed(["sbp", "zip"], "Soundboard Pack files only!"),
        ],
    )
    submit = SubmitField("Import Soundboard")