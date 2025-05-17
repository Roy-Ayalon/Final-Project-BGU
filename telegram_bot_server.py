import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, CallbackQueryHandler,
    ContextTypes
)

TOKEN       = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-app.up.railway.app

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Check Meme", callback_data="check")]]
    await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👋 Send me a meme (as photo).",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please send your meme now."
    )

async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # download the highest-res photo
    file = await update.message.photo[-1].get_file()
    path = f"/tmp/{file.file_id}.jpg"
    await file.download_to_drive(path)
    await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text="✅ Meme received! Forwarding for analysis…"
    )
    # TODO: call your cluster API here
    # resp = requests.post(CLUSTER_URL+"/analyze", files={"meme": open(path,"rb")})
    # await ctx.bot.send_message(chat_id=..., text=resp.json()["result"])

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check_callback, pattern="^check$"))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

if __name__ == "__main__":
    # expose webhook endpoint
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "8443")),
        webhook_url=f"{WEBHOOK_URL}/webhook/{TOKEN}"
    )