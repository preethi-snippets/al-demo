from flask import Flask

application = Flask(__name__, static_folder='static', static_url_path='')
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///csvTest.sqlite'

from application import views, models
