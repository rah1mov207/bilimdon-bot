import os
from groq import Groq
from pypdf import PdfReader
from telegram import Update, Inlineiser
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ==============================
# TOKENLAR
# ==============================

TELEGRAM_TOKEN = "8595411023:AAHY5T4bM0RJYSebjW-GPuSh4s1Vb7slARE"
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

# ==============================
# FOYDALANUVCHI XOTIRASI
# ==============================

user_memory = {}

# ==============================
# MATN CHAT (XOTIRA BILAN)
# ==============================

def chat_text(user_id, prompt):

    if user_id not in user_memory:
        user_memory[user_id] = [
            {
                "role": "system",
                "content": "Sen Bilimdon Botsan. Har doim o‘zbek tilida foydali javob ber."
            }
        ]

    user_memory[user_id].append({
        "role": "user",
        "content": prompt
    })

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=user_memory[user_id]
    )

    reply = completion.choices[0].message.content

    user_memory[user_id].append({
        "role": "assistant",
        "content": reply
    })

    # xotirani cheklash (oxirgi 20 xabar)
    user_memory[user_id] = user_memory[user_id][-20:]

    return reply

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
                    {"type": "text", "text": "Bu rasmni batafsil tahlil qil."},
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

    return text[:8000]

# ==============================
# AUDIO → TEXT
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
        "Assalomu alaykum! Men Bilimdon Bot 🤖\n"
        "Savol yozing, rasm, PDF yoki ovoz yuboring."
    )

# ==============================
# TEXT HANDLER
# ==============================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    user_text = update.message.text.lower()

    if "rasm yarat" in user_text:

        keyboard = [[
            InlineKeyboardButton(
                "🖼 Rasm yaratish botini ochish",
                url="https://t.me/mening_gpt_botim_bot"
            )
        ]]

        await update.message.reply_text(
            "Men rasm yaratolmayman. Quyidagi botdan foydalaning:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    await update.message.reply_text("O‘ylayapman...")

    reply = chat_text(user_id, update.message.text)

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

    text = analyze_pdf(file_path)

    reply = chat_text(update.message.from_user.id, text)

    await update.message.reply_text(reply)

# ==============================
# VOICE HANDLER
# ==============================

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Ovoz tahlil qilinmoqda...")

    voice = update.message.voice

    file = await context.bot.get_file(voice.file_id)

    file_path = "voice.ogg"

    await file.download_to_drive(file_path)

    text = transcribe_audio(file_path)

    reply = chat_text(update.message.from_user.id, text)

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

    print("Bilimdon Bot ishga tushdi")

    app.run_polling()

# ==============================

if __name__ == "__main__":
    main()
