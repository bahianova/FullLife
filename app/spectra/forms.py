from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField, DecimalField
from wtforms.validators import DataRequired


class SpectrumForm(FlaskForm):
    title = FileField('Filename', validators=[FileRequired(), FileAllowed(['csv', 'txt'])])
    submit = SubmitField('Upload')


class SpectrumOptionsForm(FlaskForm):
    option = DecimalField(places=1, validators=[DataRequired()])
    submit = SubmitField('Run')


class SpectrumSaveForm(FlaskForm):
    title = FileField('Filename', validators=[FileRequired(), FileAllowed(['csv', 'txt'])])
    submit = SubmitField('Save')
