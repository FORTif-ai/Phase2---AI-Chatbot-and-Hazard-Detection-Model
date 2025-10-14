# Imports
from flask import Flask
from Board import pages       # Import the blueprint from pages.py


def create_app():
    """
    Application factory function
    Creates and configures a Flask app instance,
    then register all blueprints (routes)
    """
    app = Flask(__name__)
    
    # Register the 'pages' blueprint
    app.register_blueprint(pages.bp)
    return app