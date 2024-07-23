import telebot, sqlite3, time
from database_functions import execute
from ids import CHAT_ID, CHAT_ID_ADMINS, LOG_THREAD_ID, XP_THREAD_ID, HABITS, LEVELS, TOKEN


bot = telebot.TeleBot(TOKEN)
#updates = bot.get_updates()
 

def add_xp(user, xp_increment, reason):
    new_user = False    # Flag to determine if the use just has been inserted
    Connection = sqlite3.connect('files.db')
    cursor = Connection.cursor()
    cursor.execute(f"SELECT XP FROM DB_XP WHERE User = '{user}';")
    Connection.commit()
    record = cursor.fetchall()
    cursor.close()

    if len(record) == 0:
        # User does not exist, insert new record
        total_xp = xp_increment
        cursor = Connection.cursor()
        cursor.execute(f"INSERT INTO DB_XP (User, XP, Level) VALUES  ('{user}', '{xp_increment}', 'جایمند');")
        Connection.commit()
        record = cursor.fetchall()
        cursor.close()
        new_user = True

    else:
        # Updating XP
        total_xp = int(record[0][0]) + xp_increment
        cursor = Connection.cursor()
        cursor.execute(f"UPDATE DB_XP SET XP = '{str(total_xp)}'  WHERE User = '{user}' ;")
        Connection.commit()
        record = cursor.fetchall()
        cursor.close()

        # LEVELING LOGIC-----------------------------
        if xp_increment != 0 and not new_user:
            # Log report
            bot.send_message(
                            chat_id=CHAT_ID_ADMINS,
                            text=f'@{user} gained {xp_increment} xp from {reason}.\nTotal xp: {total_xp}',
                            message_thread_id=LOG_THREAD_ID
                                )
            
            def up_report(username, level):
                text = f"تبریک به @{username}! شما به سطح <b>{level}</b> ارتقا یافتید!"
                bot.send_message(CHAT_ID, text, message_thread_id=XP_THREAD_ID, parse_mode='HTML')

            def down_report(username, level):
                text = f"متأسفانه @{username}، شما به سطح <b>{level}</b> نزول کردید."
                bot.send_message(CHAT_ID, text, message_thread_id=XP_THREAD_ID, parse_mode='HTML')

            def get_level(username):
                cursor = Connection.cursor()
                cursor.execute(f"SELECT Level FROM DB_XP WHERE User = '{username}';")
                Connection.commit()
                record = cursor.fetchone()
                cursor.close()
                return record[0]
                    
            def update_db(username, level):
                cursor = Connection.cursor()
                cursor.execute(f"UPDATE DB_XP SET Level = '{level}'  WHERE User = '{username}' ;")
                Connection.commit()
                cursor.close()


            old_level = get_level(user)
            if total_xp >= 2000:
                if old_level != LEVELS[3]:
                    new_level = LEVELS[3]
                    up_report(user, new_level)
                    update_db(user, new_level)


            elif 2000 > total_xp >= 500:
                if old_level != LEVELS[2]:
                    new_level = LEVELS[2]
                    update_db(user, new_level)

                    if old_level == LEVELS[3]:
                        down_report(user, new_level)
                    else:
                        up_report(user, new_level)


            elif 500 > total_xp >= 100:
                if old_level != LEVELS[1]:
                    new_level = LEVELS[1]
                    update_db(user, new_level)

                    if old_level == LEVELS[0]:
                        up_report(user, new_level)
                    else:
                        down_report(user, new_level)

            elif total_xp < 100:
                if old_level != LEVELS[0]:
                    new_level = LEVELS[0]
                    down_report(user, new_level)
                    update_db(user, new_level)

    return total_xp


def get_overview(username):
    Connection = sqlite3.connect('files.db')
    cursor = Connection.cursor()
    cursor.execute("SELECT XP, Level FROM DB_XP WHERE User = ?", (username,))
    record = cursor.fetchone()
    cursor.close()
    return int(record[0]), record[1]

   

# LeaderBoard for xp
def xp_leaderboard():
    # Getting all users
    Connection = sqlite3.connect('files.db')
    cursor = Connection.cursor()
    cursor.execute(f"SELECT User, XP, Level FROM DB_XP;")
    users = cursor.fetchall()
    cursor.close()

    lb = []
    for user in users:
        username, total_xp, level = user
        total_xp = int(total_xp)  # Convert XP from str to int
        lb.append((username, total_xp, level))

    lb.sort(key=lambda x: x[1], reverse=True)
    top_10 = lb[:10]

    # Create leaderboard message
    leaderboard_str = "🏆 <b>XP Leaderboard</b> 🏆\n\n<b>Username</b> ︱ <b>XP</b> ︱ <b>Level</b>\n〰️〰️〰️〰️〰️〰️〰️〰️〰️\n\n"
    for idx, member in enumerate(top_10, start=1):
        leaderboard_str += f"{idx}. {member[0]} - <b>{member[2]}</b> - {member[1]}\n\n"
    
    msg = bot.send_message(CHAT_ID, leaderboard_str, message_thread_id=XP_THREAD_ID, parse_mode='HTML')
    try:
        bot.pin_chat_message(CHAT_ID, msg.message_id, disable_notification=True)
    except Exception as e:
        print(f"Error pinning message: {e}")


