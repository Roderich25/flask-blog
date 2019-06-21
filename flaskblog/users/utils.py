import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flaskblog import mail
from flask_mail import Message
from flask_login import current_user


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = f"{random_hex}{f_ext}"
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    if current_user.image_file != 'default.jpg':
        os.remove(os.path.join(current_app.root_path, 'static/profile_pics', current_user.image_file))
    return picture_fn


def send_user_email(user_email, token, mail_subject, mail_message, goto):
    msg = Message(mail_subject, sender=os.getenv('FlaskUserMail'), recipients=[user_email])
    msg.body = f"""
                FlaskBlog

                {mail_message}
                {url_for(goto, token=token, _external=True)}

                If you did not make this request then simply ignore this e-mail.
                """
    mail.send(msg)
