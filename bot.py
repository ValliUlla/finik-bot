import os
import logging
import asyncio
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
    CallbackQueryHandler,
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

# защита от спама
muted_users = {}


async def delete_later(message, delay=20):
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
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)

        if member.status in ["left", "kicked"]:

            # если уже мутнут — просто удаляем сообщение
            if user.id in muted_users:
                await context.bot.delete_message(chat.id, update.message.message_id)
                return

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

            muted_users[user.id] = True

            mention = user.mention_html()

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Подписаться", url=CHANNEL_LINK)],
                [InlineKeyboardButton("Я подписался", callback_data="check_sub")]
            ])

            msg = await context.bot.send_message(
                chat_id=chat.id,
                text=f"{mention}, подпишитесь на канал чтобы писать в чате.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )

            asyncio.create_task(delete_later(msg))

    except Exception as e:
        logging.error(e)


async def check_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user = query.from_user
    chat = query.message.chat

    await query.answer()

    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)

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

            if user.id in muted_users:
                del muted_users[user.id]

            msg = await context.bot.send_message(
                chat_id=chat.id,
                text=f"{user.mention_html()} теперь может писать.",
                parse_mode="HTML"
            )

            asyncio.create_task(delete_later(msg))

            try:
                await query.message.delete()
            except:
                pass

        else:

            await query.answer(
                "Вы ещё не подписались на канал",
                show_alert=True
            )

    except Exception as e:
        logging.error(e)


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_subscription
        )
    )

    app.add_handler(
        CallbackQueryHandler(check_button)
    )

    print("BOT STARTED")

    app.run_polling()


if __name__ == "__main__":
    main()
