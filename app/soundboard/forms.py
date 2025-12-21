from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class SoundboardForm(FlaskForm):
    name = StringField('Soundboard Name', validators=[DataRequired(), Length(min=1, max=64)])
    icon = StringField('Icon (Font Awesome class or URL)', validators=[Length(max=255)])
    submit = SubmitField('Save')