# KING OF THE HILL
def check_king_of_the_hill():
    today = time.strftime("%Y-%m-%d")
    yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
    three_days_ago = time.strftime("%Y-%m-%d", time.localtime(time.time() - 3 * 86400))
    yesterday_leaderboard = execute(f"SELECT username, habit FROM leaderboard_history WHERE date = '{yesterday}'")

    for leader in yesterday_leaderboard:
        username, habit = leader
        result = execute(
            f"""
            SELECT COUNT(*)
            FROM leaderboard_history
            WHERE username = '{username}' AND habit = '{habit}' AND date BETWEEN '{three_days_ago}' AND '{yesterday}'
            """,
            fetchall=False
        )
        count = result[0]

        if count >= 3:
            add_xp(username, 1, f'King of the hill for habit: {habit}')

# Function to update leaderboard history
def update_leaderboard_history():
    date = time.strftime("%Y-%m-%d")
    execute(f"DELETE FROM leaderboard_history WHERE date = '{date}'")

    for habit in HABITS:
        top_user = execute(
            f"""
            SELECT username
            FROM habits
            WHERE habit = '{habit}' AND date = '{date}'
            ORDER BY streak DESC
            LIMIT 1
            """,
            fetchall=False
        )
        
        if top_user:
            execute(
                f"""
                INSERT INTO leaderboard_history (date, username, habit)
                VALUES ('{date}', '{top_user[0]}', '{habit}')
                """
            )


# Add xp manualy 
def add_xp_command(message):      
    try:
        # Parse the command arguments
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(
                CHAT_ID, 
                "Example: /add_xp <username> <xp_increment>\nلطفا هر دو مورد نام‌کاربری و افزایش امتیاز را وارد کنید.",
                message_thread_id=message.message_thread_id
            )
            return
        
        username = args[1][1:]
        xp_increment = int(args[2])
    
        add_xp(username, xp_increment, 'manual add_xp command')
        bot.send_message(
            CHAT_ID,
            f"با موفقیت {xp_increment} xp به @{username} اضافه شد.",
            message_thread_id=message.message_thread_id
        )

    except Exception as e:
        print(e)
        bot.send_message(
            CHAT_ID,
            "خطایی در افزودن xp رخ داده است.",
            message_thread_id=message.message_thread_id
        )


# Remove xp manualy
def remove_xp_command(message): 
    try:
        # Parse the command arguments
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(
                CHAT_ID, 
                "Example: /add_xp <username> <xp_increment>\nلطفا هر دو مورد نام‌کاربری و افزایش امتیاز را وارد کنید.",
                message_thread_id=message.message_thread_id
            )
            return
        
        username = args[1][1:]
        xp_increment = -int(args[2])

        add_xp(username, xp_increment, 'manual remove_xp command')
        bot.send_message(
            CHAT_ID,
            f"با موفقیت {-xp_increment} xp از @{username} حذف شد.",
            message_thread_id=message.message_thread_id
        )

    except Exception as e:
        print(e)
        bot.send_message(
            CHAT_ID,
            "خطایی در حذف xp رخ داده است.",
            message_thread_id=message.message_thread_id
        )



def overview_command(message):
    member = message.from_user.username  # Assuming the member who sent the command
    total_xp, level = get_overview(member)

    # Determine XP required to level up
    if total_xp < 100:
        xp_to_up = f"{100 - total_xp} xp برای رسیدن به سطح بعدی "
    elif 100 <= total_xp < 500:
        xp_to_up = f"{500 - total_xp} xp برای رسیدن به سطح بعدی"
    elif 500 <= total_xp < 2000:
        xp_to_up = f"{2000 - total_xp} xp برای رسیدن به سطح بعدی"
    elif total_xp >= 2000:
        xp_to_up = "شما به بیشترین سطح رسیده‌اید"

    message_text = (
        "<b>Overview 📈</b>\n\n"
        f"<blockquote><b>Username:</b> @{member}\n\n"
        f"<b>Total xp:</b> {total_xp} xp | {xp_to_up}\n\n"
        f"<b>Level:</b> {level}</blockquote>"
    )

    # Send the XP and level overview as HTML-formatted message
    bot.reply_to(message, message_text, parse_mode='HTML')

