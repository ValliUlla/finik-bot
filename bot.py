import os
import logging
from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHAT_POPUTCHIKI = int(os.getenv("CHAT_POPUTCHIKI"))
CHAT_COURIERS = int(os.getenv("CHAT_COURIERS"))

ALLOWED_CHATS = {CHAT_POPUTCHIKI, CHAT_COURIERS}


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    chat = update.effective_chat

    if chat.id not in ALLOWED_CHATS:
        return

    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
        status = member.status

        if status in ["left", "kicked"]:
            try:
                await context.bot.delete_message(
                    chat_id=chat.id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                logging.error(f"Не удалось удалить сообщение: {e}")

            try:
                # мут пользователя
await context.bot.restrict_chat_member(
    chat_id=chat.id,
    user_id=user.id,
    permissions=ChatPermissions(can_send_messages=False)
)

# сообщение с ссылкой
await context.bot.send_message(
    chat_id=chat.id,
    text="Чтобы писать в этом чате, сначала подпишитесь на канал:https://t.me/visacenter_vKSA"
)
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение: {e}")

    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")


def main():
    if not TOKEN:
        raise ValueError("Переменная TELEGRAM_TOKEN не найдена")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_subscription
        )
    )

    logging.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
