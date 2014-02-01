from flask import Flask
import default_settings
app = Flask(__name__)
app.config.from_object('default_settings.DevelopmentConfig')
app.secret_key = 'I am coming for you.'
import tcdiracweb.views
