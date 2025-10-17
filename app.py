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
CORS(app)

# --- API Endpoint for News ---
@app.route("/api/news", methods=["GET"])
def get_news():
    try:
        doc_ref = db.collection("news").document("latest_headlines")
        doc = doc_ref.get()
        return jsonify(doc.to_dict()) if doc.exists else (jsonify({"error": "No headlines found"}), 404)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)