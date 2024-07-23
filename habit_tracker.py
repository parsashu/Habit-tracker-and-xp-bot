import telebot, time, threading
from telebot import types
from telebot.apihelper import ApiTelegramException
from database_functions import execute
from ids import CHAT_ID, HABIT_THREAD_ID, HABITS, HABITS_ENGLISH, TOKEN

bot = telebot.TeleBot(TOKEN)

# Getting old habit tracker messages
records = execute("""
        SELECT message_id
        FROM messages
        ORDER BY message_id DESC
        LIMIT 7;
    """)
message_ids = []
for record in records:
    message_ids.append(record[0])
message_ids.reverse()


def habit_tracker():
    # Delete all data from habits table
    execute('DELETE FROM habits')

    # Delete the old habit tracker message if it exists
    try:
        old_habit_tracker_id = execute(f"""
                                    SELECT message_id
                                    FROM messages
                                    WHERE text = "کدامیک از فعالیت‌های زیر را امروز انجام داده‌اید؟ 📊"
                                        """,
                                        fetchall=False)[0]
        execute('DELETE FROM messages WHERE text = "کدامیک از فعالیت‌های زیر را امروز انجام داده‌اید؟ 📊"')

        if old_habit_tracker_id is not None:
            bot.delete_message(CHAT_ID, old_habit_tracker_id)
            execute(f"""
                DELETE FROM messages
                WHERE message_id = '{old_habit_tracker_id}'
                            """)
    except Exception as e:
        print(f"Error deleting old habit tracker message: {e}")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌅 سحرخیزی", callback_data="سحرخیزی"))
    markup.add(types.InlineKeyboardButton("💻 کار عمیق", callback_data="کار عمیق"))
    markup.add(types.InlineKeyboardButton("🧘‍♂️ مدیتیشن", callback_data="مدیتیشن"))
    markup.add(types.InlineKeyboardButton("📓 جورنال", callback_data="جورنال"))
    markup.add(types.InlineKeyboardButton("🚿 آب سرد", callback_data="آب سرد"))
    markup.add(types.InlineKeyboardButton("🏋️‍♀️ ورزش", callback_data="ورزش"))
    markup.add(types.InlineKeyboardButton("📚 خواندن کتاب", callback_data="خواندن کتاب"))

    new_habit_tracker = bot.send_message(CHAT_ID,
                    "کدامیک از فعالیت‌های زیر را امروز انجام داده‌اید؟ 📊",
                    reply_markup=markup,
                    message_thread_id=HABIT_THREAD_ID
                    )
    bot.send_message(
        CHAT_ID, 
        "📋<b>لیست افرادی که فعالیت‌ها را انجام داده‌اند:</b>", 
        message_thread_id=HABIT_THREAD_ID, 
        parse_mode='HTML'
    )

    # Insert new habit tracker message
    execute(f"INSERT INTO messages (message_id, text) VALUES ({new_habit_tracker.message_id}, '{new_habit_tracker.text}')")

    global message_ids
    message_ids = []

    for habit in HABITS:
        try:
            msg = bot.send_message(CHAT_ID, f"📌{habit}:\n-", message_thread_id=HABIT_THREAD_ID)
        except ApiTelegramException as e:
            if e.result.status_code == 429:
                retry_after = int(e.result.json().get('parameters', {}).get('retry_after', 1))
                time.sleep(retry_after)
                msg = bot.send_message(CHAT_ID, f"📌{habit}:\n-", message_thread_id=HABIT_THREAD_ID)
            else:
                print(f"Error sending habit message: {e}")
                continue

        message_ids.append(msg.message_id)
        execute(f"INSERT INTO messages (message_id, text) VALUES ({msg.message_id}, '{msg.text}')")

user_clicks = {}

def clean_old_data():
    while True:
        current_time = time.time()
        to_remove = [user_id for user_id, clicks in user_clicks.items() if current_time - clicks[-1] > 3600]  # 1 hour
        for user_id in to_remove:
            del user_clicks[user_id]
        time.sleep(3600)  # هر یک ساعت

# شروع کردن یک ترد برای پاکسازی داده‌های قدیمی
cleaning_thread = threading.Thread(target=clean_old_data)
cleaning_thread.daemon = True
cleaning_thread.start()

