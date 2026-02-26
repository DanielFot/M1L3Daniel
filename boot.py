import telebot
from config import token
import re
from datetime import datetime

bot = telebot.TeleBot(token)

BANNED_USERS_FILE = "banned_users.txt"


def save_banned_user(user, message_text):
    """
    Saves banned user information into a text file safely.
    """
    try:
        with open(BANNED_USERS_FILE, "a", encoding="utf-8") as file:
            file.write(
                f"Time: {datetime.now()}\n"
                f"User ID: {user.id}\n"
                f"Username: @{user.username}\n"
                f"First Name: {user.first_name}\n"
                f"Last Name: {user.last_name}\n"
                f"Message: {message_text}\n"
                f"{'-'*40}\n"
            )
    except Exception as e:
        print(f"Error saving banned user: {e}")


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я бот для управления чатом.")


@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.reply_to_message:
        chat_id = message.chat.id
        user_id = message.reply_to_message.from_user.id

        try:
            user_status = bot.get_chat_member(chat_id, user_id).status
        except Exception as e:
            bot.reply_to(message, f"Ошибка при получении статуса пользователя: {e}")
            return

        if user_status in ['administrator', 'creator']:
            bot.reply_to(message, "Невозможно забанить администратора.")
        else:
            try:
                bot.ban_chat_member(chat_id, user_id)
                bot.reply_to(
                    message,
                    f"Пользователь @{message.reply_to_message.from_user.username} был забанен."
                )
            except Exception as e:
                bot.reply_to(message, f"Ошибка при бане пользователя: {e}")
    else:
        bot.reply_to(
            message,
            "Эта команда должна быть использована в ответ на сообщение пользователя."
        )


@bot.message_handler(func=lambda message: True, content_types=['text'])
def auto_moderation(message):
    """
    Automatically bans users if their message contains a link.
    """
    if not message.text:
        return

    chat_id = message.chat.id
    user = message.from_user

    # Check for links (https:// or http:// or www.)
    if re.search(r"(https?://|www\.)", message.text, re.IGNORECASE):
        try:
            user_status = bot.get_chat_member(chat_id, user.id).status

            if user_status in ['administrator', 'creator']:
                return  # Do not ban admins

            # Save user info before banning
            save_banned_user(user, message.text)

            bot.ban_chat_member(chat_id, user.id)
            bot.send_message(
                chat_id,
                f"Пользователь @{user.username} был автоматически забанен за отправку ссылки."
            )

        except Exception as e:
            print(f"Auto moderation error: {e}")


if __name__ == "__main__":
    try:
        bot.infinity_polling(none_stop=True)
    except Exception as e:
        print(f"Bot polling error: {e}")

