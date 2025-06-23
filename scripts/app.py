from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from werkzeug.utils import secure_filename # For securing filenames

# Define the folder to save uploaded files
UPLOAD_FOLDER = 'mangodata'
# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx', 'txt'}

# Add the directory containing your AI agent script to the Python path
sys.path.append(os.path.dirname(__file__))

try:
    from ai_agent import AIAgent
    print("Successfully imported AIAgent from ai_agent.py")
except ImportError as e:
    print(f"ERROR: Could not import AIAgent. Check ai_agent.py file name and class name. Error: {e}", file=sys.stderr)
    sys.exit(1) # Exit if agent can't be imported

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
print(f"Ensured upload folder '{UPLOAD_FOLDER}' exists.")

try:
    ai_agent = AIAgent()
    print("AI Agent initialized successfully.")
except Exception as e:
    print(f"ERROR: Could not initialize AIAgent. Error: {e}", file=sys.stderr)
    sys.exit(1) # Exit if agent can't be initialized

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    print("Received request to /upload endpoint.")
    if 'file' not in request.files:
        print("No file part in the request.")
        return jsonify({"message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        print("No selected file.")
        return jsonify({"message": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            file.save(file_path)
            print(f"File '{filename}' saved to '{file_path}'")
            return jsonify({"message": "File uploaded successfully", "filename": filename}), 200
        except Exception as e:
            print(f"Error saving file: {e}", file=sys.stderr)
            return jsonify({"message": f"Failed to save file: {e}"}), 500
    else:
        print(f"File type not allowed: {file.filename}")
        return jsonify({"message": "File type not allowed"}), 400

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message')
    # Get the last uploaded filename from the frontend
    # This will now be passed as 'file_to_use' to the AI agent
    file_to_use = data.get('last_uploaded_file')

    if not user_message:
        return jsonify({"response": "No message provided."}), 400

    print(f"Received message from frontend: {user_message}")
    if file_to_use:
        print(f"Explicit file to use: {file_to_use}")

    try:
        # Pass the user message and the explicit file_to_use to the AI agent
        bot_response = ai_agent.process_message(user_message, file_to_use=file_to_use)
        print(f"AI Agent response: {bot_response}")
        return jsonify({"response": bot_response})
    except Exception as e:
        import traceback
        print(f"ERROR: Exception during AI agent processing: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({"response": "An internal server error occurred while processing your request."}), 500

@app.route('/')
def home():
    return "Flask backend is running!"

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True, host='127.0.0.1', port=5000)
    print("Flask app stopped.")