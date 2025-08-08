"""
Telegram Bot Handlers
"""

import os
import urllib.request
from typing import Optional
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .config import BotConfig


class MemeBot:
    """Main bot class handling all user interactions"""
    
    def __init__(self):
        BotConfig.ensure_temp_dir()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        welcome_message = (
            "👋 Hello! I'm your meme classifier 🤖\n\n"
            "Send me any meme 🖼️ and I'll check if it's offensive 🚫 or safe ✅.\n"
            "If needed, I'll generate a better one! 💡\n\n"
            "Just send me an image to get started!"
        )
        await update.message.reply_text(welcome_message)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle uploaded photos"""
        try:
            # Get the highest resolution photo
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            file_path = os.path.join(BotConfig.TEMP_DIR, f"{photo.file_id}.jpg")
            
            # Download the image
            await file.download_to_drive(file_path)
            context.user_data['original_image_path'] = file_path
            
            await update.message.reply_text("📥 Thanks! Processing your meme, please wait... 🔍")
            
            # Send to processing server
            await self._process_image(update, context, file_path)
            
        except Exception as e:
            await update.message.reply_text(
                f"⚠️ An error occurred while processing your image: {str(e)}\n"
                "Please try again later."
            )
    
    async def _process_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: str) -> None:
        """Send image to processing server and handle response"""
        try:
            with open(file_path, 'rb') as img:
                response = requests.post(BotConfig.FLASK_SERVER_URL, files={'image': img}, timeout=30)
            
            if response.status_code != 200:
                await update.message.reply_text("⚠️ Processing server is unavailable. Please try again later.")
                return
            
            result = response.json()
            await self._handle_classification_result(update, context, result)
            
        except requests.exceptions.RequestException as e:
            await update.message.reply_text(
                "⚠️ Connection to processing server failed. Please try again later."
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ An unexpected error occurred: {str(e)}")
    
    async def _handle_classification_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: dict) -> None:
        """Handle the classification result from the server"""
        status = result.get("status", "")
        meme_path = result.get("meme", "")
        explanation = result.get("explanation", "")
        question = result.get("question", "")
        
        if status == "Non-Offensive":
            await self._handle_non_offensive(update, context)
        elif status == "Offensive":
            await self._handle_offensive(update, context, explanation, meme_path, question)
        else:
            await update.message.reply_text("❓ Unexpected server response.")
    
    async def _handle_non_offensive(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle non-offensive meme"""
        await update.message.reply_text("✅ This meme is NON-OFFENSIVE!")
        
        # Send back the original image
        file_path = context.user_data.get('original_image_path')
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as img:
                await update.message.reply_photo(photo=img)
            os.remove(file_path)
        
        await update.message.reply_text("🟢 Safe to use!")
        context.user_data.pop('original_image_path', None)
    
    async def _handle_offensive(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              explanation: str, meme_path: str, question: str) -> None:
        """Handle offensive meme"""
        await update.message.reply_text("🚫 This meme is OFFENSIVE!")
        await update.message.reply_text(f"🧐 *Why?*\n{explanation}", parse_mode="Markdown")
        await update.message.reply_text("⏳ Generating a better version for you...")
        
        # Download and send alternative meme
        try:
            await self._send_alternative_meme(update, context, meme_path)
            await self._ask_for_approval(update, context, question)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Failed to generate alternative: {str(e)}")
    
    async def _send_alternative_meme(self, update: Update, context: ContextTypes.DEFAULT_TYPE, meme_path: str) -> None:
        """Download and send the alternative meme"""
        # Construct the full URL
        if meme_path.startswith("/"):
            new_meme_url = BotConfig.FLASK_SERVER_URL.replace("/upload", meme_path)
        else:
            new_meme_url = BotConfig.FLASK_SERVER_URL.replace("/upload", "/" + meme_path)
        
        temp_filename = os.path.join(BotConfig.TEMP_DIR, "alt_" + os.path.basename(meme_path))
        urllib.request.urlretrieve(new_meme_url, temp_filename)
        
        with open(temp_filename, 'rb') as alt_img:
            await update.message.reply_photo(photo=alt_img)
        
        os.remove(temp_filename)
        await update.message.reply_text("✨ Here's the new version!")
    
    async def _ask_for_approval(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question: str) -> None:
        """Ask user for approval of the generated meme"""
        keyboard = [
            [InlineKeyboardButton("👍 Yes", callback_data="approve_yes"),
             InlineKeyboardButton("👎 No", callback_data="approve_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(question, reply_markup=reply_markup)
    
    async def handle_approval(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle user approval/disapproval"""
        query = update.callback_query
        await query.answer()
        decision = query.data
        
        if decision == "approve_yes":
            await self._handle_approval_yes(query, context)
        elif decision == "approve_no":
            await self._handle_approval_no(query, context)
    
    async def _handle_approval_yes(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle approval yes"""
        await query.edit_message_text(
            "✨ Great! I'm glad you liked it. To classify another meme, just send me an image anytime!"
        )
        # Cleanup
        self._cleanup_user_data(context)
    
    async def _handle_approval_no(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle approval no - offer temperature selection"""
        original = context.user_data.get('original_image_path')
        if not original or not os.path.exists(original):
            await query.edit_message_text("❌ Original image not found. Please try again with a new image.")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("Low (0.3)", callback_data="temp_0.3"),
                InlineKeyboardButton("Default (0.7)", callback_data="temp_0.7"),
                InlineKeyboardButton("High (1.0)", callback_data="temp_1.0")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "🤔 Let's try again with a different creativity level. Choose Creativity Level:",
            reply_markup=reply_markup
        )
    
    async def handle_temperature(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle temperature selection for regeneration"""
        query = update.callback_query
        await query.answer()
        
        # Extract temperature value
        temp = float(query.data.split("_")[1])
        context.user_data['temperature'] = temp
        original = context.user_data.get('original_image_path')
        
        if not original or not os.path.exists(original):
            await query.edit_message_text("❌ Original image not found. Please try again with a new image.")
            return
        
        await query.edit_message_text(f"🌡️ Creativity set to {temp}. Regenerating…")
        
        try:
            # Re-send image with temperature parameter
            with open(original, 'rb') as img_file:
                response = requests.post(
                    BotConfig.FLASK_SERVER_URL,
                    files={'image': img_file},
                    data={'temperature': temp},
                    timeout=30
                )
            
            if response.status_code != 200:
                await query.message.reply_text("⚠️ Failed to regenerate. Try again later.")
                return
            
            result = response.json()
            await self._send_regenerated_meme(query, context, result)
            
        except Exception as e:
            await query.message.reply_text(f"⚠️ Regeneration failed: {str(e)}")
    
    async def _send_regenerated_meme(self, query, context: ContextTypes.DEFAULT_TYPE, result: dict) -> None:
        """Send the regenerated meme and ask for approval"""
        meme_path = result.get("meme", "")
        
        # Download and send the new meme
        if meme_path.startswith("/"):
            new_url = BotConfig.FLASK_SERVER_URL.replace("/upload", meme_path)
        else:
            new_url = BotConfig.FLASK_SERVER_URL.replace("/upload", "/" + meme_path)
        
        temp_fn = os.path.join(BotConfig.TEMP_DIR, f"temp_{os.path.basename(meme_path)}")
        urllib.request.urlretrieve(new_url, temp_fn)
        
        with open(temp_fn, 'rb') as photo:
            await query.message.reply_photo(photo=photo)
        
        os.remove(temp_fn)
        
        # Ask for approval again
        keyboard = [
            [InlineKeyboardButton("👍 Yes", callback_data="approve_yes"),
             InlineKeyboardButton("👎 No", callback_data="approve_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            result.get("question", "Do you like this version?"),
            reply_markup=reply_markup
        )
    
    def _cleanup_user_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clean up user data and temporary files"""
        original_path = context.user_data.get('original_image_path')
        if original_path and os.path.exists(original_path):
            os.remove(original_path)
        
        context.user_data.pop('original_image_path', None)
        context.user_data.pop('temperature', None)
