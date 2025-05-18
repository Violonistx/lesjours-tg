from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from services.api_client import LesJoursAPI
import config

api = LesJoursAPI(config.API_BASE_URL)

def list_masterclasses(update: Update, context: CallbackContext):
    page = int(context.args[0]) if context.args else 1
    data = api.list_masterclasses(page=page, page_size=5)

    buttons = [
        [InlineKeyboardButton(item['title'], callback_data=f'mc:show:{item["id"]}')]
        for item in data['results']
    ]

    nav = []
    if data.get('previous'):
        nav.append(InlineKeyboardButton('‹ Назад', callback_data=f'mc:page:{page-1}'))
    if data.get('next'):
        nav.append(InlineKeyboardButton('Вперёд ›', callback_data=f'mc:page:{page+1}'))
    if nav:
        buttons.append(nav)

    update.message.reply_text(
        'Список мастер-классов:',
        reply_markup=InlineKeyboardMarkup(buttons)
    )

def masterclass_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    _, action, value = query.data.split(':', 2)

    if action == 'page':
        context.args = [value]
        list_masterclasses(update, context)
        return

    mc_id = int(value)

    if action == 'show':
        mc = api.get_masterclass(mc_id)
        text = f"*{mc['title']}*\n\n{mc['description'][:500]}..."
        button = InlineKeyboardButton('Записаться', callback_data=f'mc:book:{mc_id}')
        query.answer()
        query.edit_message_text(
            text, parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[button]])
        )
        return

    if action == 'book':
        order = api.book_masterclass(mc_id, {})
        query.answer('Вы записаны!')
        query.edit_message_text(
            f"Вы записались на *{order['masterclass_title']}*",
            parse_mode='Markdown'
        )

classes_handler = CommandHandler('classes', list_masterclasses)
