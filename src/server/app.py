"""
Flask Server for AI Meme Classification and Generation
This server should run on your CUDA-enabled machine
Integrates the actual AI models from main.py
"""

import os
import sys
import time
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
import re

# Import your actual AI functions
try:
    from .main import classification, meme_manipulation, generate_image
except ImportError:
    # Fallback for when running directly
    from main import classification, meme_manipulation, generate_image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploaded_images'
GENERATED_FOLDER = 'generated_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

logger.info("🚀 AI Processing Server initialized with actual models")


def allowed_file(filename: str) -> bool:
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "AI Processing Server is running",
        "timestamp": time.time()
    })


@app.route('/upload', methods=['POST'])
def upload_and_process():
    """Main endpoint for meme processing - integrates your actual AI pipeline"""
    try:
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400
        
        # Save uploaded file with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logger.info(f"📥 Received file: {filename}")
        
        # Get temperature parameter for generation
        temperature = float(request.form.get('temperature', 0.7))
        
        # Step 1: Classify the meme using your actual classification function
        predicted = classification(filepath)
        
        # Step 2: Handle response based on classification
        if predicted == 0:  # Non-offensive
            logger.info("✅ Meme classified as non-offensive")
            return jsonify({
                'status': 'Non-Offensive',
                'message': 'The meme is classified as non-offensive. You can use it freely.',
                'meme': f'/download/{filename}',
                'confidence': 0.95
            })
        
        else:  # Offensive - generate alternative
            logger.info("🚫 Meme classified as offensive, generating alternative...")
            
            # Step 3: Get explanation using your meme_manipulation function
            explanation_messages = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are a direct assistant."}]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "path": filepath},
                        {"type": "text", "text": "explain shortly why this meme is offensive? start with 'This meme is offensive'"}
                    ]
                }
            ]
            explanation = meme_manipulation(explanation_messages, temperature=temperature)
            
            # Step 4: Generate alternative meme description and text
            generation_messages = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are a direct assistant."}]
                },
                {
                    "role": "user", 
                    "content": [
                        {"type": "image", "path": filepath},
                        {"type": "text", "text": "change the meme to be not offensive, give me image description and upper text and lower text only."}
                    ]
                }
            ]
            meme_convert = meme_manipulation(generation_messages, temperature=temperature)
            meme_convert = meme_convert.replace("*", "")
            
            # Step 5: Parse AI response to extract components
            lower_match = re.search(r"Lower Text:\s*(.*)", meme_convert, re.DOTALL)
            lower_text = lower_match.group(1).strip() if lower_match else ""
            lower_text = lower_text.replace('"', '').replace("'", "")
            if lower_match:
                meme_convert = meme_convert[:lower_match.start()]
            
            upper_match = re.search(r"Upper Text:\s*(.*)", meme_convert, re.DOTALL)  
            upper_text = upper_match.group(1).strip() if upper_match else ""
            upper_text = upper_text.replace('"', '').replace("'", "")
            if upper_match:
                meme_convert = meme_convert[:upper_match.start()]
                
            desc_match = re.search(r"Image Description:\s*(.*)", meme_convert, re.DOTALL)
            image_description = desc_match.group(1).strip() if desc_match else ""
            
            # Clean up extracted text
            upper_text = upper_text.strip('"').strip("'")
            lower_text = lower_text.strip('"').strip("'") 
            image_description = image_description.strip('"').strip("'")
            
            # Step 6: Generate alternative meme using your generate_image function
            final_meme = generate_image(image_description, upper_text, lower_text)
            alternative_filename = f"alternative_{filename}"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], alternative_filename)
            final_meme.save(output_path)
            
            logger.info(f"✨ Generated alternative meme: {alternative_filename}")
            
            # Clean up original file
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'status': 'Offensive',
                'explanation': explanation,
                'message': 'This meme was offensive. A new meme has been generated.',
                'meme': f'/download/{alternative_filename}',
                'question': 'Do you like this alternative version?',
                'confidence': 0.87
            })
            
    except Exception as e:
        logger.error(f"❌ Error processing upload: {e}")
        # Clean up file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500


@app.route('/download/<filename>')
@app.route('/generated/<filename>')  # Support both endpoints for compatibility
def serve_file(filename):
    """Serve uploaded or generated files"""
    try:
        safe_filename = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        if os.path.exists(file_path):
            logger.info(f"📤 Serving file: {safe_filename}")
            return send_file(file_path, mimetype='image/png', as_attachment=False)
        else:
            logger.warning(f"❌ File not found: {safe_filename}")
            return jsonify({"error": "File not found"}), 404
            
    except Exception as e:
        logger.error(f"❌ Error serving file {filename}: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    logger.info("🚀 Starting AI Processing Server...")
    logger.info("🔧 Make sure you have:")
    logger.info("  - CUDA-enabled GPU")
    logger.info("  - All AI models downloaded")
    logger.info("  - impact.ttf font file in the same directory")
    app.run(host='0.0.0.0', port=5002, debug=False)
