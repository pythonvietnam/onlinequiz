from flask import Flask
from flask.ext.pymongo import PyMongo
from flaskext.uploads import UploadSet, IMAGES, configure_uploads
from datetime import timedelta

app = Flask(__name__)

app.config.from_object('config')

app.permanent_session_lifetime = timedelta(minutes=30)

mongo = PyMongo(app, config_prefix='MONGO')

images = UploadSet('images', IMAGES)
configure_uploads(app, images)

from app import views
