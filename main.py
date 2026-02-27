import requests
import smtplib
import twilio
from twilio.rest import Client
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, send_from_directory
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
# from flask_gravatar import Gravatar
from hashlib import md5
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from forms import NewPost, RegisterForm, LoginForm, CommentForm
from functools import wraps
from flask import abort
import os


# Email and Password for SMTPLIB:
my_email = "cwdebojyoti@gmail.com"
password = os.environ.get("SMTP_PASS")

client = Client(os.environ.get("TWILIO_SID"), os.environ.get("TWILIO_AUTH_TOKEN"))



app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("APP_SEC_KEY")
app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = '465' 
app.config['MAIL_USE_TLS'] = False 
app.config['MAIL_USE_SSL'] = True
Bootstrap5(app)
ckeditor = CKEditor(app)
app.config['CKEDITOR_PKG_TYPE'] = 'full'
app.config['CKEDITOR_CODE_SNIPPET'] = True

# Creating and initiating Login manager for Flask login:
login_manager = LoginManager()
login_manager.init_app(app)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:ubuntu@localhost/blogs'
db = SQLAlchemy(model_class=Base)
db.init_app(app)



def avatar(email):
    digest = md5(email.lower().encode('utf-8')).hexdigest()
    return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={30}'


# CONFIGURE TABLE

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key= True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)

    #This will act like a List of BlogPost objects attached to each User. 
    #The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")

    role: Mapped[str] = mapped_column(String(250), nullable= False, default= 'admin')

    #*******Add parent relationship*******#
    #"comment_author" refers to the comment_author property in the Comment class.
    comments: Mapped[str] = relationship("Comment", back_populates="comment_author")



class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")

    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))

    comments = relationship("Comment", back_populates="parent_post")

    subject: Mapped[str] = mapped_column(String(100), nullable= False)

    status: Mapped[str] = mapped_column(String(10), nullable= False)



class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    #*******Add child relationship*******#
    #"users.id" The users refers to the tablename of the Users class.
    #"comments" refers to the comments property in the User class.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    # Child Relationship to the BlogPosts
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)




#Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)        
    return decorated_function


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route("/")
def home():
    # blog_url = "https://api.npoint.io/9586e0ab5fd38c29ef51"
    # response = requests.get(blog_url)
    # all_post = response.json()
    current_year = datetime.now().year
    result = db.session.execute(db.select(BlogPost).where(BlogPost.status == "Published"))
    all_post = result.scalars().all()
    return render_template("index.html", posts = all_post, year = current_year, logged_in = current_user.is_authenticated)


@app.route("/drafts")
def drafts():
    current_year = datetime.now().year
    result = db.session.execute(db.select(BlogPost).where(BlogPost.status == "Draft"))
    all_post = result.scalars().all()
    return render_template("drafts.html", posts = all_post, year = current_year, logged_in = current_user.is_authenticated)


@app.route("/coding_blog")
def coding_blog():
    current_year = datetime.now().year
    result = db.session.execute(db.select(BlogPost).where((BlogPost.subject == "Code") & (BlogPost.status == "Published")))
    coding_post = result.scalars().all()
    return render_template("index_code.html", posts = coding_post, year = current_year, logged_in = current_user.is_authenticated)


@app.route("/chemistry_blog")
def chemistry_blog():
    current_year = datetime.now().year
    result = db.session.execute(db.select(BlogPost).where((BlogPost.subject == "Chemistry") & (BlogPost.status == "Published")))
    coding_post = result.scalars().all()
    return render_template("index_chemistry.html", posts = coding_post, year = current_year, logged_in = current_user.is_authenticated)


@app.route('/register', methods = ['GET', 'POST'])
def register():
    current_year = datetime.now().year
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        email = register_form.email.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user_to_add = result.scalar()
        if user_to_add:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        else:
            new_user = User(
                name = register_form.name.data,
                email = register_form.email.data,
                password = generate_password_hash(register_form.password.data, method= 'pbkdf2:sha256', salt_length= 8)
            )
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)

            return redirect(url_for("home"))
        
    return render_template("register.html", form = register_form, year = current_year, logged_in = current_user.is_authenticated)


