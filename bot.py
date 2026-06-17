from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons)

import credentials

chat_modes = {}



# 1. *"Випадковий факт"*
# Телеграм-бот повинен обробляти команду /random.
# При обробці команди він надсилає заздалегідь підготовлене зображення
# та робить запит до ChatGPT із заздалегідь підготовленим промптом.
# Відповідь ChatGPT потрібно отримати та передати користувачеві.
# До повідомлення має бути прикріплена кнопка "Закінчити", натискання на яку
# працює так само, як команда /start.
# І кнопка "Хочу ще факт", натискання на яку
# працює так само, як команда /random




async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
   # chat_modes[update.message.from_user.id] = "DEFAULT_MODE"
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓'
        # Додати команду в меню можна так:
        # 'command': 'button text'

    })

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_modes[update.message.callback_query.from_user.id] = "RANDOM_MODE"
    prompt = load_prompt('random')
    response = await chat_gpt.send_question(prompt,"Give random facts")
    await send_image(update, context, 'random')
    ##await send_text(update, context, response)
    await send_text_buttons(update,context,response,{
        "random_end":"End",
        "random_more":"Wanna more facts,"
    })

async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_modes[update.message.from_user.id]="GPT_MODE"
    await send_image(update, context, 'gpt')
    await send_text(update, context, load_message('gpt'))
    # await send_text_buttons(update, context, response, {
    #     "gpt_end": "Stop to Chat",

    # })

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode=chat_modes.get(update.message.from_user.id)
    if mode is None:
        await send_text(update, context, " What a command you used? Press /start command please")
    elif mode == "GPT_MODE":
        pt = load_prompt('gpt')
        response = await chat_gpt.send_question(pt,update.message.text)
             await send_text_buttons(update, context, response, {
            "gpt_end": "Stop to Chat",
        })

async def gpt_buttons_handler(update: Update, context):
    query = update.callback_query.data
    if query == "gpt_end":
        chat_modes[update.callback_query.from_user.id] = "None"
        await start(update, context)




async def buttons_handler(update: Update, context):
    query = update.callback_query.data
    if query == "random_end":
        #chat_modes[update.message.from_user.id] = "DEFAULT_MODE"
        await start(update, context)





chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

#Обробники команд:
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', gpt))
app.add_handler(MessageHandler(None, text_handler))

#Обробники колбеку:
app.add_handler(CallbackQueryHandler(buttons_handler, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(gpt_buttons_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()
