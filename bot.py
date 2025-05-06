
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from PIL import Image
import io
import os

user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛌 Day Off", callback_data='day_off')],
        [InlineKeyboardButton("🏖 Vacation", callback_data='vacation')],
        [InlineKeyboardButton("💼 Business Trip", callback_data='business_trip')],
    ]
    await update.message.reply_text("Выбери тип аватарки:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "business_trip":
        keyboard = [
            [InlineKeyboardButton("🌍 UTC", callback_data='business_trip_utc')],
            [InlineKeyboardButton("🇦🇪 Dubai (+4)", callback_data='business_trip_dubai')],
            [InlineKeyboardButton("🇷🇺 Moscow (+3)", callback_data='business_trip_moscow')],
            [InlineKeyboardButton("🇺🇸 New York (-4)", callback_data='business_trip_ny')],
        ]
        await query.message.reply_text("Выбери часовой пояс:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        user_state[user_id] = query.data
        await query.message.reply_text("Отправь мне свою фотографию")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_state:
        await update.message.reply_text("Сначала выбери тип аватарки через /start")
        return

    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    user_img = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")

    overlay_type = user_state[user_id]
    overlay_path = f"overlays/{overlay_type}.png"

    if not os.path.exists(overlay_path):
        await update.message.reply_text(f"Оверлей {overlay_type} не найден.")
        return

    overlay = Image.open(overlay_path).convert("RGBA")
    overlay = overlay.resize(user_img.size)

    combined = Image.alpha_composite(user_img, overlay)

    bio = io.BytesIO()
    bio.name = 'avatar.png'
    combined.save(bio, 'PNG')
    bio.seek(0)

    await update.message.reply_photo(photo=bio)

def main():
    import os
    token = os.getenv("TELEGRAM_BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
