
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from PIL import Image
import io
import os

user_state = {}

# Menu options
overlay_options = [
    [InlineKeyboardButton("🛌 Day Off", callback_data='day_off')],
    [InlineKeyboardButton("🏖 Vacation", callback_data='vacation')],
    [InlineKeyboardButton("💼 Business Trip", callback_data='business_trip')],
]

timezone_options = [
    [InlineKeyboardButton("🌍 UTC", callback_data='business_trip_utc')],
    [InlineKeyboardButton("🇦🇪 Dubai (+4)", callback_data='business_trip_dubai')],
    [InlineKeyboardButton("🇷🇺 Moscow (+3)", callback_data='business_trip_moscow')],
    [InlineKeyboardButton("🇺🇸 New York (-4)", callback_data='business_trip_ny')],
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Choose avatar type:", reply_markup=InlineKeyboardMarkup(overlay_options))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "business_trip":
        await query.message.reply_text("Choose a time zone:", reply_markup=InlineKeyboardMarkup(timezone_options))
    else:
        user_state[user_id] = query.data
        await query.message.reply_text("Now send me your photo.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_state:
        await update.message.reply_text("Please start with /start and choose an avatar type first.")
        return

    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    user_img = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")

    # Crop to square
    width, height = user_img.size
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    user_img = user_img.crop((left, top, right, bottom))

    overlay_type = user_state[user_id]
    overlay_path = f"overlays/{overlay_type}.png"

    if not os.path.exists(overlay_path):
        await update.message.reply_text(f"Overlay '{overlay_type}' not found.")
        return

    overlay = Image.open(overlay_path).convert("RGBA")
    overlay = overlay.resize(user_img.size)

    combined = Image.alpha_composite(user_img, overlay)

    output = io.BytesIO()
    output.name = "avatar.png"
    combined.save(output, "PNG")
    output.seek(0)

    # Send as file (uncompressed)
    await update.message.reply_document(document=InputFile(output), filename="avatar.png")

    # Show menu again
    await update.message.reply_text("Avatar created! Want to try again?", reply_markup=InlineKeyboardMarkup(overlay_options))

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
