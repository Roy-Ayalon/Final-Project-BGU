"""
Flask Server for AI Meme Classification and Generation
This server should run on your CUDA-enabled machine
"""

import os
import json
import time
from typing import Dict, Any, Optional, Tuple
from flask import Flask, request, jsonify, send_file
from PIL import Image
import torch
from werkzeug.utils import secure_filename
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
GENERATED_FOLDER = 'generated'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


class MemeProcessor:
    """
    Main class for processing memes - classification and generation
    This class should be initialized with your AI models
    """
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # TODO: Initialize your models here
        # self.ocr_model = None
        # self.classification_model = None  
        # self.generation_model = None
        self._load_models()
    
    def _load_models(self):
        """Load all AI models"""
        logger.info("Loading AI models...")
        
        # TODO: Implement model loading
        # Example structure based on your notebooks:
        """
        # Load OCR model
        from transformers import AutoModel, AutoTokenizer
        self.tokenizer_ocr = AutoTokenizer.from_pretrained('ucaslcl/GOT-OCR2_0', trust_remote_code=True)
        self.model_ocr = AutoModel.from_pretrained('ucaslcl/GOT-OCR2_0', trust_remote_code=True, 
                                                  low_cpu_mem_usage=True, device_map='cuda')
        
        # Load classification model
        from transformers import pipeline
        self.text_classification = pipeline("text-classification", model="ibm-granite/granite-guardian-hap-125m")
        
        # Load generation model
        from diffusers import StableDiffusion3Pipeline
        self.generation_pipeline = StableDiffusion3Pipeline.from_pretrained(...)
        """
        
        logger.info("Models loaded successfully")
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from meme using OCR"""
        try:
            # TODO: Implement OCR extraction
            # This should use your GOT-OCR2_0 model
            extracted_text = "Sample extracted text"  # Placeholder
            logger.info(f"Extracted text: {extracted_text}")
            return extracted_text
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def classify_meme(self, image_path: str, extracted_text: str) -> Dict[str, Any]:
        """Classify if meme is offensive"""
        try:
            # TODO: Implement classification logic
            # This should use your granite-guardian model
            
            # Placeholder logic
            is_offensive = len(extracted_text) > 10  # Dummy logic
            
            result = {
                "is_offensive": is_offensive,
                "confidence": 0.85,
                "explanation": "This meme contains potentially offensive content." if is_offensive else "This meme appears to be safe."
            }
            
            logger.info(f"Classification result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in classification: {e}")
            return {"is_offensive": False, "confidence": 0.0, "explanation": "Classification failed"}
    
    def generate_alternative_meme(self, original_image_path: str, extracted_text: str, 
                                 temperature: float = 0.7) -> Optional[str]:
        """Generate an alternative, non-offensive meme"""
        try:
            # TODO: Implement meme generation
            # This should use your Stable Diffusion pipeline
            
            generated_filename = f"generated_{int(time.time())}.png"
            generated_path = os.path.join(app.config['GENERATED_FOLDER'], generated_filename)
            
            # Placeholder: Copy original image for now
            from shutil import copy2
            copy2(original_image_path, generated_path)
            
            logger.info(f"Generated alternative meme: {generated_path}")
            return generated_filename
            
        except Exception as e:
            logger.error(f"Error generating meme: {e}")
            return None


def allowed_file(filename: str) -> bool:
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Initialize the processor
processor = MemeProcessor()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "device": str(processor.device),
        "timestamp": time.time()
    })


@app.route('/upload', methods=['POST'])
def upload_and_process():
    """Main endpoint for meme processing"""
    try:
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        logger.info(f"Received file: {filename}")
        
        # Get temperature parameter if provided
        temperature = float(request.form.get('temperature', 0.7))
        
        # Process the image
        result = process_meme(file_path, temperature)
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        return jsonify({"error": "Internal server error"}), 500


def process_meme(image_path: str, temperature: float = 0.7) -> Dict[str, Any]:
    """Process a meme through the full pipeline"""
    
    # Step 1: Extract text
    extracted_text = processor.extract_text_from_image(image_path)
    
    # Step 2: Classify
    classification = processor.classify_meme(image_path, extracted_text)
    
    if not classification["is_offensive"]:
        # Meme is safe
        return {
            "status": "Non-Offensive",
            "message": "This meme is safe to use!",
            "explanation": classification["explanation"],
            "confidence": classification["confidence"]
        }
    else:
        # Meme is offensive, generate alternative
        alternative_filename = processor.generate_alternative_meme(
            image_path, extracted_text, temperature
        )
        
        if alternative_filename:
            return {
                "status": "Offensive",
                "explanation": classification["explanation"],
                "meme": f"/generated/{alternative_filename}",
                "question": "Do you like this alternative version?",
                "confidence": classification["confidence"]
            }
        else:
            return {
                "status": "Offensive",
                "explanation": classification["explanation"],
                "message": "Unable to generate alternative",
                "confidence": classification["confidence"]
            }


@app.route('/generated/<filename>')
def serve_generated_file(filename):
    """Serve generated meme files"""
    try:
        file_path = os.path.join(app.config['GENERATED_FOLDER'], secure_filename(filename))
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        logger.error(f"Error serving file: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # Run the server
    app.run(host='0.0.0.0', port=5002, debug=False)
