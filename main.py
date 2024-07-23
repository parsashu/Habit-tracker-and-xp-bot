import telebot, time, threading, schedule
from telebot import types
from telebot.types import Message
from telebot.util import update_types
from habit_tracker import habit_tracker, streak_leaderboard, habit_button_logic
from database_functions import execute
from xp import (
    add_xp, xp_leaderboard, check_king_of_the_hill
    , add_xp_command,remove_xp_command, overview_command,
    update_leaderboard_history
        )
from ids import CHAT_ID,ANNOUNCEMENT_THREAD_ID, PROBLEMS_THREAD_ID, XP_GENERATOR_THREADS, HABITS, TOKEN


bot = telebot.TeleBot(TOKEN)
#updates = bot.get_updates()


def is_user_admin(user_id, chat_id):
    user = bot.get_chat_member(chat_id, user_id)
    try:
        return user.status in ["administrator", "creator"]

    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False
    

# Challenge logic
user_data = {}

def new_challenge(message):
    execute("DELETE FROM challenges")
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "لطفاً متن چالش را وارد کنید:")
    bot.register_next_step_handler(msg, process_challenge_text)

def process_challenge_text(message):
    if message.chat.type == 'private':
        chat_id = message.chat.id
        challenge_text = message.text
        user_data['challenge_text'] = challenge_text
        msg = bot.send_message(chat_id, "لطفاً مقدار ایکس پی را وارد کنید:")
        bot.register_next_step_handler(msg, process_xp)

def process_xp(message):
    if message.chat.type == 'private':
        chat_id = message.chat.id
        xp = message.text
        if xp.isdigit():
            user_data['xp'] = xp
            msg = bot.send_message(chat_id, "لطفاً مدت زمان (به ساعت) را وارد کنید:")
            bot.register_next_step_handler(msg, process_duration)
        else:
            bot.send_message(chat_id, "لطفاً یک عدد معتبر وارد کنید.")
            bot.register_next_step_handler(message, process_xp)

def process_duration(message):
    if message.chat.type == 'private':
        chat_id = message.chat.id
        duration = message.text
        if duration.isdigit():
            user_data['duration'] = duration

            challenge_text = user_data['challenge_text']
            xp = user_data['xp']
            duration = user_data['duration']

            # درج چالش جدید در دیتابیس
            execute(f"""
                    INSERT INTO challenges (chat_id, challenge_text, xp, duration) 
                    VALUES ({chat_id}, '{challenge_text}', {xp}, {duration})
                            """)

            # نمایش چالش جدید با لیست کاربران انجام دهنده
            show_challenge_with_users(challenge_text, xp, duration, [])
        else:
            bot.send_message(chat_id, "لطفاً یک عدد معتبر وارد کنید.")
            bot.register_next_step_handler(message, process_duration)

def show_challenge_with_users(challenge_text, xp, duration, users):
    markup = types.InlineKeyboardMarkup()
    btn_done = types.InlineKeyboardButton('انجام دادم!', callback_data=f'done{xp}')
    markup.add(btn_done)

    users_list = "\n".join([f"- {user[0]} ({user[1]})" for user in users])
    text = (
        f"📢 <b>چالش جدید</b>\n\n"
        f"<blockquote>📝 <b>متن: </b>{challenge_text}\n\n"
        f"🏆 <b>اکسپی:</b> {xp}\n\n"
        f"⏳ <b>مدت زمان:</b> {duration} ساعت\n\n</blockquote>"
        f"📋 <b>لیست کاربران:</b>\n{users_list}"
    )
    bot.send_message(CHAT_ID,
                     text,
                     parse_mode='HTML',
                     reply_markup=markup,
                     message_thread_id=ANNOUNCEMENT_THREAD_ID)


