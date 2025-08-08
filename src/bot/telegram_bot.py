from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests
import os
import json

BOT_TOKEN = '7305586081:AAGnkSchiRv7VvltvW92VqnMO_uiUUaf9NY'
FLASK_SERVER_URL = 'http://132.72.107.202:5002/upload'  # ✅ RIGHT

# Keys in context.user_data:
# 'original_image_path': path to the downloaded image

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_path = f"{photo.file_id}.jpg"
    await file.download_to_drive(file_path)
    context.user_data['original_image_path'] = file_path
    await update.message.reply_text("📥 Thanks! Processing your meme, please wait... 🔍")

    with open(file_path, 'rb') as img:
        response = requests.post(FLASK_SERVER_URL, files={'image': img})

    if response.status_code != 200:
        await update.message.reply_text("⚠️ Something went wrong. Please try again later.")
        return

    result = response.json()

    status = result.get("status", "")
    meme_path = result.get("meme", "")
    explanation = result.get("explanation", "")
    message = result.get("message", "")
    question = result.get("question", "")

    if status == "Non-Offensive":
        await update.message.reply_text("✅ This meme is NON-OFFENSIVE!")
        # Download the original image again to send back
        with open(file_path, 'wb') as img_out:
            file2 = await context.bot.get_file(photo.file_id)
            await file2.download_to_drive(file_path)
        with open(file_path, 'rb') as img:
            await update.message.reply_photo(photo=img)
        os.remove(file_path)
        await update.message.reply_text("🟢 Safe to use!")
    elif status == "Offensive":
        await update.message.reply_text("🚫 This meme is OFFENSIVE!")
        await update.message.reply_text(f"🧐 *Why?*\n{explanation}", parse_mode="Markdown")
        await update.message.reply_text("⏳ Generating a better version for you...")

        # Download and send new meme
        # Compose the full URL for the alternative meme
        # Download and send new meme
        if meme_path.startswith("/"):
            new_meme_url = FLASK_SERVER_URL.replace("/upload", meme_path)
        else:
            new_meme_url = FLASK_SERVER_URL.replace("/upload", "/" + meme_path)

        import urllib.request
        temp_filename = "alt_" + os.path.basename(meme_path)
        urllib.request.urlretrieve(new_meme_url, temp_filename)

        with open(temp_filename, 'rb') as alt_img:
            await update.message.reply_photo(photo=alt_img)

        os.remove(temp_filename)
        await update.message.reply_text("✨ Here's the new version!")

        # Ask for approval
        keyboard = [
            [InlineKeyboardButton("👍 Yes", callback_data="approve_yes"),
             InlineKeyboardButton("👎 No", callback_data="approve_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(question, reply_markup=reply_markup)
    else:
        await update.message.reply_text("❓ Unexpected server response.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! I'm your meme classifier 🤖\nSend me any meme 🖼️ and I'll check if it's offensive 🚫 or safe ✅. If needed, I’ll generate a better one! 💡")

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    decision = query.data  # "approve_yes" or "approve_no"
    original = context.user_data.get('original_image_path')

    if decision == "approve_yes":
        # End conversation, show restart hint, cleanup
        await query.edit_message_text(
            "✨ Great! I'm glad you liked it. To classify another meme, just send me an image anytime!"
        )
        # Cleanup stored path
        context.user_data.pop('original_image_path', None)

    elif decision == "approve_no" and original:
        # Ask user to pick a generation temperature
        keyboard = [
            [
                InlineKeyboardButton("Low (0.3)", callback_data="temp_0.3"),
                InlineKeyboardButton("Default (0.7)", callback_data="temp_0.7"),
                InlineKeyboardButton("High (1.0)", callback_data="temp_1.0")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🤔 Let's try again with a different creativity level. Choose Creativity Level:",
            reply_markup=reply_markup
        )
        return
    
async def handle_temperature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # extract the number after “temp_”
    temp = float(query.data.split("_")[1])
    context.user_data['temperature'] = temp
    original = context.user_data.get('original_image_path')

    # Let user know
    await query.edit_message_text(f"🌡️ Creativity set to {temp}. Regenerating…")

    # Re-send image plus temperature to Flask
    with open(original, 'rb') as img_file:
        resp = requests.post(
            FLASK_SERVER_URL,
            files={'image': img_file},
            data={'temperature': temp}
        )
    if resp.status_code != 200:
        await context.bot.send_message(update.effective_chat.id, "⚠️ Failed to regenerate. Try again later.")
        return

    result = resp.json()
    # Download & send the new meme just like you do in handle_photo:
    meme_path = result.get("meme", "")
    if meme_path.startswith("/"):
        new_url = FLASK_SERVER_URL.replace("/upload", meme_path)
    else:
        new_url = FLASK_SERVER_URL.replace("/upload", "/" + meme_path)
    import urllib.request
    temp_fn = f"temp_{os.path.basename(meme_path)}"
    urllib.request.urlretrieve(new_url, temp_fn)
    with open(temp_fn, 'rb') as photo:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)
    os.remove(temp_fn)

    # Then ask approval again
    keyboard = [
        [InlineKeyboardButton("👍 Yes", callback_data="approve_yes"),
         InlineKeyboardButton("👎 No", callback_data="approve_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result.get("question", "Do you like this version?"),
        reply_markup=reply_markup
    )

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    # Any non-photo message triggers the welcome greeting
    app.add_handler(MessageHandler(filters.ALL & ~filters.PHOTO, start))
    app.add_handler(CallbackQueryHandler(handle_approval, pattern="^approve_"))
    app.add_handler(CallbackQueryHandler(handle_temperature, pattern="^temp_"))
    app.run_polling()