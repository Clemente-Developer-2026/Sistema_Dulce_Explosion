from flask import Blueprint
usuarios_bp = Blueprint("auth", __name__,url_prefix="/auth")
from app.auth import routes