# CHAT COMMANDS-------------------------------------------------------------------------------------------------------------------
@bot.message_handler(func=lambda message: True)
def handle_messages(message: Message):
    user_id = message.from_user.id 

    if '/start' in message.text and message.chat.id != CHAT_ID:
        if message.chat.type == 'private':
            bot.send_message(message.chat.id, 
                            "درود بر شما. خوش آمدید به ربات پارس پروگرس. امیدواریم از خدمات ما رضایت داشته باشید.")

    if '/help' in message.text and message.chat.id != CHAT_ID:
        if message.chat.type == 'private':
            bot.send_message(message.chat.id,
                            "برای پیوستن به گروه خودسازی، لطفاً به لینک زیر مراجعه فرمایید:\n\nhttps://t.me/selfimprovementir/1")

    if '/admin' in message.text and message.chat.id != CHAT_ID:
        if message.chat.type == 'private':
            bot.send_message(message.chat.id, 
                            "جهت ارتباط با سازندگان ربات، می‌توانید با @itisario و @parsashu تماس حاصل فرمایید.")

    if '/overview' in message.text:
        overview_command(message)
         
    # َAdmin commands------------------
    if '/add_xp' in message.text:
        if is_user_admin(user_id, CHAT_ID):
            add_xp_command(message)
        else:
            bot.send_message(
                CHAT_ID, 
                "شما اجازه استفاده از این دستور را ندارید!",
                message_thread_id=message.message_thread_id
            )

    if '/remove_xp' in message.text:
        if is_user_admin(user_id, CHAT_ID):
            remove_xp_command(message)
        else:
            bot.send_message(
                CHAT_ID, 
                "شما اجازه استفاده از این دستور را ندارید!",
                message_thread_id=message.message_thread_id
            )


    if '/challenge' in message.text:
        if message.chat.type == 'private':
            if is_user_admin(user_id, CHAT_ID):
                new_challenge(message)
            else:
                bot.send_message(
                    CHAT_ID, 
                    "شما اجازه استفاده از این دستور را ندارید!",
                    message_thread_id=message.message_thread_id
                )

    if '/poll' in message.text:
        if is_user_admin(user_id, CHAT_ID):
            habit_tracker()
        else:
            bot.send_message(
                CHAT_ID, 
                "شما اجازه استفاده از این دستور را ندارید!",
                message_thread_id=message.message_thread_id
            )

    if '/streak_board' in message.text:
        if is_user_admin(user_id, CHAT_ID):
            streak_leaderboard()
        else:
            bot.send_message(
                CHAT_ID, 
                "شما اجازه استفاده از این دستور را ندارید!",
                message_thread_id=message.message_thread_id
            )

    if '/xp_board' in message.text:
        if is_user_admin(user_id, CHAT_ID):
            xp_leaderboard()
        else:
            bot.send_message(
                CHAT_ID, 
                "شما اجازه استفاده از این دستور را ندارید!",
                message_thread_id=message.message_thread_id
            )

    if '/check_king' in message.text:
        if is_user_admin(user_id, CHAT_ID):
            check_king_of_the_hill()  
        else:
            bot.send_message(
                CHAT_ID, 
                "شما اجازه استفاده از این دستور را ندارید!",
                message_thread_id=message.message_thread_id
            )

    if '/id' in message.text:
        if is_user_admin(user_id, message.chat.id): 
            chat_id = message.chat.id
            thread_id = message.message_thread_id if hasattr(message, 'message_thread_id') else None
            bot.send_message(chat_id=chat_id, text=f'Chat ID: {chat_id}\nThread ID: {thread_id}', message_thread_id=thread_id)
        else:
            bot.send_message(
                chat_id, 
                "شما اجازه استفاده از این دستور را ندارید!",
                message_thread_id=message.message_thread_id
            )

    # Add xp to problems and solutions----------------------
    if '#solution' in message.text.lower() or '#راهکار' in message.text:
        if message.chat.id == CHAT_ID and message.reply_to_message and message.reply_to_message.message_id == PROBLEMS_THREAD_ID:
            add_xp(message.from_user.username, 5, 'answering a problem')

    if '#problem' in message.text.lower() or '#دشواری' in message.text:
        if message.chat.id == CHAT_ID and message.reply_to_message and message.reply_to_message.message_id == PROBLEMS_THREAD_ID:
            add_xp(message.from_user.username, 10, 'asking a problem')

    # Add xp to message in xp channels----------------------
    if message.message_thread_id in XP_GENERATOR_THREADS:
        thread_id_ = message.message_thread_id
        username_ = message.from_user.username
        xp = XP_GENERATOR_THREADS[thread_id_]
        reason = f'sending message on thread: {thread_id_}'
        add_xp(username_, xp, reason)    

