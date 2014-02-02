from flask import Flask
import tcdiracweb.default_settings
app = Flask(__name__)
app.config.from_object('tcdiracweb.default_settings.DevelopmentConfig')
app.secret_key = 'I am coming for you.'
import tcdiracweb.views
