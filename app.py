# app.py
from flask import Flask, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore

# --- Firebase Initialization ---
try:
    cred = credentials.Certificate("credentials.json")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Error connecting to Firebase: {e}")
    exit()

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app) # Allows your frontend to request data from this API

# --- API Endpoint ---
@app.route("/api/news", methods=["GET"])
def get_news():
    """Fetches the latest headlines from the Firestore database."""
    try:
        doc_ref = db.collection("news").document("latest_headlines")
        doc = doc_ref.get()

        if doc.exists:
            return jsonify(doc.to_dict())
        else:
            return jsonify({"error": "No headlines found in database"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)