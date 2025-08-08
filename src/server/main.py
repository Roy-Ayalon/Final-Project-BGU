import os
import cv2
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer, pipeline, Gemma3ForConditionalGeneration
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from transformers.generation.utils import DynamicCache
DynamicCache.get_max_length = lambda self: 0
from transformers import CLIPProcessor, CLIPModel, AutoModelForSequenceClassification
from diffusers import StableDiffusion3Pipeline
from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap
import re
import matplotlib.pyplot as plt
#from accelerate import init_empty_weights, dispatch_model, infer_auto_device_map
#Hugging Face login
from huggingface_hub import login
token = "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"
login(token=token)

#####################################################Classification Models uploading###########################################
# ***Load the OCR model***
tokenizer_OCR = AutoTokenizer.from_pretrained('ucaslcl/GOT-OCR2_0', trust_remote_code=True)
model_OCR = AutoModel.from_pretrained('ucaslcl/GOT-OCR2_0', trust_remote_code=True, low_cpu_mem_usage=True, device_map="cuda:0", use_safetensors=True, pad_token_id=tokenizer_OCR.eos_token_id)
model_OCR = model_OCR.eval().cuda()
model_OCR.config.use_cache = False


# ***Load the text generation model***
text_classification = pipeline("text-classification", model="ibm-granite/granite-guardian-hap-125m", device_map="cuda:0")

# ***Load the image classification model***
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to("cuda:0").eval()
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


# ***Load the meme classification model***
model_name = "aliencaocao/qwen2-vl-7b-rslora-offensive-meme-singapore"
base_processor_name = "Qwen/Qwen2-VL-7B-Instruct"

# ***Load the fine-tuned Qwen2-VL-7B model (vision-language classifier)***
qwen_model = Qwen2VLForConditionalGeneration.from_pretrained(
    model_name, device_map="cuda:6", torch_dtype=torch.float16
)
# Load the corresponding processor (handles image preprocessing and tokenization)
qwen_processor = AutoProcessor.from_pretrained(base_processor_name)

#############################################################################################################################
#########################################Manipulation Model uploading########################################################
gemma_pipe = pipeline(
    "image-text-to-text",
    model="google/gemma-3-4b-it",
    device="cuda:8",
    torch_dtype=torch.bfloat16
)
##############################################################################################################################
#########################################Generation Model uploading###########################################################
model_generation = "stabilityai/stable-diffusion-3.5-medium"

pipeline_generation = StableDiffusion3Pipeline.from_pretrained(model_generation, torch_dtype=torch.bfloat16)
pipeline_generation = pipeline_generation.to("cuda:7")

#########################################################################################################
##############################################Classification Functions###################################
# 1) Define your labels once, with the exact same spelling & order everywhere:
image_labels    = ["Non-Offensive", "Offensive"]
candidate_texts = image_labels.copy()

