from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import config
import datetime
import requests
import traceback

user_booking = {}
events_cache = {}
all_mcs_cache = {}

def format_event_date(dt_str):
    try:
        dt = datetime.datetime.fromisoformat(dt_str)
        return dt.strftime('%d.%m.%Y %H:%M')
    except Exception:
        return dt_str

def get_masterclass_by_event_id(all_masterclasses, event_id):
    for mc in all_masterclasses.get('results', []):
        for event in mc.get('events', []):
            if event['id'] == event_id:
                return mc
    return None

def build_masterclass_dict(all_masterclasses):
    return {mc['id']: mc for mc in all_masterclasses.get('results', [])}

async def list_masterclasses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data['api']
    user_id = update.effective_user.id
    page = int(context.args[0]) if context.args else 1
    data = api.list_masterclasses(user_id=user_id, page=page, page_size=5)
    print('EVENTS DATA:', data)
    all_mcs = api.list_all_masterclasses(user_id)
    print('ALL MASTERCLASSES:', all_mcs)
    mc_dict = build_masterclass_dict(all_mcs)
    global all_mcs_cache
    all_mcs_cache[user_id] = mc_dict
    print('MC_DICT KEYS:', list(mc_dict.keys()))
    events = data.get('results', [])
    for event in events:
        events_cache[event['id']] = event
        print('EVENT:', event['id'], 'MC_ID:', event['masterclass'])
    buttons = []
    for event in events:
        mc = mc_dict.get(event['masterclass'])
        if mc:
            name = mc['name']
        else:
            name = f"Мастер-класс не найден (id: {event['masterclass']})"
        buttons.append([
            InlineKeyboardButton(f"{format_event_date(event['start_datetime'])} ({name})", callback_data=f"mc:show:{event['id']}")
        ])
    nav = []
    if data.get('previous'):
        nav.append(InlineKeyboardButton('‹ Назад', callback_data=f'mc:page:{page-1}'))
    if data.get('next'):
        nav.append(InlineKeyboardButton('Вперёд ›', callback_data=f'mc:page:{page+1}'))
    if nav:
        buttons.append(nav)
    if update.message:
        await update.message.reply_text(
            'Список ближайших событий (мастер-классов):',
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            'Список ближайших событий (мастер-классов):',
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    return

async def masterclass_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data['api']
    query = update.callback_query
    user_id = query.from_user.id
    _, action, value = query.data.split(':', 2)

    if action == 'page':
        context.args = [value]
        return await list_masterclasses(update, context)

    event_id = int(value)

    if action == 'show':
        event = events_cache.get(event_id)
        if not event:
            await query.answer('Событие не найдено')
            return
        global all_mcs_cache
        mc_dict = all_mcs_cache.get(user_id)
        mc = mc_dict.get(event['masterclass']) if mc_dict else None
        if not mc:
            await query.answer(f'Мастер-класс не найден (id: {event["masterclass"]})')
            return
        text = (
            f"<b>{mc.get('name', 'Без названия')}</b>\n"
            f"Дата: {format_event_date(event['start_datetime'])}\n"
            f"Свободных мест: {event['available_seats']}\n"
            f"\n{mc.get('short_description', '')}"
        )
        button = InlineKeyboardButton('Записаться', callback_data=f'mc:book:{event_id}')
        await query.answer()
        # Отправляем фото, если есть
        photo_url = None
        bucket = mc.get('bucket_link')
        if bucket and isinstance(bucket, list) and bucket[0].get('url'):
            photo_url = bucket[0]['url']
        if photo_url:
            await query.message.reply_photo(photo_url, caption=text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[button]]))
            await query.delete_message()
        else:
            await query.edit_message_text(
                text, parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[button]])
            )
        return

    if action == 'book':
        # Сохраняем id мастер-класса для пользователя
        user_booking[user_id] = event_id
        # Запрашиваем телефон через кнопку Telegram
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton('Отправить номер телефона', request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await query.message.reply_text(
            'Пожалуйста, отправьте свой номер телефона для бронирования:',
            reply_markup=reply_markup
        )
        await query.answer()
        return

classes_handler = CommandHandler('classes', list_masterclasses)

async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data['api']
    user = update.effective_user
    contact = update.message.contact
    if not contact or contact.user_id != user.id:
        await update.message.reply_text('Пожалуйста, используйте кнопку для отправки своего номера телефона.')
        return
    user_id = user.id
    event_id = user_booking.pop(user_id, None)
    if not event_id:
        await update.message.reply_text('Не удалось определить мастер-класс для бронирования. Попробуйте ещё раз.')
        return
    # Получаем внутренний user_id из API
    api_user_id = api.get_api_user_id(user_id)
    if not api_user_id:
        await update.message.reply_text('Ошибка: не удалось определить пользователя на сервере. Попробуйте /start.')
        return
    # Отправляем данные в API
    try:
        api.add_to_cart(user_id, api_user_id, event_id, guests_amount=1)
        # Чекаут: передаём данные пользователя
        checkout_data = {
            'phone': contact.phone_number,
            'telegram_id': user_id,
            'telegram_username': user.username or ''
        }
        api.checkout(user_id, api_user_id, checkout_data)
        await update.message.reply_text(
            "Вы успешно записались на мастер-класс! Заказ оформлен, с вами свяжется менеджер для подтверждения.\n\nЕсли возникли вопросы, напишите нашему менеджеру: @les_jour_mk",
            reply_markup=ReplyKeyboardMarkup([
                ['В главное меню']
            ], resize_keyboard=True)
        )
    except Exception as e:
        tb = traceback.format_exc()
        err_text = ''
        if isinstance(e, requests.HTTPError) and hasattr(e, 'response'):
            err_text = e.response.text
            await update.message.reply_text(f'Ошибка при бронировании (HTTP): {e.response.status_code}\n{err_text}')
        else:
            err_text = str(e)
            await update.message.reply_text(f'Ошибка при бронировании (Exception): {err_text}')
        # Отправим traceback отдельным сообщением (для отладки)
        await update.message.reply_text(f'Traceback:\n{tb}')

phone_handler = MessageHandler(filters.CONTACT, phone_handler)
