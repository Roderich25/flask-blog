from flaskblog import db, create_app
import os

if os.path.exists(
        os.path.join(os.getcwd(), 'flaskblog', os.getenv('SQLALCHEMY_DATABASE_URI').split('///')[1])) is False:
    db.create_all(app=create_app())

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=8080)
