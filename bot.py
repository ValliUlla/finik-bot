import os
import logging
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions
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


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user = update.effective_user
    chat = update.effective_chat

    if chat.id not in ALLOWED_CHATS:
        return

    try:

        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)

        # ЕСЛИ ПОДПИСАН → снимаем мут
        if member.status not in ["left", "kicked"]:

            await context.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )

            return

        # ЕСЛИ НЕ ПОДПИСАН

        await context.bot.delete_message(
            chat_id=chat.id,
            message_id=update.message.message_id
        )

        mute_until = datetime.utcnow() + timedelta(days=3)

        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=mute_until
        )

        mention = user.mention_html()

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Подписаться", url=CHANNEL_LINK)]
        ])

        await context.bot.send_message(
            chat_id=chat.id,
            text=f"{mention}, чтобы писать в этом чате подпишитесь на канал.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

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
