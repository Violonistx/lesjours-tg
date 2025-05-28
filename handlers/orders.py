from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
import datetime

async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data['api']
    user_id = str(update.effective_user.id)
    token = api.tokens.get(user_id)
    if not token:
        await update.message.reply_text('Ошибка авторизации! Пожалуйста, нажмите /start для повторной авторизации.')
        return
    try:
        data = api.list_orders(user_id)
        if isinstance(data, list):
            orders = data
        else:
            orders = data.get('results', data)
        if not orders:
            await update.message.reply_text('У вас пока нет заказов.')
            return
        text = 'Ваши заказы:\n'
        buttons = []
        for order in orders:
            order_id = order.get('id', '?')
            number = order.get('number', f"{order_id}")
            date = order.get('formatted_date', '')
            # Форматируем дату, если она в ISO
            if not date and order.get('created_at'):
                try:
                    dt = datetime.datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                    date = dt.strftime('%d.%m.%y')
                except Exception:
                    date = order.get('created_at', '')
            final_amount = order.get('final_amount') or order.get('total_amount') or ''
            status = order.get('status', 'статус неизвестен')
            if status == 'created':
                status = 'Оформлен'
            text += f"\n№{number} | {date} | {final_amount} ₽ | {status}"
            buttons.append([InlineKeyboardButton(f"Подробнее №{number}", callback_data=f"order:detail:{order_id}")])
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        if 'Требуется авторизация' in str(e):
            await update.message.reply_text('Ошибка авторизации! Пожалуйста, нажмите /start для повторной авторизации.')
            return
        if 'Не удалось определить внутренний user_id' in str(e):
            await update.message.reply_text('Ошибка: не удалось определить пользователя. Попробуйте /start.')
            return
        await update.message.reply_text(f'Ошибка при получении заказов: {e}')

async def order_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    order_id = int(query.data.split(':')[2])
    api = context.bot_data['api']
    user_id = str(query.from_user.id)
    data = api.list_orders(user_id)
    if isinstance(data, list):
        orders = data
    else:
        orders = data.get('results', data)
    order = next((o for o in orders if o.get('id') == order_id), None)
    if not order:
        await query.answer('Заказ не найден')
        return
    number = order.get('number', f"{order_id}")
    date = order.get('formatted_date', '')
    final_amount = order.get('final_amount') or order.get('total_amount') or ''
    status = order.get('status', 'статус неизвестен')
    if status == 'created':
        status = 'Оформлен'
    text = f"<b>Заказ №{number}</b>\nДата заказа: {date}\nСтатус: {status}\nСумма: {final_amount} ₽\n"
    # Позиции заказа
    units = order.get('order_units', [])
    for unit in units:
        if unit.get('type') == 'master_class':
            name = unit.get('name', 'Мастер-класс')
            guests = unit.get('guestsAmount', 1)
            total = unit.get('totalPrice', '')
            dt = unit.get('date', {})
            dt_str = ''
            if dt:
                start = dt.get('start_datetime')
                end = dt.get('end_datetime')
                if start and end:
                    try:
                        dt_start = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                        dt_end = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                        dt_str = f"\nДата: {dt_start.strftime('%d.%m.%Y')} с {dt_start.strftime('%H:%M')} до {dt_end.strftime('%H:%M')}"
                    except Exception:
                        dt_str = f"\nДата: {start} - {end}"
            address = unit.get('address', '')
            text += f"\n<b>Мастер-класс:</b> {name}\nГостей: {guests}\nСтоимость: {total} ₽{dt_str}\nАдрес: {address}\n"
        elif unit.get('type') == 'certificate':
            amount = unit.get('amount', '')
            text += f"\n<b>Сертификат:</b> на сумму {amount} ₽\n"
    sale = order.get('total_sale')
    if sale:
        text += f"\nСкидка: {sale} ₽"
    await query.message.reply_text(text, parse_mode='HTML')
    await query.answer()
