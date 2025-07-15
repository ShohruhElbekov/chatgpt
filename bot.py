from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import time
import requests
import os

API_ID = 23346001
API_HASH = "08c63cda730a00374392062e09c426d1"
BOT_TOKEN = "8161140522:AAHHIJaLYmlPCsTJrInDxDRfKWTfzXaMDXI"
TOGETHER_API_KEY = "10888df0044c2a80602f2b4238e376fdd95fc62a6ab824b265a074ff5b1b1fe9"
TOGETHER_MODEL = "deepseek-ai/DeepSeek-V3"
ADMIN_IDS = [7181480233]
CHANNELS = ["@texno_yangiliklr_UZ", "@kompyuterishlaridastirlar"]

app = Client("deepseek_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

MESSAGE_LIMIT = 10
TIME_WINDOW = 2 * 60 * 60  # 2 soat

user_messages = {}
user_language = {}

def load_languages():
    if os.path.exists("user_languages.txt"):
        with open("user_languages.txt", "r") as f:
            for line in f:
                parts = line.strip().split(":", 1)
                if len(parts) == 2:
                    user_language[int(parts[0])] = parts[1]

def save_language(user_id, lang):
    user_language[user_id] = lang
    with open("user_languages.txt", "a") as f:
        f.write(f"{user_id}:{lang}\n")

def load_users():
    users = set()
    if os.path.exists("user_ids.txt"):
        with open("user_ids.txt", "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if parts:
                    users.add(int(parts[0]))
    return users

def save_user(user):
    user_id = user.id
    if user_id not in all_users:
        username = f"@{user.username}" if user.username else "NoUsername"
        fullname = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
        with open("user_ids.txt", "a", encoding="utf-8") as f:
            f.write(f"{user_id} | {username} | {fullname}\n")
        all_users.add(user_id)

all_users = load_users()
load_languages()

@app.on_message(filters.command("start") & filters.private)
def start(client, message):
    user = message.from_user
    user_id = user.id
    save_user(user)

    if user_id in user_language:
        message.reply_text("✅ Botga xush kelibsiz! Savolingizni yozing.")
        return

    keyboard = ReplyKeyboardMarkup(
        [["🇺🇿 O‘zbekcha", "🇷🇺 Русский", "🇬🇧 English"]],
        resize_keyboard=True, one_time_keyboard=True
    )
    message.reply_text("🌐 Iltimos, tilni tanlang:\n\nPlease choose your language:", reply_markup=keyboard)

@app.on_message(filters.text & filters.private)
def handle_message(client, message):
    user = message.from_user
    user_id = user.id
    text = message.text

    save_user(user)

    if user_id not in user_language:
        langs = {"🇺🇿 O‘zbekcha": "uz", "🇷🇺 Русский": "ru", "🇬🇧 English": "en"}
        lang = langs.get(text)
        if lang:
            save_language(user_id, lang)
            buttons = [
                [InlineKeyboardButton(ch[1:], url=f"https://t.me/{ch[1:]}")] for ch in CHANNELS
            ]
            buttons.append([InlineKeyboardButton("✅ Davom etish", callback_data="continue")])
            message.reply_text("📢 Quyidagi kanallarga obuna bo‘ling va davom eting:", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            message.reply_text("❗️ Iltimos, tilni tanlang.")
        return

    # Limit tekshiruvi
    now = time.time()
    timestamps = user_messages.get(user_id, [])
    timestamps = [t for t in timestamps if now - t < TIME_WINDOW]
    if len(timestamps) >= MESSAGE_LIMIT:
        lang = user_language.get(user_id, "uz")
        messages = {
            "uz": "⏳ 2 soatda 10 ta savol berishingiz mumkin. Keyinroq urinib ko‘ring.",
            "ru": "⏳ Вы задали 10 вопросов за 2 часа. Пожалуйста, попробуйте позже.",
            "en": "⏳ You've asked 10 questions in 2 hours. Please try again later."
        }
        message.reply_text(messages.get(lang))
        return

    try:
        message.reply_chat_action("typing")  # ⌨️ "Typing..." ko‘rsatish
        reply = ask_deepseek(text)
        message.reply_text(reply)
        timestamps.append(now)
        user_messages[user_id] = timestamps

        # Log
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {user_id}: {text}\n")
    except Exception as e:
        print(f"Xato: {e}")
        message.reply_text("❌ Javobni olishda xatolik. Keyinroq urinib ko‘ring.")

@app.on_callback_query(filters.regex("continue"))
def continue_handler(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    lang = user_language.get(user_id, "uz")
    texts = {
        "uz": "✅ Botga xush kelibsiz! Endi savolingizni yozishingiz mumkin.",
        "ru": "✅ Добро пожаловать! Можете отправить свой вопрос.",
        "en": "✅ Welcome! You can now ask your question."
    }
    callback_query.message.reply_text(texts.get(lang, "✅ You can now chat."))
    callback_query.answer()

def ask_deepseek(prompt):
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": TOGETHER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]

@app.on_message(filters.command("stat") & filters.private)
def show_stats(client, message):
    if message.from_user.id not in ADMIN_IDS:
        return
    message.reply_text(f"📊 Umumiy foydalanuvchilar: {len(all_users)}")

@app.on_message(filters.command("logs") & filters.private)
def show_logs(client, message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if not os.path.exists("log.txt"):
        message.reply_text("📂 Log fayli topilmadi.")
        return
    with open("log.txt", "r", encoding="utf-8") as f:
        logs = f.readlines()[-30:]
    message.reply_text("📝 Oxirgi savollar:\n\n" + "".join(logs))

print("✅ DeepSeek bot ishga tushdi!")
app.run()
