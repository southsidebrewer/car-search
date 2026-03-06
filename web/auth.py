from functools import wraps
from flask import request, redirect, session, url_for
from werkzeug.security import check_password_hash
import os

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def validate_passcode(passcode):
    return check_password_hash(os.getenv("PASSCODE_HASH"), passcode)
