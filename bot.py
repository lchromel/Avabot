
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from PIL import Image
import io
import os

user_state = {}

overlay_options = [
    [InlineKeyboardButton("🛌 Day Off", callback_data='day_off')],
    [InlineKeyboardButton("🏖 Vacation", callback_data='vacation')],
    [InlineKeyboardButton("💼 Business Trip", callback_data='business_trip')],
]

timezone_options = [
    [InlineKeyboardButton("🌎 LATAM (MSK –8)", callback_data='business_trip_latam')],
    [InlineKeyboardButton("🌍 AFRICA (MSK –3)", callback_data='business_trip_africa')],
    [InlineKeyboardButton("🇵🇰 PAKISTAN (MSK +2)", callback_data='business_trip_pakistan')],
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

async def fallback_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please choose avatar type first: /start")

async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    overlay_type = user_state.get(user_id)

    if not overlay_type:
        await update.message.reply_text("Please choose avatar type first: /start")
        return

    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
    elif update.message.document and update.message.document.mime_type.startswith("image/"):
        photo_file = await update.message.document.get_file()
    else:
        await update.message.reply_text("Please send an image file or photo.")
        return

    photo_bytes = await photo_file.download_as_bytearray()
    user_img = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")

    # Crop to square
    width, height = user_img.size
    min_dim = min(width, height)
    user_img = user_img.crop((
        (width - min_dim) // 2,
        (height - min_dim) // 2,
        (width + min_dim) // 2,
        (height + min_dim) // 2
    ))

    overlay_path = f"overlays/{overlay_type}.png"
    if not os.path.exists(overlay_path):
        await update.message.reply_text(f"Overlay '{overlay_type}' not found.")
        return

    overlay = Image.open(overlay_path).convert("RGBA").resize(user_img.size)
    combined = Image.alpha_composite(user_img, overlay)

    output = io.BytesIO()
    output.name = "avatar.png"
    combined.save(output, "PNG")
    output.seek(0)

    await update.message.reply_document(document=InputFile(output), filename="avatar.png")

    # Reset user session
    user_state.pop(user_id, None)

    await update.message.reply_text("Avatar created! Want to try again?", reply_markup=InlineKeyboardMarkup(overlay_options))

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), fallback_text_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, image_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
