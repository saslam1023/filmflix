from app import create_app
from gunicorn.app.base import BaseApplication

# Create the Flask application
app = create_app()

class FlaskGunicornApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self.application

if __name__ == '__main__':
    options = {
        'bind': '0.0.0.0:8080',  # Adjust port as needed
        'workers': 4,             # Adjust based on server capacity
        'loglevel': 'info',       # Adjust log level as needed
        'accesslog': '-'          # Log to stdout
    }
    FlaskGunicornApplication(app, options).run()
