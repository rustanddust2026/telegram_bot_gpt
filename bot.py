from telegram import Update
from telegram.ext import (ApplicationBuilder,CallbackQueryHandler,CommandHandler,ContextTypes,MessageHandler,filters)

import os
import tempfile

from gpt import ChatGptService
from util import (default_callback_handler,load_message,load_prompt,send_image,send_text,send_text_buttons,send_voice_file,show_main_menu)

import credentials

chat_modes = {}
current_person = {}
quiz_topic = {}
quiz_score = {}
quiz_waiting = {}

personage = [
    "talk_cobain",
    "talk_queen",
    "talk_tolkien",
    "talk_nietzsche",
    "talk_hawking",
]

QUIZ_TOPICS = ["quiz_prog", "quiz_math", "quiz_biology"]

QUIZ_TOPIC_BUTTONS = {
    "quiz_prog": "Програмування",
    "quiz_math": "Математика",
    "quiz_biology": "Біологія",
}

QUIZ_RESULT_BUTTONS = {
    "quiz_more": "Ще питання",
    "quiz_change": "Інша тема",
    "quiz_end": "Закінчити",
}


def clear_quiz_state(user_id: int) -> None:
    quiz_topic.pop(user_id, None)
    quiz_score.pop(user_id, None)
    quiz_waiting.pop(user_id, None)


async def show_quiz_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_text_buttons(update,context,load_message("quiz"),{**QUIZ_TOPIC_BUTTONS, "quiz_end": "Закінчити"})


async def send_quiz_question(update: Update,context: ContextTypes.DEFAULT_TYPE,user_id: int,topic_key: str):
    quiz_topic[user_id] = topic_key
    response = await chat_gpt.send_question(load_prompt("quiz"), topic_key)
    quiz_waiting[id_of_user] = True
    await send_text(update, context, response)


async def send_quiz_more_question(update: Update,context: ContextTypes.DEFAULT_TYPE,id_of_user: int,):
    response = await chat_gpt.add_message("quiz_more")
    quiz_waiting[id_of_user] = True
    await send_text(update, context, response)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_of_user = update.effective_user.id
    chat_modes[id_of_user] = None
    current_person.pop(id_of_user, None)
    clear_quiz_state(id_of_user)

    text = load_message("main")
    await send_image(update, context, "main")
    await send_text(update, context, text)
    await show_main_menu(update,context,{
            "start": "Головне меню",
            "random": "Дізнатися випадковий цікавий факт 🧠",
            "gpt": "Задати питання чату GPT 🤖",
            "talk": "Поговорити з відомою особистістю 👤",
            "quiz": "Взяти участь у квізі ❓",
            "voice": "Голосовий ChatGPT 🎤",
        },
    )


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = load_prompt("random")
    response = await chat_gpt.send_question(prompt, "Give random facts")
    await send_image(update, context, "random")
    await send_text_buttons(
        update,
        context,
        response,{
            "random_end": "Закінчити",
            "random_more": "Хочу ще факт",
        },
    )


async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_modes[update.effective_user.id] = "GPT_MODE"
    chat_gpt.set_prompt(load_prompt("gpt"))
    await send_image(update, context, "gpt")
    await send_text(update, context, load_message("gpt"))


async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_modes[update.effective_user.id] = "VOICE_MODE"
    chat_gpt.set_prompt(load_prompt("voice"))
    await send_image(update, context, "voice")
    await send_text(update, context, load_message("voice"))


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_of_user = update.effective_user.id
    if chat_modes.get(id_of_user) != "VOICE_MODE":
        await send_text(
            update,
            context,
            "Натисніть /voice для початку .",
        )
        return

    voice_file = await context.bot.get_file(update.message.voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_in:
        input_path = tmp_in.name

    output_path = None
    try:
        await voice_file.download_to_drive(input_path)
        text = chat_gpt.speech_to_text(input_path)
        response = await chat_gpt.add_message(text)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_out:
            output_path = tmp_out.name

        chat_gpt.text_to_speech(response, output_path)
        await send_voice_file(update, context, output_path)
        await send_text_buttons(
            update,
            context,
            response,
            {"voice_end": "Закінчити"},
        )
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)
        if output_path and os.path.exists(output_path):
            os.unlink(output_path)