@app.route('/login', methods = ['GET', 'POST'])
def login():
    current_year = datetime.now().year
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user_to_login = result.scalar()
        if not user_to_login:
            flash("This email does not exist!")
            return redirect(url_for('login'))
        elif not check_password_hash(user_to_login.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user_to_login)
            return redirect(url_for('home'))
        
    return render_template("login.html", form = login_form, year = current_year, logged_in = current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
    


@app.route("/about")
def about():
    current_year = datetime.now().year
    return render_template("about.html", year = current_year, logged_in = current_user.is_authenticated)


@app.route("/contact", methods = ["GET", "POST"])
def contact():
    if request.method == "POST":
        data = request.form
        name = data["name"]
        user_email = data["email"]
        phone = data["phone"]
        message = data["message"]
        # print(f"Name: {name}\nemail: {user_email}\nPhone: {phone}\nMessage: {message}")
        send_message(name, user_email, phone, message)

        heading = "Message submitted successfully!"
        current_year = datetime.now().year
        return render_template("contact.html", text = heading, year = current_year, logged_in = current_user.is_authenticated)
    else:
        heading = "Contact Me"
        current_year = datetime.now().year
        return render_template("contact.html", text = heading, year = current_year, logged_in = current_user.is_authenticated)


@app.route("/post/<int:num>", methods = ['GET', 'POST'])
def post(num):
    # blog_url = "https://api.npoint.io/9586e0ab5fd38c29ef51"
    # response = requests.get(blog_url)
    # all_post = response.json()
    
    current_year = datetime.now().year
    requested_post = db.get_or_404(BlogPost, num)

    comment_form = CommentForm()

    # Only allow logged-in users to comment on posts
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post,
            
        )
        db.session.add(new_comment)
        db.session.commit()

    return render_template("post.html", blog_posts = requested_post, form=comment_form, year = current_year, logged_in = current_user.is_authenticated, avatar=avatar)


# @app.route("/form-entry", methods = ["POST"])
# def receive_data():
#     return "Message submitted Successfully."



@app.route("/new_post", methods = ['GET', 'POST'])
@role_required('admin')
def make_post():
    new_post = NewPost()
    current_year = datetime.now().year
    heading = "New Post"


    if new_post.validate_on_submit():
        if new_post.submit_draft.data:
            post_status = "Draft"
        elif new_post.submit_publish.data:
            post_status = "Published"
        new_blog = BlogPost(
            title = new_post.post_title.data,
            subtitle = new_post.subtitle.data,
            date = datetime.now().date(),
            body = new_post.post_content.data,
            author = current_user,
            img_url = new_post.bg_img_url.data,
            subject = new_post.subject.data,
            status=post_status
        )

        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('home'))


    return render_template('make-post.html', year = current_year, form = new_post, heading = heading, logged_in = current_user.is_authenticated)



@app.route("/edit_post/<int:post_id>", methods = ['GET', 'POST'])
@role_required('admin')
def edit_post(post_id):
    heading = "Edit Post"
    current_year = datetime.now().year
    post_to_edit = db.get_or_404(BlogPost, post_id)
    edit_post_form = NewPost(
        post_title = post_to_edit.title,
        subtitle = post_to_edit.subtitle,
        author_name = post_to_edit.author,
        bg_img_url = post_to_edit.img_url,
        post_content = post_to_edit.body
    )

    if edit_post_form.submit_draft.data:
            post_status = "Draft"
    elif edit_post_form.submit_publish.data:
        post_status = "Published"

    if edit_post_form.validate_on_submit():
        post_to_edit.title = edit_post_form.post_title.data
        post_to_edit.subtitle = edit_post_form.subtitle.data
        post_to_edit.author = current_user
        post_to_edit.img_url = edit_post_form.bg_img_url.data
        post_to_edit.body = edit_post_form.post_content.data
        post_to_edit.status = post_status

        db.session.commit()

        return redirect(url_for("post", num = post_id))
    
    return render_template ("make-post.html", year = current_year, form = edit_post_form, heading = heading, logged_in = current_user.is_authenticated)



@app.route("/delete_post/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()

    return redirect(url_for('home'))



@app.route('/manage_users', methods=['GET', 'POST'])
@role_required('admin')
def manage_users():
    users = User.query.all()
    current_year = datetime.now().year
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        new_role = request.form.get(f'role_{user_id}')
        user = User.query.get(user_id)
        if user:
            user.role = new_role
            db.session.commit()
        return redirect(url_for('manage_users'))
    return render_template('manage_user.html', users=users, year = current_year, logged_in = current_user.is_authenticated)



# def send_message(name, user_email, phone, message):
#     msg_content = f"Name: {name}\nemail: {user_email}\nPhone: {phone}\nMessage: {message}"
#     connection = smtplib.SMTP("smtp.gmail.com")
#     connection.starttls()
#     connection.login(user= my_email, password= password)
#     connection.sendmail(from_addr= my_email, 
#                             to_addrs= "debojyotichattoraj1996@gmail.com", 
#                             msg= f"Subject: New User Information!\n\n {msg_content}")
#     connection.close()



def send_message(name, user_email, phone, message):
    msg_content = f"Name: {name}\nemail: {user_email}\nPhone: {phone}\nMessage: {message}"
    # client = Client(account_sid, auth_token)
    message = client.messages.create(
        body= msg_content,
        from_=f'whatsapp:{os.environ.get("TWILIO_API_NUM")}',
        to=f'whatsapp:{os.environ.get("TWILIO_MY_NUM")}',
    )




if __name__ == "__main__":
    app.run(debug=True, host= '0.0.0.0', port= 8000)
