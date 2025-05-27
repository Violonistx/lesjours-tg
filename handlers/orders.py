from telegram import Update
from telegram.ext import ContextTypes

async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data['api']
    user_id = str(update.effective_user.id)
    token = api.tokens.get(user_id)
    if not token:
        await update.message.reply_text('Ошибка авторизации! Пожалуйста, нажмите /start для повторной авторизации.')
        return
    api_user_id = api.get_api_user_id(user_id)
    if not api_user_id:
        await update.message.reply_text('Ошибка: не удалось определить пользователя. Попробуйте /start.')
        return
    try:
        data = api.list_orders(user_id)
        orders = data.get('results', data)
        if not orders:
            await update.message.reply_text('У вас пока нет заказов.')
            return
        text = 'Ваши заказы:\n'
        for order in orders:
            text += f"\nЗаказ №{order.get('id', '?')}: {order.get('status', 'статус неизвестен')}\n"
        await update.message.reply_text(text)
    except Exception as e:
        if 'Требуется авторизация' in str(e):
            await update.message.reply_text('Ошибка авторизации! Пожалуйста, нажмите /start для повторной авторизации.')
            return
        await update.message.reply_text(f'Ошибка при получении заказов: {e}')
