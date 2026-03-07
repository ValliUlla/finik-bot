import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    chat = update.effective_chat

    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)

        if member.status in ["left", "kicked"]:
            try:
                await context.bot.delete_message(
                    chat_id=chat.id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                logging.error(e)

            await context.bot.send_message(
                chat_id=chat.id,
                text="Чтобы писать в этом чате, подпишитесь на канал Финик визовый центр."
            )

    except Exception as e:
        logging.error(e)

def main():
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN не найден")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_subscription
        )
    )

    app.run_polling()

if __name__ == "__main__":
    main()
