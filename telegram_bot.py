from telegram.ext import ApplicationBuilder
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, filters
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup




TOKEN = "7305586081:AAGnkSchiRv7VvltvW92VqnMO_uiUUaf9NY"


app = ApplicationBuilder() \
    .token(TOKEN) \
    .build()

async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm your bot. How can I assist you today?")
    keyboard = [
        [InlineKeyboardButton("Meme classification", callback_data='option1')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please choose an option:", reply_markup=reply_markup)

async def handle_message(update, context):
    user_message = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You said: {user_message}")
    keyboard = [
        [InlineKeyboardButton("Meme classification", callback_data='option1')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please choose an option:", reply_markup=reply_markup)

async def handle_button(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == 'option1':
        await context.bot.send_message(chat_id=query.message.chat.id, text="You selected Meme classification.")
        # Here you can add the logic for meme classification
    else:
        await context.bot.send_message(chat_id=query.message.chat.id, text="Unknown option.")
    keyboard = [
        [InlineKeyboardButton("Meme classification", callback_data='option1')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=query.message.chat.id, text="Please choose an option:", reply_markup=reply_markup)
    
async def handle_error(update, context):
    print(f"Update {update} caused error {context.error}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="An error occurred. Please try again later.")

def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_error_handler(handle_error)

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()