from flask import Flask

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///csvTest.sqlite'

from app import views, models
