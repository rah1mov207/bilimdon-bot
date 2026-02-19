import os
import requests
from groq import Groq
from pypdf import PdfReader
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# ==============================
# TOKENLAR
# ==============================

TELEGRAM_TOKEN = "8595411023:AAHY5T4bM0RJYSebjW-GPuSh4s1Vb7slARE"
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

# ==============================
# MATN CHAT
# ==============================

def chat_text(prompt):

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )

    return completion.choices[0].message.content

# ==============================
# RASM ANALIZ
# ==============================

def analyze_image(image_url):

    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Bu rasmni tahlil qil."},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                ]
            }
        ]
    )

    return completion.choices[0].message.content

# ==============================
# PDF ANALIZ
# ==============================

def analyze_pdf(file_path):

    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text()

    return chat_text(f"Quyidagi PDF mazmunini tushuntir:\n{text[:8000]}")

# ==============================
# OVOZNI MATNGA AYLANTRISH
# ==============================

def transcribe_audio(file_path):

    with open(file_path, "rb") as audio_file:

        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3"
        )

    return transcription.text

# ==============================
# START
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
         "Assalomu alaykum! Men Bilimdon Bot 🤖\n\n"
        "Qanday yordam bera olaman? \n"
    )

# ==============================
# MATN HANDLER
# ==============================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_text = update.message.text.lower()

    # agar foydalanuvchi rasm yaratmoqchi bo‘lsa
    if "rasm yarat" in user_text or "/image" in user_text:

        keyboard = [
            [InlineKeyboardButton(
                "🖼 Rasm yaratish botini ochish",
                url="https://t.me/mening_gpt_botim_bot"
            )]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Men rasm yaratolmayman.\n"
            "Rasm yaratish uchun quyidagi botdan foydalaning:",
            reply_markup=reply_markup
        )

        return

    # oddiy savollarga javob
    await update.message.reply_text("O‘ylayapman...")

    reply = chat_text(update.message.text)

    await update.message.reply_text(reply)

# ==============================
# PHOTO HANDLER
# ==============================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Rasm tahlil qilinmoqda...")

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    image_url = file.file_path

    result = analyze_image(image_url)

    await update.message.reply_text(result)

# ==============================
# PDF HANDLER
# ==============================

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("PDF o‘qilmoqda...")

    document = update.message.document
    file = await context.bot.get_file(document.file_id)

    file_path = "temp.pdf"
    await file.download_to_drive(file_path)

    result = analyze_pdf(file_path)

    await update.message.reply_text(result)

# ==============================
# VOICE HANDLER
# ==============================

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Ovoz matnga aylantirilmoqda...")

    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    file_path = "voice.ogg"
    await file.download_to_drive(file_path)

    text = transcribe_audio(file_path)

    reply = chat_text(text)

    await update.message.reply_text(reply)

# ==============================
# MAIN
# ==============================

def main():

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("Bilimdon Bot ULTIMATE ishga tushdi")

    app.run_polling()

# ==============================

if __name__ == "__main__":
    main()
