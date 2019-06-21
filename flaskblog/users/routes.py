from flask import render_template, url_for, flash, redirect, request, session, Blueprint
from flaskblog import db, bcrypt
from flaskblog.users.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, PasswordForm
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flaskblog.users.utils import save_picture, send_user_email

users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        token = User.get_token({'username': form.username.data, 'email': form.email.data})
        send_user_email(form.email.data, token, 'Register FlaskBlog account',
                        'To create your account please visit the following link:', 'users.verify_account')
        flash("Please check your email to create your account.", 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash("Login Unsuccesfull. Check email and password!", 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated", 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename=f"profile_pics/{current_user.image_file}")
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user) \
        .order_by(Post.date_posted.desc()) \
        .paginate(per_page=5, page=page)
    return render_template("user_posts.html", posts=posts, user=user)


@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        token = User.get_token({'user_id': user.id})
        user.token = token
        db.session.commit()
        send_user_email(user.email, token, 'Password reset request',
                        'To reset your password visit the following link:', 'users.reset_token')
        flash('Check your e-mail to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title="Reset Password", form=form)


@users.route("/reset_password/<string:token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    if User.verify_token(token) is None:
        flash("Invalid or Expired link", 'warning')
        return redirect(url_for('users.login'))
    user_id = User.verify_token(token)['user_id']
    user = User.query.get(user_id)
    if user is None or token != user.token:
        flash("Invalid or Expired link", 'warning')
        return redirect(url_for('users.login'))
    form = PasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        user.token = ''
        db.session.commit()
        flash("Password updated", 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title="Reset Password", legend="Reset Password", form=form)


@users.route("/verify_account/<string:token>", methods=['GET', 'POST'])
def verify_account(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    if User.verify_token(token) is None or session['rgtkn'] == token:
        flash("Invalid or Expired link", 'warning')
        return redirect(url_for('users.login'))
    username, email = [User.verify_token(token)[key] for key in ['username', 'email']]
    form = PasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        session['rgtkn'] = token
        db.session.add(user)
        db.session.commit()
        flash("Account created", 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title="Create account", legend="Choose Password", form=form)


@users.route("/cookies")
def cookies():
    return f"{session['rgtkn']}"
