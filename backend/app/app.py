import os
import sys

print("RUNNING APP FROM:", __file__)

from flask import Flask
from flask_cors import CORS

# Add backend folder to Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from models.model_loader import model
from routes.predict import predict_bp
from database.database import create_database


app = Flask(__name__)

# Enable CORS for frontend connection
CORS(app)


# Create database
create_database()


# Register API routes
app.register_blueprint(predict_bp)


@app.route("/")
def home():
    return "AI Skin Disease Detection Backend is Running!"


@app.route("/test")
def test():
    print("TEST ROUTE CALLED")
    return "Backend Working"


if __name__ == "__main__":

    print("=" * 50)
    print("AI Skin Disease Detection Backend Started")
    print("Database Connected Successfully")
    print("Model Loaded Successfully")
    print("=" * 50)

    # Render provides PORT automatically
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
