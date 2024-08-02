import os
import requests
import zipfile
import subprocess
import telebot
import shutil

# Configuration
DOWNLOAD_URL = 'https://dl.google.com/dl/android/aosp/oriole-ota-ap2a.240705.004-0fe0567d.zip'
TELEGRAM_TOKEN = '7458211623:AAEl7Msf2vLE627BhvUOFZ6qavkwHWQ1G2U'
CHANNEL_ID = '-1002247204227'

# Directory paths
DOWNLOAD_DIR = 'downloaded_files'
EXTRACT_DIR = 'extracted_files'
PAYLOAD_DIR = 'payload_files'

# Ensure directories exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)
os.makedirs(PAYLOAD_DIR, exist_ok=True)

def download_file(url, dest):
    response = requests.get(url, stream=True)
    print("downloading....")
    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"Downloaded {dest}")

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Extracted {zip_path} to {extract_to}")

def extract_specific_files(payload_path, extract_to, files_to_extract):
    # Assuming you have payload_dumper installed and in PATH
    for file_name in files_to_extract:
        subprocess.run(['payload-dumper-go.exe', '-p', file_name, '-o', extract_to, payload_path], check=True)
    print(f"Extracted specific files from payload.bin to {extract_to}")

def send_files_via_telegram(bot, channel_id, file_paths):
    for file_path in file_paths:
        with open(file_path, 'rb') as file:
            bot.send_document(channel_id, file)
            print(f"Sent {file_path} to Telegram channel {channel_id}")

def cleanup(directories):
    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            print(f"Deleted {directory}")

def main():
    # Initialize Telegram bot
    bot = telebot.TeleBot(TELEGRAM_TOKEN)

    # Download firmware file
    firmware_zip_path = os.path.join(DOWNLOAD_DIR, 'firmware.zip')
    #download_file(DOWNLOAD_URL, firmware_zip_path)

    # Extract firmware file
    #extract_zip(firmware_zip_path, EXTRACT_DIR)

    # Extract specific files from payload.bin
    payload_path = os.path.join(EXTRACT_DIR, 'payload.bin')
    required_files = ['boot', 'init_boot', 'vendor_boot', 'dtbo']
    extract_specific_files(payload_path, PAYLOAD_DIR, required_files)

    # Collect required files
    required_files = ['boot.img', 'vendor_boot.img', 'dtbo.img']
    file_paths = [os.path.join(PAYLOAD_DIR, file) for file in required_files]

    # Send files to Telegram channel
    send_files_via_telegram(bot, CHANNEL_ID, file_paths)

    # Clean up
    cleanup([DOWNLOAD_DIR, EXTRACT_DIR, PAYLOAD_DIR])

if __name__ == '__main__':
    main()