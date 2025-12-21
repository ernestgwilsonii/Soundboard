from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class SoundboardForm(FlaskForm):
    name = StringField('Soundboard Name', validators=[DataRequired(), Length(min=1, max=64)])
    icon = StringField('Icon (Font Awesome class or URL)', validators=[Length(max=255)])
    submit = SubmitField('Save')

class SoundForm(FlaskForm):
    name = StringField('Sound Name', validators=[DataRequired(), Length(min=1, max=64)])
    audio_file = FileField('Audio File', validators=[
        FileRequired(),
        FileAllowed(['mp3', 'wav', 'ogg'], 'Audio files only!')
    ])
    icon = StringField('Icon (Font Awesome class)', validators=[Length(max=255)])
    submit = SubmitField('Upload')
