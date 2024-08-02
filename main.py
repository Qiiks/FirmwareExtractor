import os
import time
import requests
import logging
import telebot
from telebot import types
from dotenv import load_dotenv
from collections import defaultdict


logging.basicConfig(
    filename='bot.log',  # Log file name
    filemode='a',  # Append mode
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Log message format
)

# Create a custom logger
logger = logging.getLogger(__name__)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set logging level for the console handler to INFO and above

# Create a formatter and add it to the console handler
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Add the console handler to the logger
logger.addHandler(console_handler)


# Load environment variables from .env file
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')
GITHUB_REPO = 'Qiiks/FirmwareExtractor'  # Replace with your GitHub username and repository
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Initialize Telegram bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Track user requests and cooldowns
user_cooldowns = defaultdict(lambda: 0)
COOLDOWN_PERIOD = 10 * 60  # 10 minutes in seconds

def trigger_github_workflow(repo, token, firmware_url):
    workflow_url = f'https://api.github.com/repos/{repo}/actions/workflows/extract_payload.yml/dispatches'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    data = {
        'ref': 'main',  # or the branch you want to run the workflow on
        'inputs': {
            'firmware_url': firmware_url
        }
    }
    response = requests.post(workflow_url, headers=headers, json=data)
    response.raise_for_status()
    logger.info(f'Triggered workflow for {firmware_url}')

def get_latest_run_id(repo, token):
    url = f'https://api.github.com/repos/{repo}/actions/runs'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    runs = response.json()['workflow_runs']
    if not runs:
        raise ValueError('No workflow runs found')

    runs.sort(key=lambda x: x['created_at'], reverse=True)
    latest_run = runs[0]
    run_id = latest_run['id']
    logger.info(f'Latest run ID: {run_id}')
    return run_id

def check_run_status(repo, run_id, token):
    url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    run_status = response.json()['status']
    logger.info(f'Workflow run status: {run_status}')
    return run_status

def get_artifact_download_url(repo, run_id, token):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    artifacts_url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts'
    response = requests.get(artifacts_url, headers=headers)
    response.raise_for_status()

    artifacts = response.json()['artifacts']
    if artifacts:
        # Assuming the first artifact is the one you want
        artifact = artifacts[0]
        download_url = artifact['archive_download_url']
        logger.info(f'Artifact download URL: {download_url}')
        return download_url
    else:
        raise ValueError('No artifacts found')

def send_download_link_via_telegram(bot, channel_id, download_url, message):
    bot.send_message(chat_id=channel_id, text=f"Your files are ready. Download them from: {download_url}", reply_parameters=types.ReplyParameters(message.message_id))
    logger.info(f'Sent download link to Telegram channel {channel_id}')

@bot.message_handler(commands=['download'])
def handle_download(message):
    user_id = message.from_user.id
    current_time = time.time()
    last_request_time = user_cooldowns[user_id]

    if current_time - last_request_time < COOLDOWN_PERIOD:
        wait_time = COOLDOWN_PERIOD - (current_time - last_request_time)
        bot.reply_to(message, f"Please wait {int(wait_time / 60)} minutes before requesting again.")
        return
    
    user_cooldowns[user_id] = current_time
    
    try:
        command, firmware_url = message.text.split(' ', 1)
        if 'https://dl.google.com/dl/android/aosp/' in firmware_url and 'factory' not in firmware_url:
            bot.reply_to(message, "Processing your request. This may take a while.")
        else:
            bot.reply_to(message, 'Link is invalid, Provide download link for full OTA zip.')
            return
        trigger_github_workflow(GITHUB_REPO, GITHUB_TOKEN, firmware_url)
        bot.reply_to(message, "Started the GitHub workflow. I will notify you once the files are ready.")

        # Fetch latest run ID and check workflow status
        run_id = get_latest_run_id(GITHUB_REPO, GITHUB_TOKEN)
        
        # Poll for workflow status
        while True:
            status = check_run_status(GITHUB_REPO, run_id, GITHUB_TOKEN)
            if status == 'completed':
                break
            time.sleep(10)  # Wait before checking again

        download_url = get_artifact_download_url(GITHUB_REPO, run_id, GITHUB_TOKEN)
        send_download_link_via_telegram(bot, message.chat.id, download_url, message)
        bot.reply_to(message, "Files are ready. Check the channel for the download link.")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

def main():
    logger.info("Bot started")
    bot.polling()

while True:
    try:
        main()
    except Exception as e:
        logger.info("error occured: ", e)
        time.sleep(5)  # Wait 5 seconds before retrying
