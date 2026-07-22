from flask import Flask

def create_app():
    # Initialize the core Flask application
    app = Flask(__name__)
    
    # Secret key for sessions/forms
    app.config['SECRET_KEY'] = 'dev-key-perfume-pro'

    # Register Blueprints
    from app.routes.inventory_routes import inventory_bp
    app.register_blueprint(inventory_bp)

    return app