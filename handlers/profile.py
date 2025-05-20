from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

ABOUT_TEXT = (
    "🎨 <b>О нас</b>\n\n"
    "Творческая студия Les Jours была создана в 2024 году как пространство для людей, желающих прикоснуться к творчеству.\n\n"
    "Мы поддерживаем каждого в стремлении познать новое и раскрыть свой потенциал под руководством профессиональных мастеров. Здесь вы забываете о делах и просто наслаждаетесь процессом — создаёте что-то красивое и уникальное.\n\n"
    "Это не только про творчество, но и про состояние души: когда внутри становится легче, спокойнее и теплее…\n\n"
    "Приходите к нам, чтобы почувствовать эту магию на себе! Мы уверены, вы уйдёте с улыбкой, творческой искрой и ощущением, что мир стал чуть лучше!\n\n"
    "📱 По всем вопросам:\n"
    "Telegram: @les_jour_mk\n"
    "WhatsApp: +7 983 285-83-99\n\n"
    "Мы в соцсетях:\n"
    "Telegram: @les_jour"
)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ABOUT_TEXT, parse_mode='HTML')

about_handler = CommandHandler('about', about_command)
