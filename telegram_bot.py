import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Telegram Bot Token (Ekran görüntündeki yeni token)
TELEGRAM_TOKEN = "8920384961:AAHtJVZTqJL3QseitzL6_0XAPCEHQqUZKt8"

PROMPTS = {
    "maryjane": "Sen Mary Jane'sin. Kullanıcının hem samimi dostu hem de zeki asistanısın. Doğal, yardımsever ve sıcak bir dille konuşursun.",
    "elraenn": "Sen Elraenn (Tuğkan Gönültaş) karakterine büründün. Samimi, mahalle kültüründen gelen, 'reis', 'kardeşim' gibi hitaplar kullanan, hikaye anlatıcılığı yüksek ve aşırı doğal bir dille tavsiyeler verirsin.",
    "egefitness": "Sen Ege Fitness karakterine büründün. Yüksek motivasyonlu, disiplin odaklı, hırslı, 'basmaya devam', 'bahane yok' mantığıyla konuşan son derece enerjik ve sert bir antrenör/dost gibi yaklaşırsın.",
    "buseaydin": "Sen Psikolog Buse Aydın üslubuna büründün. Empatik, duygu ve düşünceleri klinik bakış açısıyla analiz eden, farkındalık kazandıran, sakin ve yönlendirici bir dille destek olursun."
}

# Kullanıcıların aktif rol seçimi
user_roles = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_roles[update.effective_user.id] = "maryjane"
    await update.message.reply_text(
        "Merhaba! Ben Mary Jane. Telefonundan da seninleyim!\n\n"
        "Mod Değiştirmek İçin Komutlar:\n"
        "/maryjane - Varsayılan Dost & Asistan\n"
        "/elraenn - Elraenn Modu\n"
        "/egefitness - Ege Fitness Modu\n"
        "/buseaydin - Psikolog Buse Aydın Modu"
    )

async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.replace('/', '').lower()
    if command in PROMPTS:
        user_roles[update.effective_user.id] = command
        await update.message.reply_text(f"Mod Değiştirildi: {command.capitalize()}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_role = user_roles.get(user_id, "maryjane")
    sys_instruction = PROMPTS[current_role]
    
    user_text = update.message.text
    
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=user_text,
            config=types.GenerateContentConfig(system_instruction=sys_instruction)
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Aksaklık oluştu: {str(e)}")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["maryjane", "elraenn", "egefitness", "buseaydin"], set_role))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Mary Jane Telegram Botu Çalışıyor...")
    app.run_polling()