async def voice_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    id_of_user = update.callback_query.from_user.id

    if query == "voice_end":
        chat_modes[id_of_user] = None
        await start(update, context)

    await update.callback_query.answer()


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_modes[user_id] = "TALK_MODE"
    current_person.pop(user_id, None)

    await send_image(update, context, "talk")
    await send_text_buttons(update,context,load_message("talk"),{
            "talk_cobain": "Курт Кобейн 🎸",
            "talk_queen": "Єлизавета II 👑",
            "talk_tolkien": "Джон Толкін 📖",
            "talk_nietzsche": "Фрідріх Ніцше 🧠",
            "talk_hawking": "Стівен Гокінг 🔬",
        },
    )


async def talk_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    user_id = update.callback_query.from_user.id

    if query == "talk_end":
        chat_modes[user_id] = None
        current_person.pop(user_id, None)
        await start(update, context)
    elif query in personage:
        current_person[user_id] = query
        chat_gpt.set_prompt(load_prompt(query))
        await send_text_buttons(update,context,"Особистість обрана. Напишіть повідомлення.",
            {"talk_end": "Закінчити"},
        )
    await update.callback_query.answer()


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_modes[user_id] = "QUIZ_MODE"
    quiz_score[user_id] = 0
    quiz_waiting[user_id] = False
    quiz_topic.pop(user_id, None)

    await send_image(update, context, "quiz")
    await show_quiz_topics(update, context)


async def quiz_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    user_id = update.callback_query.from_user.id

    if query == "quiz_end":
        chat_modes[user_id] = None
        clear_quiz_state(user_id)
        await start(update, context)
    elif query == "quiz_change":
        # quiz_waiting[user_id] = False
        await show_quiz_topics(update, context)
    elif query == "quiz_more":
        await send_quiz_more_question(update, context, user_id)
    elif query in QUIZ_TOPICS:
        await send_quiz_question(update, context, user_id, query)

    await update.callback_query.answer()


async def random_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data

    if query == "random_end":
        await start(update, context)
    elif query == "random_more":
        await random(update, context)

    await update.callback_query.answer()


async def gpt_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    user_id = update.callback_query.from_user.id

    if query == "gpt_end":
        chat_modes[user_id] = None
        await start(update, context)

    await update.callback_query.answer()


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    mode = chat_modes.get(user_id)
    text = update.message.text

    if mode == "GPT_MODE":
        response = await chat_gpt.add_message(text)
        await send_text_buttons(update,context,response,{"gpt_end": "Закінчити"})
    elif mode == "TALK_MODE":
        person = current_person.get(user_id)
        if person is None:
            await send_text(update, context, "Спочатку виберіть особистість.")
            return

        response = await chat_gpt.add_message(text)
        await send_text_buttons(update,context,response,{"talk_end": "Закінчити"})
    elif mode == "QUIZ_MODE":
         if not quiz_waiting.get(user_id):
            await send_text(update, context, "Оберіть тему квізу.")
            return

         response = await chat_gpt.add_message(text)
         quiz_waiting[user_id] = False

    if response.strip().startswith("Правильно"):
        quiz_score[user_id] = quiz_score.get(user_id, 0) + 1

        score = quiz_score.get(user_id, 0)
        result_text = f"{response}\n\nРахунок: {score}"

        await send_text_buttons(update, context, result_text, QUIZ_RESULT_BUTTONS)
    elif mode == "VOICE_MODE":
        await send_text(update,context,"Надішліть голосове повідомлення».")


chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник колбеку можна так:
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("random", random))
app.add_handler(CommandHandler("gpt", gpt))
app.add_handler(CommandHandler("talk", talk))
app.add_handler(CommandHandler("quiz", quiz))
app.add_handler(CommandHandler("voice", voice))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
app.add_handler(MessageHandler(filters.VOICE, voice_handler))
# Зареєструвати обробник колбеку можна так:
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern="^random_.*"))
app.add_handler(CallbackQueryHandler(gpt_buttons_handler, pattern="^gpt_.*"))
app.add_handler(CallbackQueryHandler(talk_buttons_handler, pattern="^talk_.*"))
app.add_handler(CallbackQueryHandler(quiz_buttons_handler, pattern="^quiz_.*"))
app.add_handler(CallbackQueryHandler(voice_buttons_handler, pattern="^voice_.*"))
app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()
