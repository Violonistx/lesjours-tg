from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
import logging
import config

def get_main_menu():
    return ReplyKeyboardMarkup([
        ['📋 Мастер-классы', '🎁 Сертификаты'],
        ['ℹ️ О нас', '❌ Отмена бронирования']
    ], resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data['api']
    user = update.effective_user
    try:
        api.ensure_auth(user.id, user.first_name or '', user.last_name or '')
        await update.message.reply_text(
            f"Привет, {user.first_name or 'гость'}!\n\n"
            "Я помогу вам выбрать и забронировать мастер-класс, а также приобрести сертификат.\n"
            "Пользуйтесь кнопками ниже!",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        await update.message.reply_text(
            "Ошибка авторизации/регистрации. Попробуйте позже или обратитесь к администратору."
        )

async def logout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "В этом боте авторизация не требуется. Просто пользуйтесь функционалом!",
        reply_markup=get_main_menu()
    )

# Обработка нажатий на кнопки главного меню

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    logging.info(f"Пользователь нажал: {text}")  # Для отладки
    if text == '📋 Мастер-классы':
        from handlers.masterclasses import list_masterclasses
        return await list_masterclasses(update, context)
    elif text == '🎁 Сертификаты':
        from handlers.certificates import list_certificates
        return await list_certificates(update, context)
    elif text == 'ℹ️ О нас':
        from handlers.profile import about_command
        return await about_command(update, context)
    elif text == '❌ Отмена бронирования':
        await update.message.reply_text(
            'Для отмены бронирования напишите нашему менеджеру: @les_jour_mk',
            reply_markup=get_main_menu()
        )
    else:
        await update.message.reply_text(
            f'Пожалуйста, используйте кнопки меню ниже. (Вы отправили: {text})',
            reply_markup=get_main_menu()
        )

start_handler = CommandHandler('start', start_command)
logout_handler = CommandHandler('logout', logout_handler)
menu_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), menu_handler)
