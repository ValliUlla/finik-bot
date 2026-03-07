import os
import logging
import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_TOKEN")

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHAT_POPUTCHIKI = int(os.getenv("CHAT_POPUTCHIKI"))
CHAT_COURIERS = int(os.getenv("CHAT_COURIERS"))

CHANNEL_LINK = "https://t.me/+REqFc1k8aEc1MGQy"

ALLOWED_CHATS = {CHAT_POPUTCHIKI, CHAT_COURIERS}


async def delete_later(message, delay=15):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user = update.effective_user
    chat = update.effective_chat

    if chat.id not in ALLOWED_CHATS:
        return

    try:

        # ПРОВЕРКА: если админ — ничего не делаем
        chat_member = await context.bot.get_chat_member(chat.id, user.id)

        if chat_member.status in ["administrator", "creator"]:
            return

        # ПРОВЕРКА ПОДПИСКИ НА КАНАЛ
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)

        if member.status not in ["left", "kicked"]:
            return

        # НЕ ПОДПИСАН → удаляем сообщение
        await context.bot.delete_message(
            chat_id=chat.id,
            message_id=update.message.message_id
        )

        mention = user.mention_html()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Подписаться на канал", url=CHANNEL_LINK)]
        ])

        msg = await context.bot.send_message(
            chat_id=chat.id,
            text=f"{mention}, чтобы писать в этом чате подпишитесь на канал.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        asyncio.create_task(delete_later(msg))

    except Exception as e:
        logging.error(e)


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            check_subscription
        )
    )

    print("BOT STARTED")

    app.run_polling()


if __name__ == "__main__":
    main()
