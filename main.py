import telebot
import requests 
import user_agent 
import time
import uuid
import random
import os
import json
from telebot import types
from threading import Lock

# Bot Configuration
BOT_TOKEN = "7305455161:AAE_GKpzo09eMJJje_gOttCXYCZqEWN9VUg"
bot = telebot.TeleBot(BOT_TOKEN)

# User Database
USER_DATA_FILE = "users_data.json"
user_data_lock = Lock()

# Welcome Text
WELCOME_MESSAGE = """
🔥 Welcome to Instagram Account Creator Bot 🔥

📱 Developer: @nusrc
⚙️ Tool: Instagram Account Creator
🌐 Server: Application

Press /create to create a new account
"""

# Initialize data file if not exists
def init_data_file():
    if not os.path.exists(USER_DATA_FILE):
        with user_data_lock:
            with open(USER_DATA_FILE, "w") as f:
                json.dump({}, f)

# Save user data
def save_user_data(user_id, data):
    with user_data_lock:
        try:
            with open(USER_DATA_FILE, "r") as f:
                all_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            all_data = {}
        
        all_data[str(user_id)] = data
        
        with open(USER_DATA_FILE, "w") as f:
            json.dump(all_data, f, indent=4)

# Get user data
def get_user_data(user_id):
    user_id = str(user_id)
    with user_data_lock:
        try:
            with open(USER_DATA_FILE, "r") as f:
                all_data = json.load(f)
                return all_data.get(user_id, {})
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

# Clear user session after process completion
def clear_user_session(user_id):
    data = get_user_data(user_id)
    # Keep only previously created accounts
    accounts = data.get("created_accounts", [])
    save_user_data(user_id, {"created_accounts": accounts, "current_process": None})

# Add new account to user's created accounts list
def add_created_account(user_id, account_info):
    data = get_user_data(user_id)
    if "created_accounts" not in data:
        data["created_accounts"] = []
    
    data["created_accounts"].append(account_info)
    save_user_data(user_id, data)

# Start command
@bot.message_handler(commands=['start'])
def start_command(message):
    init_data_file()
    bot.send_message(message.chat.id, WELCOME_MESSAGE, parse_mode='Markdown')

# Create new account command
@bot.message_handler(commands=['create'])
def create_account_command(message):
    msg = bot.send_message(message.chat.id, "Enter email address to create a new account:")
    bot.register_next_step_handler(msg, process_email_step)

# Process email input step
def process_email_step(message):
    email = message.text.strip()
    user_id = message.from_user.id
    
    # Save email in user data
    user_data = get_user_data(user_id)
    user_data["current_process"] = {"email": email}
    save_user_data(user_id, user_data)
    
    # Setup session variables
    st4_uuid = str(uuid.uuid4())
    st4_time = str(time.time()).split('.')[1]
    st4_user_agent = str(user_agent.generate_user_agent())
    st4_session = requests.Session()
    
    # Check email
    url = "https://www.instagram.com/api/v1/web/accounts/check_email/"
    payload = {
        'email': email,
    }
    headers = {
        'User-Agent': st4_user_agent, 
        'sec-ch-ua': "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\"",
        'x-ig-www-claim': "0",
        'x-web-session-id': "o7brq2:ihhkws:b833kp",
        'sec-ch-ua-platform-version': "\"14.0.0\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua-full-version-list': "\"Not A(Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"132.0.6961.0\"",
        'sec-ch-prefers-color-scheme': "dark",
        'x-csrftoken': "8D26VZbnpmxsokorogKvshOiKojeTii5",
        'sec-ch-ua-platform': "\"Android\"",
        'x-ig-app-id': "1217981644879628",
        'sec-ch-ua-model': "\"RMX3941\"",
        'sec-ch-ua-mobile': "?1",
        'x-instagram-ajax': "1021370996",
        'x-asbd-id': "359341",
        'origin': "https://www.instagram.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.instagram.com/accounts/signup/email/",
        'accept-language': "en",
    }
    
    try:
        response = st4_session.post(url, data=payload, headers=headers).text
        if '"available":true' in response:
            # Save session data
            user_data["current_process"]["user_agent"] = st4_user_agent
            user_data["current_process"]["time"] = st4_time
            user_data["current_process"]["device_id"] = "Z8-eMwABAAH5f09r6VWab1y0iA86"
            save_user_data(user_id, user_data)
            
            # Send verification code
            url = "https://www.instagram.com/api/v1/accounts/send_verify_email/"
            payload = {
                'device_id': "Z8-eMwABAAH5f09r6VWab1y0iA86",
                'email': email,  
            }
            
            response = st4_session.post(url, data=payload, headers=headers).text
            if '"email_sent":true' in response:
                bot.send_message(message.chat.id, "✅ Verification code sent to your email.\n\nEnter the code you received:")
                bot.register_next_step_handler(message, process_verification_code)
            else:
                bot.send_message(message.chat.id, f"❌ Error sending verification code: {response}")
                clear_user_session(user_id)
        else:
            bot.send_message(message.chat.id, f"❌ Email not available: {response}")
            clear_user_session(user_id)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error occurred: {str(e)}")
        clear_user_session(user_id)

