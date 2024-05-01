# flaskr/core.py



#limiter = Limiter(key_func=get_remote_address,default_limits=["5 per minute"])

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
#from redis import Redis

app = Flask(__name__)
limiter = Limiter(
    key_func=get_remote_address
    #storage_uri='redis://localhost:6379/0'  # Adjust this URI based on your Redis configuration
)