from flask import Flask, request, jsonify, send_file
import os
from datetime import datetime
from main import classification, meme_manipulation, generate_image
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploaded_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part in the request'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Step 1–2: Save the image
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    temp = float(request.form.get('temperature', 0.7))

    # Step 3: Classify
    predicted = classification(filepath)

    # Step 4: Respond to user
    if predicted == 0:
        return jsonify({
            'status': 'Non-Offensive',
            'message': 'The meme is classified as non-offensive. You can use it freely.',
            'meme': f'/download/{filename}'
        })

    # Step 5: Explain and generate alternative
    message1 = [
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
    explanation = meme_manipulation(message1, temperature=temp)

    message2 = [
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
    meme_convert = meme_manipulation(message2, temperature=temp)
    meme_convert = meme_convert.replace("*", "")

    # Parse AI response
    lower_match = re.search(r"Lower Text:\s*(.*)", meme_convert, re.DOTALL)
    lower_text = lower_match.group(1).strip() if lower_match else ""
    # remove "" signs from lower_text
    lower_text = lower_text.replace('"', '').replace("'", "")
    if lower_match:
        meme_convert = meme_convert[:lower_match.start()]

    upper_match = re.search(r"Upper Text:\s*(.*)", meme_convert, re.DOTALL)
    upper_text = upper_match.group(1).strip() if upper_match else ""
    # remove "" signs from upper_text
    upper_text = upper_text.replace('"', '').replace("'", "")
    if upper_match:
        meme_convert = meme_convert[:upper_match.start()]

    desc_match = re.search(r"Image Description:\s*(.*)", meme_convert, re.DOTALL)
    image_description = desc_match.group(1).strip() if desc_match else ""

    # Strip any surrounding single or double quotes from the extracted text
    upper_text = upper_text.strip('"').strip("'")
    lower_text = lower_text.strip('"').strip("'")
    image_description = image_description.strip('"').strip("'")

    final_meme = generate_image(image_description, upper_text, lower_text)
    output_path = os.path.join(UPLOAD_FOLDER, "alternative_" + filename)
    final_meme.save(output_path)

    return jsonify({
        'status': 'Offensive',
        'explanation': explanation,
        'message': 'This meme was offensive. A new meme is generated.',
        'meme': f'/download/{os.path.basename(output_path)}',
        'question': 'Do you like this new version?'
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename),
                     mimetype='image/png',
                     as_attachment=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)