# Process verification code step
def process_verification_code(message):
    st4_code = message.text.strip()
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if "current_process" not in user_data:
        bot.send_message(message.chat.id, "❌ Session expired, please start again with /create")
        return
    
    email = user_data["current_process"]["email"]
    st4_user_agent = user_data["current_process"]["user_agent"]
    device_id = user_data["current_process"]["device_id"]
    
    url = "https://www.instagram.com/api/v1/accounts/check_confirmation_code/"
    payload = {
        'code': st4_code,
        'device_id': device_id,
        'email': email,
    }
    headers = {
        'User-Agent': st4_user_agent, 
        'sec-ch-ua': "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\"",
        'x-ig-www-claim': "0",
        'x-web-session-id': "o7brq2:ihhkws:b833kp",
        'sec-ch-ua-platform-version': "\"14.0.0\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua-full-version-list': "\"Not A(Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"132.0.6961.0\"",
        'sec-ch-prefers-color-scheme': "dark",
        'x-csrftoken': "8D26VZbnpmxsokorogKvshOiKojeTii5",
        'sec-ch-ua-platform': "\"Android\"",
        'x-ig-app-id': "1217981644879628",
        'sec-ch-ua-model': "\"RMX3941\"",
        'sec-ch-ua-mobile': "?1",
        'x-instagram-ajax': "1021370996",
        'x-asbd-id': "359341",
        'origin': "https://www.instagram.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.instagram.com/accounts/signup/emailConfirmation/",
        'accept-language': 'en',
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        result = response.json()
        if 'signup_code' in result:
            st4_newCode = result['signup_code']
            user_data["current_process"]["signup_code"] = st4_newCode
            save_user_data(user_id, user_data)
            
            # Proceed to create account
            create_instagram_account(message)
        else:
            bot.send_message(message.chat.id, f"❌ Invalid verification code: {response.text}")
            clear_user_session(user_id)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error verifying code: {str(e)}")
        clear_user_session(user_id)

# Create Instagram account
def create_instagram_account(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if "current_process" not in user_data:
        bot.send_message(message.chat.id, "❌ Session expired, please start again with /create")
        return
    
    email = user_data["current_process"]["email"]
    st4_user_agent = user_data["current_process"]["user_agent"]
    st4_time = user_data["current_process"]["time"]
    st4_newCode = user_data["current_process"]["signup_code"]
    
    # Create random account data
    st4_password = ''.join(random.choice('qwertyuiopasdfghjklzxcvbnm1234567890') for i in range(random.randrange(9, 10)))
    username = ''.join(random.choice('qwertyuiopasdfghjklzxcvbnm1234567890') for i in range(10))
    st4_day = random.randrange(1, 28)
    st4_first_name = random.choice(["John", "Alex", "Michael", "Robert", "David", "Thomas", "James", "William", "Christopher", "Matthew", "Daniel"])
    st4_month = random.randrange(1, 12)
    st4_year = random.randrange(1989, 2006)
    
    url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"
    payload = {
        'enc_password': f"#PWD_INSTAGRAM_BROWSER:0:{st4_time}:{st4_password}",
        'day': st4_day,
        'email': email,
        'failed_birthday_year_count': "{}",
        'first_name': st4_first_name,
        'month': st4_month,
        'username': username,
        'year': st4_year,
        'client_id': "Z8-eMwABAAH5f09r6VWab1y0iA86",
        'seamless_login_enabled': "1",
        'tos_version': "row",
        'force_sign_up_code': st4_newCode,  
    }
    headers = {
        'User-Agent': st4_user_agent, 
        'sec-ch-ua': "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\"",
        'x-ig-www-claim': "0",
        'x-web-session-id': "v3s3xo:8vy7v8:i14b7i",
        'sec-ch-ua-platform-version': "\"14.0.0\"",
        'x-requested-with': "XMLHttpRequest",
        'sec-ch-ua-full-version-list': "\"Not A(Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"132.0.6961.0\"",
        'sec-ch-prefers-color-scheme': "dark",
        'x-csrftoken': "B6yOLYbJgFWFh2e0rNe2wZHXbnPZw9LP",
        'sec-ch-ua-platform': "\"Android\"",
        'x-ig-app-id': "1217981644879628",
        'sec-ch-ua-model': "\"RMX3941\"",
        'sec-ch-ua-mobile': "?1",
        'x-instagram-ajax': "1021374421",
        'x-asbd-id': "359341",
        'origin': "https://www.instagram.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.instagram.com/accounts/signup/username/",
        'accept-language': "en",
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        if '"account_created":true' in response.text:
            ST4_SESSION = response.cookies.get_dict()['sessionid']
            
            # Store account info
            account_info = {
                "email": email,
                "username": username,
                "password": st4_password,
                "name": st4_first_name,
                "birth": f"{st4_year}/{st4_month}/{st4_day}",
                "sessionid": ST4_SESSION,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Save account info for user
            add_created_account(user_id, account_info)
            
            # Save session to external file
            with open("ACC_SESSIONS_IG.txt", "a") as f:
                f.write(f"{ST4_SESSION}\n")
            
            # Create success message
            success_message = f"""
✅ Account created successfully!

📧 Email: {email}
👤 Username: {username}
🔑 Password: {st4_password}
📝 Name: {st4_first_name}
🎂 Birth Date: {st4_year}/{st4_month}/{st4_day}
🔐 Session ID: {ST4_SESSION}

🔰 Session ID saved to ACC_SESSIONS_IG.txt

Thanks for using the bot! 🙏
Developer: @ix_chyo
"""
            bot.send_message(message.chat.id, success_message)
            
            # Add control buttons
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("Create New Account", callback_data="new_account"),
                types.InlineKeyboardButton("View My Accounts", callback_data="my_accounts")
            )
            bot.send_message(message.chat.id, "What would you like to do now?", reply_markup=markup)
            
            # Clear current process data
            clear_user_session(user_id)
        else:
            bot.send_message(message.chat.id, f"❌ Account creation failed: {response.text}")
            clear_user_session(user_id)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error creating account: {str(e)}")
        clear_user_session(user_id)

# Handle interactive buttons
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "new_account":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        create_account_command(call.message)
    
    elif call.data == "my_accounts":
        user_id = call.from_user.id
        user_data = get_user_data(user_id)
        accounts = user_data.get("created_accounts", [])
        
        if not accounts:
            bot.answer_callback_query(call.id, "You haven't created any accounts yet!")
            return
        
        # Display created accounts
        accounts_text = "🔰 Your created accounts:\n\n"
        
        for i, account in enumerate(accounts, 1):
            accounts_text += f"📱 Account {i}:\n"
            accounts_text += f"👤 Username: {account['username']}\n"
            accounts_text += f"📧 Email: {account['email']}\n"
            accounts_text += f"🔑 Password: {account['password']}\n"
            accounts_text += f"📅 Created on: {account.get('created_at', 'Unknown')}\n\n"
        
        bot.send_message(call.message.chat.id, accounts_text)
        bot.answer_callback_query(call.id)

# Show accounts command
@bot.message_handler(commands=['accounts'])
def show_accounts(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    accounts = user_data.get("created_accounts", [])
    
    if not accounts:
        bot.send_message(message.chat.id, "You haven't created any accounts yet!")
        return
    
    # Display created accounts
    accounts_text = "🔰 Your created accounts:\n\n"
    
    for i, account in enumerate(accounts, 1):
        accounts_text += f"📱 Account {i}:\n"
        accounts_text += f"👤 Username: {account['username']}\n"
        accounts_text += f"📧 Email: {account['email']}\n"
        accounts_text += f"🔑 Password: {account['password']}\n"
        accounts_text += f"📅 Created on: {account.get('created_at', 'Unknown')}\n\n"
    
    bot.send_message(message.chat.id, accounts_text)

# Help command
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📋 **Commands List:**

/start - Start using the bot
/create - Create a new Instagram account
/accounts - View your created accounts
/help - Show this help

🔰 **How to use:**
1. Click /create to start creating a new account
2. Enter your email address
3. Enter the verification code sent to your email
4. An account with random info will be created and sent to you

🔰 **Developer:**
@ix_chyo
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# Handle unknown messages
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    bot.send_message(message.chat.id, "Sorry, I didn't understand your request. Use /help to get the commands list.")

if __name__ == "__main__":
    init_data_file()
    print("🚀 Bot started...")
    bot.infinity_polling()