# 2) Your CLIP classifier now only refers to that one list:
def image_classifier_clip(clean_img):
    """
    Zero‑shot classifies an image as "Offensive" or "Non‑Offensive" using CLIP.
    """
    image = Image.open(clean_img).convert("RGB")

    # use the global candidate_texts (same as image_labels!)
    inputs = clip_processor(
        text=candidate_texts,
        images=image,
        return_tensors="pt",
        padding=True
    )
    inputs = {k: v.to(clip_model.device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = clip_model(**inputs).logits_per_image  # (1,2)
    probs = logits.softmax(dim=1)[0]

    best_idx = probs.argmax().item()
    label    = candidate_texts[best_idx]

    # print in the same order as image_labels
    print(f"Scores → {image_labels[0]}: {probs[0]:.3f}, {image_labels[1]}: {probs[1]:.3f}")
    return label

def meme_classifier(meme_path):
    # Prepare a single-turn "conversation" with the image and a prompt question
    conversation = [{
        "role": "user",
        "content": [
            {"type": "image", "path": meme_path},
            {"type": "text", "text": "Is this meme offensive or non-offensive? "
                                     "Respond with 'Offensive' or 'Non-offensive'."}
        ]
    }]
    # Process the conversation into model inputs (image pixels + tokenized text)
    inputs = qwen_processor.apply_chat_template(
        conversation, add_generation_prompt=True, tokenize=True, return_tensors="pt", return_dict=True
    ).to(qwen_model.device)
    # Generate the model's response (as text) with a limited number of tokens
    output_ids = qwen_model.generate(**inputs, max_new_tokens=16)
    # The output sequence includes the prompt; slice to get generated answer tokens only
    generated_ids = output_ids[0, inputs["input_ids"].shape[1]:]
    answer = qwen_processor.decode(generated_ids, skip_special_tokens=True).strip()

    # Interpret the model's answer and map to "Offensive" or "Non-offensive"
    ans_lower = answer.lower()
    if "offensive" in ans_lower:
        # If the answer contains "not offensive" or "non-offensive", it's non-offensive
        if "not offensive" in ans_lower or "non-offensive" in ans_lower:
            return 0 #"Non-Offensive"
        else:
            return 1 #"Offensive"
    # Default: if "offensive" wasn't mentioned, assume non-offensive
    return 0 #"Non-Offensive"

def get_text_from_meme_and_save_mask(meme_path, mask_path):
    """
    Extracts text from a meme and creates a white-text binary mask for inpainting.

    Returns:
        extracted_text (str): OCR extracted text
        mask_img_path (str): Full path to saved binary mask image
    """
    threshold = [255, 255, 255]

    # Open image and convert to RGB
    image = Image.open(meme_path).convert('RGB')
    image_data = np.array(image)

    # Create mask: white text becomes white, background becomes black
    mask = np.all(image_data < threshold, axis=-1)
    image_data[mask] = [0, 0, 0]
    image_data[~mask] = [255, 255, 255]

    # Run OCR on original image
    model_OCR.config.use_cache = False
    res = model_OCR.chat(tokenizer_OCR, meme_path, ocr_type='ocr')
    result = res.replace('\n', " ")

    # Save the mask image
    mask_img = Image.fromarray(image_data)
    mask_img.save(mask_path)
    return result


def remove_text_from_image(meme_path, mask_img_path):
    """
    Removes white text from meme using inpainting, based on the binary mask.

    Returns:
        cleaned_image (np.ndarray): Image with text removed
    """
    binary_image = cv2.imread(mask_img_path)
    source_image = cv2.imread(meme_path)

    # Convert mask to grayscale
    gray_image = cv2.cvtColor(binary_image, cv2.COLOR_BGR2GRAY)
    mask = gray_image == 255

    # Inpaint image
    inpainted_image = cv2.inpaint(source_image, mask.astype(np.uint8), 3, cv2.INPAINT_TELEA)

    return inpainted_image

def classification(meme):
    """
    Classifies a meme as "Offensive" or "Non-Offensive" using two models:
    1. CLIP model for image classification
    2. Qwen2-VL model for meme classification
    """

    # Labels
    labels = ["Non-Offensive", "Offensive"]
    # Get the text and mask image path
    extracted_text = get_text_from_meme_and_save_mask(meme, "mask.png")

    # Remove text from image using inpainting
    cleaned_image = remove_text_from_image(meme, "mask.png")
    # Save the cleaned image
    cv2.imwrite("clean.png", cleaned_image)
     # Run text classification
    text_model_result = text_classification(extracted_text)

    # Interpret model result
    raw_label = text_model_result[0]['label']
    if raw_label.lower() in ['hate', 'offensive', 'toxic', 'label_1']:
        predicted_text_label = 1
    else:
        predicted_text_label = 0

    # Run CLIP model
    image_model_result = image_classifier_clip("clean.png")
    predicted_image_label = labels.index(image_model_result)
    predicted_image_label = 0 if predicted_image_label < 1 else 1
    os.remove("clean.png")
    os.remove("mask.png")
    # Run Qwen2-VL model
    qwen2_model_result = meme_classifier(meme)
    predicted_meme_label = qwen2_model_result

    # Combine results
    predicted_combined_label = predicted_text_label or predicted_image_label or predicted_meme_label
    print(f"Text Model: {predicted_text_label}, Image Model: {predicted_image_label}, Qwen2-VL Model: {predicted_meme_label}, Combined: {predicted_combined_label}")
    return predicted_combined_label
###########################################################################################
######################################Meme manipulation Function###################################
def meme_manipulation(messages, temperature=0.7):
    output = gemma_pipe(
        text=messages,
        max_new_tokens=200,
        do_sample=True,
        temperature=temperature
    )
    return output[0]["generated_text"][-1]["content"]
##################################################################################################
##################################OCR + Generation Functions##############################
def split_text_into_lines(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        if font.getbbox(test_line)[2] <= max_width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    return lines

def calculate_text_positions_and_font_size(
    text, image_size, font_path, max_font_size=100, margin=20, position="top"
):
    width, height = image_size
    font_size = max_font_size

    while font_size > 10:
        font = ImageFont.truetype(font_path, font_size)
        max_line_width = width - 2 * margin
        lines = split_text_into_lines(text, font, max_line_width)
        total_text_height = sum(
            [font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]
        ) + (len(lines) - 1) * margin

        if total_text_height <= height / 2 - margin:
            break
        font_size -= 1

    positions = []
    if position == "top":
        y_offset = margin
    else:  # "bottom"
        y_offset = height - total_text_height - 2 * margin

    for line in lines:
        line_width = font.getbbox(line)[2] - font.getbbox(line)[0]
        x_position = (width - line_width) // 2
        positions.append((x_position, y_offset))
        y_offset += font.getbbox(line)[3] - font.getbbox(line)[1] + margin

    return font_size, positions, lines

def draw_text_with_outline(draw, position, text, font, outline_color, text_color, thickness):
    x, y = position
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text(position, text, font=font, fill=text_color)

def add_text_to_image(
    input_image_path,
    upper_text,
    lower_text,
    font_path="impact.ttf",
    outline_color=(0, 0, 0),
    text_color=(255, 255, 255),
    outline_thickness=2,
    max_font_size=100,
    margin=10,
):
    img = input_image_path
    draw = ImageDraw.Draw(img)

    top_font_size, top_positions, top_lines = calculate_text_positions_and_font_size(
        upper_text, img.size, font_path, max_font_size, margin, position="top"
    )
    bottom_font_size, bottom_positions, bottom_lines = calculate_text_positions_and_font_size(
        lower_text, img.size, font_path, max_font_size, margin, position="bottom"
    )

    top_font = ImageFont.truetype(font_path, top_font_size)
    bottom_font = ImageFont.truetype(font_path, bottom_font_size)

    for line, pos in zip(top_lines, top_positions):
        draw_text_with_outline(draw, pos, line, top_font, outline_color, text_color, outline_thickness)

    for line, pos in zip(bottom_lines, bottom_positions):
        draw_text_with_outline(draw, pos, line, bottom_font, outline_color, text_color, outline_thickness)
    return img

def generate_image(image_description, upper_text, lower_text, num_inf_steps=28, guidance_scale=3.5):
    image = pipeline_generation(
            image_description,
            num_inference_steps=num_inf_steps,
            guidance_scale=guidance_scale,
    ).images[0]
    final_meme = add_text_to_image(
        image,
        upper_text=upper_text,
        lower_text=lower_text,
        font_path="impact.ttf"
    )
    return final_meme
##################################################################################################

########################################APPLICATION###############################################
# Function to allow the user to upload an image
def upload_image(file_path=None):


    # Open file dialog to let user select an image
    #file_path = "data/new_img/23419.png"
    

    predicted = classification(file_path)
    if predicted == 1:
        message1 = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a direct assistant."}]
            },
            {
                "role": "user",
                "content": [
                            {"type": "image", "path": file_path},
                            {"type": "text", "text": "explain shortly why this meme is offensive? start with 'This meme is offensive'"}
                ]
            }
        ]
        message2 = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a direct assistant."}]
            },
            {
                "role": "user",
                "content": [
                            {"type": "image", "path": file_path},
                            {"type": "text", "text": "change the meme to be not offensive, give me image description and upper text and lower text only."}
                ]
            }
        ]
        explanation = meme_manipulation(message1)
        print(explanation)
        meme_convert = meme_manipulation(message2)
        print(meme_convert)
        meme_convert = meme_convert.replace("*", "")

        # Use regex to extract content without the labels
        # Updated regex without asterisks
        lower_match = re.search(r"Lower Text:\s*(.*)", meme_convert, re.DOTALL)
        lower_text = lower_match.group(1).strip() if lower_match else ""
        if lower_match:
            meme_convert = meme_convert[:lower_match.start()]  # Remove everything from 'Lower Text:' onward

        upper_match = re.search(r"Upper Text:\s*(.*)", meme_convert, re.DOTALL)
        upper_text = upper_match.group(1).strip() if upper_match else ""
        if upper_match:
            meme_convert = meme_convert[:upper_match.start()]  # Remove everything from 'Upper Text:' onward

        desc_match = re.search(r"Image Description:\s*(.*)", meme_convert, re.DOTALL)
        image_description = desc_match.group(1).strip() if desc_match else ""
        final_meme = generate_image(image_description, upper_text, lower_text)
        final_meme.save("alternative_meme.png")
        print("Alternative meme generated as alternative_meme.png")
    else:
        print("The meme is classified as non-offensive!\n You can use this meme in any platform you want.")

# Call the function
#upload_image()
##################################################################################################################