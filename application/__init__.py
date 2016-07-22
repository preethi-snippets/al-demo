from flask import Flask
import os
import config

application = Flask(__name__, static_folder='static', static_url_path='')
application.config['SQLALCHEMY_DATABASE_URI'] = config.database_url
application.config['SECRET_KEY'] = config.secret_key

from application import views, models

print "Calling kvsession store..................."
models.create_kvsession_store()