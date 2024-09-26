from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post:
class NewPost(FlaskForm):
    post_title = StringField('Post Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    # author_name = StringField("Author's Name", validators=[DataRequired()])
    bg_img_url = StringField("URL for Background Image", validators=[DataRequired()])
    post_content = CKEditorField("Body of the Post", validators=[DataRequired()])
    submit = SubmitField('Create')


# Create a RegisterForm to register new users:
class RegisterForm(FlaskForm):
    name = StringField('User Name', validators=[DataRequired()])
    email = StringField('Enter Email', validators=[DataRequired()])
    password = PasswordField('Choose Password:', validators=[DataRequired()])
    submit = SubmitField('Register')


# Create a LoginForm to login existing users:
class LoginForm(FlaskForm):
    email = StringField('Enter Email', validators=[DataRequired()])
    password = PasswordField('Enter Password:', validators=[DataRequired()])
    submit = SubmitField('LogIn')


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