# Buttons------------------------------------------------------------------------------------------------------------------------
 # Habit tracker button
@bot.callback_query_handler(func=lambda call: call.data in HABITS)
def callback_habit_tracker(call):
    habit_button_logic(call)

# Challenge button
@bot.callback_query_handler(func=lambda call: call.data.startswith('done'))
def challenge_button_logic(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    xp = int(call.data[4:])

    # Fetch the user's challenge record
    record = execute(f"SELECT * FROM challenges WHERE chat_id={chat_id} AND user_id={user_id}", fetchall=False)

    if record and record[7] == 1:
        # User clicks the button again to mark as not done
        add_xp(username, -xp, 'undoing a challenge')
        bot.answer_callback_query(call.id, "حذف شد.")
        execute(f"UPDATE challenges SET done=0 WHERE chat_id={chat_id} AND user_id={user_id}")
    else:
        # User clicks the button to mark as done
        bot.answer_callback_query(call.id, "ثبت شد.")
        add_xp(username, xp, 'doing a challenge')
        if record:
            execute(f"UPDATE challenges SET done=1 WHERE chat_id={chat_id} AND user_id={user_id}")
        else:
            execute(f"INSERT INTO challenges (chat_id, user_id, username, done) VALUES ({chat_id}, {user_id}, '{username}', 1)")

    # Retrieve the updated list of users who have marked the challenge as done
    users = execute(f"SELECT username FROM challenges WHERE chat_id={chat_id} AND done=1")

    challenge_text = user_data['challenge_text']
    xp = user_data['xp']
    duration = user_data['duration']

    users_list = "\n".join([f"• {user[0]}" for user in users])

    new_message_text = (
        f"📢 <b>چالش جدید</b>\n\n"
        f"<blockquote>📝 <b>متن: </b>{challenge_text}\n\n"
        f"🏆 <b>اکسپی:</b> {xp}\n\n"
        f"⏳ <b>مدت زمان:</b> {duration} ساعت\n\n</blockquote>"
        f"📋 <b>لیست کاربران:</b>\n{users_list}"
    )

    if call.message.text != new_message_text:
        bot.edit_message_text(chat_id=CHAT_ID, message_id=call.message.message_id,
                              text=new_message_text,
                              parse_mode='HTML',
                              reply_markup=call.message.reply_markup)

# Scheduling---------------------------------------------------------------------------------------------------------------------
# Global variable to hold the current thread
current_thread = None

def stop_thread():
    global current_thread
    if current_thread and current_thread.is_alive():
        current_thread.do_run = False
        current_thread.join()

def start_scheduling():
    global current_thread

    def schedule_messages():
        # Scheduling tasks
        schedule.every().day.at("01:30").do(streak_leaderboard)
        schedule.every().day.at("01:31").do(habit_tracker)
        schedule.every().day.at("01:32").do(xp_leaderboard)
        #schedule.every().day.at("14:10").do(update_leaderboard_history)
        #schedule.every().day.at("14:11").do(check_king_of_the_hill)

        while getattr(threading.current_thread(), "do_run", True):
            schedule.run_pending()
            time.sleep(1)

    # Stop the previous thread if it exists
    stop_thread()

    # Create and start a new thread
    current_thread = threading.Thread(target=schedule_messages)
    current_thread.do_run = True
    current_thread.daemon = True
    current_thread.start()

start_scheduling()


if __name__ == '__main__':
    print("Bot is now online!")
    print('--------------------------------')
    bot.infinity_polling(allowed_updates=update_types, timeout=None)











