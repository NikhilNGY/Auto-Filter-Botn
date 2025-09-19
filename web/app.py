from flask import Flask, jsonify

# Minimal Flask app
web_app = Flask(__name__)

@web_app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "message": "Bot is running!"})

# Optional: health check endpoint for Koyeb
@web_app.route("/healthz", methods=["GET"])
def health_check():
    return "OK", 200
