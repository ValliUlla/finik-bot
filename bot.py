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

CHANNEL_ID_1 = int(os.getenv("CHANNEL_ID"))
CHANNEL_ID_2 = -1001910164289

CHAT_POPUTCHIKI = int(os.getenv("CHAT_POPUTCHIKI"))
CHAT_COURIERS = int(os.getenv("CHAT_COURIERS"))

CHANNEL_LINK_1 = "https://t.me/+GB5IKixNa8pmMzUy"
CHANNEL_LINK_2 = "https://t.me/+eTbePnqsrdIwZDgy"

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
    message = update.message

    if chat.id not in ALLOWED_CHATS:
        return

    try:
        # Игнор сообщений от имени группы / анонимных админов
        if message.sender_chat is not None:
            return

        if user is None:
            return

        # Игнор админов и создателя чата
        chat_member = await context.bot.get_chat_member(chat.id, user.id)
        if chat_member.status in ["administrator", "creator"]:
            return

        # Проверка подписки на оба канала
        member1 = await context.bot.get_chat_member(CHANNEL_ID_1, user.id)
        member2 = await context.bot.get_chat_member(CHANNEL_ID_2, user.id)

        subscribed_1 = member1.status not in ["left", "kicked"]
        subscribed_2 = member2.status not in ["left", "kicked"]

        # Если подписан на оба — ничего не делаем
        if subscribed_1 and subscribed_2:
            return

        # Удаляем сообщение неподписанного
        await context.bot.delete_message(
            chat_id=chat.id,
            message_id=message.message_id
        )

        mention = user.mention_html()
        buttons = []

        if not subscribed_1:
            buttons.append([
                InlineKeyboardButton("Подписаться на РАБОТА KSA", url=CHANNEL_LINK_1)
            ])

        if not subscribed_2:
            buttons.append([
                InlineKeyboardButton("Подписаться на чат Курьеры", url=CHANNEL_LINK_2)
            ])

        keyboard = InlineKeyboardMarkup(buttons)

        msg = await context.bot.send_message(
            chat_id=chat.id,
            text=f"{mention}, чтобы писать в этом чате подпишитесь на обязательные каналы.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        asyncio.create_task(delete_later(msg))

    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")


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
