from app import create_app
from gunicorn.app.base import BaseApplication

# Create the Flask application
app = create_app()

class FlaskGunicornApplication(BaseApplication):
    def load_config(self):
        self.cfg.set('bind', '0.0.0.0:8080')

    def load(self):
        return app

if __name__ == '__main__':
    FlaskGunicornApplication().run()
