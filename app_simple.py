#!/usr/bin/env python3

# Minimal Flask app for deployment testing
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from Replit Deployment!"

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)