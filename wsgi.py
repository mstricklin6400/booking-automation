"""
WSGI entry point for gunicorn deployment.
This file is the standard entry point for production deployments using gunicorn.
"""

from app import app

# This is what gunicorn looks for
application = app

if __name__ == "__main__":
    application.run()