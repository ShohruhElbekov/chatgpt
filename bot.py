import asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
import aiofiles
import json
import time
import os
import openai

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data_file = "user_data.json"
questions_file = "user_questions.json"

user_data = {}
user_questions = {}

# Load user data from file
if os.path.exists(user_data_file):
    with open(user_data_file, "r") as f:
        user_data = json.load(f)

if os.path.exists(questions_file):
    with open(questions_file, "r") as f:
        user_questions = json.load(f)

languages = {
    "Uz": "🇺🇿 O‘zbekcha",
    "Ru": "🇷🇺 Русский",
    "En": "🇬🇧 English"
}

start_buttons = ReplyKeyboardMarkup(
    [[KeyboardButton("Start")]], resize_keyboard=True
)

lang_buttons = ReplyKeyboardMarkup(
    [[KeyboardButton("🇺🇿 O‘zbekcha"), KeyboardButton("🇷🇺 Русский"), KeyboardButton("🇬🇧 English")]],
    resize_keyboard=True
)

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        await message.reply("Tilni tanlang / Choose language / Выберите язык:", reply_markup=lang_buttons)
    else:
        await message.reply("Savolingizni yuboring:", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("📊 Statistika")]], resize_keyboard=True))

@app.on_message(filters.text & filters.private)
async def handle_message(client, message):
    user_id = str(message.from_user.id)
    text = message.text

    if text == "📊 Statistika":
        stats = f"Foydalanuvchilar soni: {len(user_data)}"
        await message.reply(stats)
        return

    if text in languages.values():
        for code, lang in languages.items():
            if text == lang:
                user_data[user_id] = {"lang": code}
                with open(user_data_file, "w") as f:
                    json.dump(user_data, f)
                await message.reply("Iltimos, savolingizni yuboring:")
                return

    if user_id not in user_data:
        await message.reply("Iltimos, avval tilni tanlang:", reply_markup=lang_buttons)
        return

    if not check_question_limit(user_id):
        await message.reply("⏳ Siz 2 soat ichida 10 ta savol yubordingiz. Iltimos, keyinroq urinib ko‘ring.")
        return

    await message.chat.send_action("typing")
    waiting = await message.reply("⏳ Ma'lumotlar to‘planmoqda...")

    try:
        answer = await ask_deepseek(text)
        await waiting.edit_text(answer)
        increment_question_count(user_id)
    except Exception as e:
        await waiting.edit_text("⚠️ Xatolik yuz berdi, keyinroq urinib ko‘ring.")
        print("Error:", e)

def check_question_limit(user_id):
    now = time.time()
    questions = user_questions.get(user_id, [])
    questions = [q for q in questions if now - q < 7200]
    user_questions[user_id] = questions
    return len(questions) < 10

def increment_question_count(user_id):
    user_questions[user_id].append(time.time())
    with open(questions_file, "w") as f:
        json.dump(user_questions, f)

async def ask_deepseek(prompt):
    max_tokens = 500 if len(prompt) < 100 else 1500
    response = openai.ChatCompletion.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=max_tokens
    )
    return response.choices[0].message["content"]

app.run()
