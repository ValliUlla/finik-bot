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

CHAT_POPUTCHIKI = int(os.getenv("CHAT_POPUTCHIKI"))
CHAT_COURIERS = int(os.getenv("CHAT_COURIERS"))

CHANNEL_WORK = {
    "id": -1002002128681,
    "name": "РАБОТА KSA",
    "link": "https://t.me/+GB5IKixNa8pmMzUy"
}

CHANNEL_COURIERS = {
    "id": -1002026737566,
    "name": "чат Курьеры",
    "link": "https://t.me/+eTbePnqsrdIwZDgy"
}

# Чтобы не плодить кучу сообщений бота одному и тому же человеку
last_bot_messages = {}


async def delete_later(message, delay=15):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


def get_required_channels(chat_id):
    if chat_id == CHAT_POPUTCHIKI:
        return [CHANNEL_WORK, CHANNEL_COURIERS]

    if chat_id == CHAT_COURIERS:
        return [CHANNEL_WORK]

    return []


def build_buttons(missing_channels):
    buttons = []

    for channel in missing_channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"Подписаться на {channel['name']}",
                url=channel["link"]
            )
        ])

    return InlineKeyboardMarkup(buttons)


def build_text(mention, missing_channels):
    names = [channel["name"] for channel in missing_channels]

    if len(names) == 1:
        return f"{mention}, чтобы писать в этом чате подпишитесь на {names[0]}."

    if len(names) == 2:
        return f"{mention}, чтобы писать в этом чате подпишитесь на {names[0]} и {names[1]}."

    joined = ", ".join(names[:-1]) + f" и {names[-1]}"
    return f"{mention}, чтобы писать в этом чате подпишитесь на {joined}."


async def get_missing_channels(user_id, bot, required_channels):
    missing_channels = []

    for channel in required_channels:
        member = await bot.get_chat_member(channel["id"], user_id)
        status = member.status

        if status in ["left", "kicked"]:
            missing_channels.append(channel)

    return missing_channels


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    message = update.message
    chat = update.effective_chat
    user = update.effective_user

    if chat.id not in {CHAT_POPUTCHIKI, CHAT_COURIERS}:
        return

    try:
        # Игнор сообщений от имени группы / анонимных админов
        if message.sender_chat is not None:
            return

        if user is None:
            return

        # Игнор админов и владельца чата
        group_member = await context.bot.get_chat_member(chat.id, user.id)
        if group_member.status in ["administrator", "creator"]:
            return

        required_channels = get_required_channels(chat.id)
        missing_channels = await get_missing_channels(user.id, context.bot, required_channels)

        # Если все условия выполнены — ничего не делаем
        if not missing_channels:
            return

        # Удаляем сообщение пользователя
        await context.bot.delete_message(
            chat_id=chat.id,
            message_id=message.message_id
        )

        # Удаляем старое предупреждение бота этому пользователю, если было
        old_message_id = last_bot_messages.get((chat.id, user.id))
        if old_message_id:
            try:
                await context.bot.delete_message(chat_id=chat.id, message_id=old_message_id)
            except Exception:
                pass

        mention = user.mention_html()
        keyboard = build_buttons(missing_channels)
        text = build_text(mention, missing_channels)

        bot_message = await context.bot.send_message(
            chat_id=chat.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        last_bot_messages[(chat.id, user.id)] = bot_message.message_id

        asyncio.create_task(delete_later(bot_message))

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
