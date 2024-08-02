import os
import requests
import telebot
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')
GITHUB_REPO = 'Qiiks/FirmwareExtractor'  # Replace with your GitHub username and repository
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Initialize Telegram bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

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
    print(f'Triggered workflow for {firmware_url}')

def download_artifacts(repo, run_id, token):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    artifacts_url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts'
    response = requests.get(artifacts_url, headers=headers)
    response.raise_for_status()

    artifacts = response.json()['artifacts']
    for artifact in artifacts:
        download_url = artifact['archive_download_url']
        artifact_name = artifact['name']
        download_response = requests.get(download_url, headers=headers, stream=True)
        download_response.raise_for_status()
        
        with open(f'{artifact_name}.zip', 'wb') as f:
            for chunk in download_response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f'Downloaded {artifact_name}.zip')

def extract_files(artifact_name):
    import zipfile
    with zipfile.ZipFile(f'{artifact_name}.zip', 'r') as zip_ref:
        zip_ref.extractall(artifact_name)
    print(f'Extracted {artifact_name}')

def send_files_via_telegram(bot, channel_id, file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                bot.send_document(chat_id=channel_id, document=file)
                print(f'Sent {file_path} to Telegram channel {channel_id}')
        else:
            print(f'File not found: {file_path}')

@bot.message_handler(commands=['download'])
def handle_download(message):
    try:
        command, firmware_url = message.text.split(' ', 1)
        trigger_github_workflow(GITHUB_REPO, GITHUB_TOKEN, firmware_url)
        bot.reply_to(message, "Started the GitHub workflow. I will notify you once the files are ready.")

        # This part requires polling or webhook to get the run_id and then download artifacts
        # Assuming the run_id is somehow obtained after the workflow completion
        run_id = 'latest_run_id'  # Replace this with the actual method to get the latest run_id
        download_artifacts(GITHUB_REPO, run_id, GITHUB_TOKEN)
        extract_files('extracted-files')

        file_paths = [
            'extracted-files/boot.img',
            'extracted-files/vendor_boot.img',
            'extracted-files/dtbo.img'
        ]
        send_files_via_telegram(bot, message.chat.id, file_paths)
        bot.reply_to(message, "Files have been sent to the channel.")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

def main():
    bot.polling()

if __name__ == '__main__':
    main()