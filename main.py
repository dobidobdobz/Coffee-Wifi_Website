from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from wtforms import StringField, SubmitField, BooleanField, PasswordField, EmailField
from wtforms.validators import DataRequired, URL, Length
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from werkzeug.security import generate_password_hash, check_password_hash
import os


SECRET_KEY = os.environ.get("SECRET_KEY")

# starting flask server
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
# This line integrates Bootstrap 5 into the Flask application using a Flask extension
Bootstrap5(app)
# This line integrates the CKEditor rich text editor into the Flask application
ckeditor = CKEditor(app)

# flask login function initializing within app
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# create a new database if does not exist
class Base(DeclarativeBase):
    pass


# configures flask server app to use or connect to sqlite data base
# creates a sql ORM to interact with database
# initialize database inside the flask app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# create home server and render html
@app.route("/", methods=["GET", "POST"])
def home():
    # get data from database(query the database)
    cafes_data = cafe.query.all()
    return render_template("index.html", cafes=cafes_data, current_user=current_user)


# create form for user to add new cafe
class AddNewCafe(FlaskForm):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name = StringField('Cafe name', validators=[DataRequired()])
    map_url = StringField("Cafe Location on Google Maps (URL)", validators=[DataRequired(), URL()])
    img_url = StringField("Image of coffee shop (URL)", validators=[DataRequired(), URL()])
    location = StringField("Neighborhood / District eg. Peckham", validators=[DataRequired()])
    has_sockets = BooleanField("Are there any power sockets?")
    has_toilet = BooleanField("Is there WC on the premises?")
    has_wifi = BooleanField("Is there any wifi on the premises?")
    can_take_calls = BooleanField("Can you comfortably take calls there?")
    seats = StringField("How many seats are on the premises eg. 100+?", validators=[DataRequired()])
    coffee_price = StringField("How much does a coffee cost?", validators=[DataRequired()])
    submit = SubmitField('Add to database')


# Create a RegisterForm to register new users to sign up
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email Address", validators=[DataRequired()])
    password = PasswordField("password", validators=[DataRequired(), Length(min=8)])
    submit = SubmitField("Register!")


# create login form
class LoginForm(FlaskForm):
    email = StringField("Email Address", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("login")


# creates new user's table in database to store signed-up user in database
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)


# CONFIGURE DATABASE TABLE for data related to adding a new cafe to the database
class cafe(db.Model):
    __tablename__ = "cafe"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


# page allows you to fill out form & add new cafe data to the database and display it to the website
# requires the user be logged in to be able to access this page
@app.route("/add_coffee_shop", methods=["GET", "POST"])
@login_required
def add_coffee_shop():
    form = AddNewCafe()

    # if form is submitted add to databases
    if form.validate_on_submit():

        # add database here
        new_cafe = cafe(
            name=request.form["name"],
            map_url=request.form["map_url"],
            img_url=request.form["img_url"],
            location=request.form["location"],
            has_sockets=True if request.form.get("has_sockets") == "y" else False,
            has_toilet=True if request.form.get('has_toilet') == "y" else False,
            has_wifi=True if request.form.get('has_wifi') == "y" else False,
            can_take_calls=True if request.form.get('can_take_calls') == "y" else False,
            seats=request.form["seats"],
            coffee_price=request.form["coffee_price"]
        )

        # creates session adds data & commits the data to table
        db.session.add(new_cafe)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("add_coffee_shop.html", form=form)


# user registration page
@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            #  Use Werkzeug to hash the user's password when creating a new user.
            password=generate_password_hash(password=form.password.data, method="pbkdf2:sha256", salt_length=8),
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect(url_for("home"))
    return render_template("register.html", form=form)


# Retrieve a user from the database based on their email.
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # searches database for a match
        matching_email_credentials = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        # if not a match display appropriate invalid or incorrect details msg
        if not matching_email_credentials:
            flash("email is invalid or does not exist please try again or register")
            return redirect("login")
        elif not check_password_hash(password=form.password.data, pwhash=matching_email_credentials.password):
            flash("password is incorrect, please try again!")
            return redirect("login")
        else:
            login_user(matching_email_credentials)
            if current_user.id == 1:
                return redirect(url_for("home"))
            else:
                return redirect(url_for("home"))
    return render_template("login.html", form=form)


# server functionality to provide logout to user.
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# runs flask server in debug mode applying changes as they are made when you refresh.
if __name__ == '__main__':
    app.run(debug=True)