# Button logic
def habit_button_logic(call):
    global message_ids
    global user_clicks
    habit = call.data
    user_id = call.from_user.id
    username = call.from_user.username
    user_id = call.from_user.id
    current_time = time.time()

    # Prevent user from spamming button
    if user_id in user_clicks:
        clicks = user_clicks[user_id]
        # فیلتر کردن کلیک‌هایی که بیشتر از 1.5 ثانیه پیش بوده‌اند
        clicks = [t for t in clicks if current_time - t < 1.5]
        # اگر تعداد کلیک‌های باقی‌مانده بیشتر از 1 باشد
        if len(clicks) >= 1:
            bot.answer_callback_query(call.id, text="لطفا صبر کنید.")
            return
        clicks.append(current_time)
        user_clicks[user_id] = clicks
    else:
        user_clicks[user_id] = [current_time]

    # Finding message list in respect to specific habit
    index = HABITS.index(habit)
    message_id = message_ids[index]

    original_message = execute(
        f"""
            SELECT text
            FROM messages
            WHERE message_id = '{message_id}'
        """,
        fetchall=False
    )

    # Insert in DB_streak2 if not exist
    exist_check = execute(
        f"""
            SELECT *
            FROM DB_streak2
            WHERE User = '{username}'
        """,
        fetchall=False
    )

    if exist_check is None:
        execute(f"""
    INSERT INTO DB_streak2 (User, EarlyRising, DeepWork, Meditation, Journal, ColdShower, Gym, ReadingBook)
    VALUES ('{username}', 0, 0, 0, 0, 0, 0, 0)
                        """)

    # Check if the user has already clicked this habit
    report = execute(f"""
                SELECT *
                FROM habits
                WHERE user_id = '{user_id}' AND habit = '{habit}'
                """, 
                fetchall=False
            )

    # User hasn't clicked the habit
    if report is None:
        date = time.strftime("%Y-%m-%d")  
        execute(f"""
                INSERT INTO habits (user_id, username, habit, date)
                VALUES ('{user_id}', '{username}', '{habit}', '{date}')
                        """)

        bot.answer_callback_query(call.id, f"ثبت شد: {habit}")

        # Adding user to the completed list
        new_text = original_message[0] + f" @{username}|"
        bot.edit_message_text(new_text, chat_id=CHAT_ID, message_id=message_id)

        execute( f"""
                UPDATE messages
                SET text = '{new_text}'
                WHERE message_id = '{message_id}'
                            """)
        
    # User has already clicked the habit
    elif report[2] == habit:
        bot.answer_callback_query(call.id, "عادت انتخابی حذف شد.")
        execute(f"""
                DELETE FROM habits
                WHERE user_id = '{user_id}' AND habit = '{habit}'
                            """)

        segments = original_message[0].split(' ')
        updated_segments = []

        # Remove the username from the segments
        for seg in segments:
            if seg.strip() != f'@{username}|':
                updated_segments.append(seg)

        # Join the segments back into a string
        #title = f'📌{habit}:\n-'
        new_text_ = ' '.join(updated_segments)
        bot.edit_message_text(new_text_, chat_id=CHAT_ID, message_id=message_id)

        execute(f"""
                UPDATE messages
                SET text = '{new_text_}'
                WHERE message_id = '{message_id}'
                        """)
        return

# LeaderBoard for streaks
def streak_leaderboard():
    # Calculate streaks
    doer_users = execute("SELECT username, habit FROM habits")
    all_users = execute("SELECT * FROM DB_streak2")

    for user in all_users:
        for i in range(7):   # Needs to change when another habit added!
            username = user[0]
            habit_ = HABITS[i]
            old_streak = user[i + 1]

            # Calculating new streak
            if (username, habit_) in doer_users:
                new_streak = int(old_streak) + 1
            else:
                new_streak = 0

            # Updating the streak for user and habit
            habit_english = HABITS_ENGLISH[i]
            execute(f"UPDATE DB_streak2 SET {habit_english} = {new_streak} WHERE User = '{username}'")

    # Getting leaderboard datas
    leaderboard_str = "🏆 <b>Streak Leaderboard</b> 🏆\n\n<b>Username</b>    |    <b>Streak</b>\n\n"
    for english_habit in HABITS_ENGLISH:
        leaderboard = execute(f"SELECT User, {english_habit} FROM DB_streak2")
        sorted_leaderboard = sorted(leaderboard, key=lambda x: int(x[1]))

        if len(sorted_leaderboard) >= 3:
            top3 = sorted_leaderboard[-3:]
            top3 = top3[::-1]
        else:
            top3 = sorted_leaderboard[::-1]

        leaderboard_str += f"<b>{english_habit}</b> 〰️〰️〰️〰️〰️〰️〰️〰️〰️\n"
        for idx, member in enumerate(top3, start=1):
            medals = ["🥇", "🥈", "🥉"]
            medal = medals[idx - 1] if idx <= 3 else ""
            leaderboard_str += f"{medal} {idx}. {member[0]}  -  {member[1]}\n"
        leaderboard_str += '\n'

    msg = bot.send_message(CHAT_ID, leaderboard_str, message_thread_id=HABIT_THREAD_ID, parse_mode='HTML')   
    try:
        bot.pin_chat_message(CHAT_ID, msg.message_id, disable_notification=True)
    except Exception as e:
        print(f"Error pinning message: {e}")
        