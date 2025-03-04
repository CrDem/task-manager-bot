# Task Manager Bot

This is a Telegram bot that helps you manage tasks and deadlines. It uses MongoDB as a database to store tasks and related information.

## Launch for Windows

### 1. Download MongoDB

- Go to [MongoDB Community Downloads](https://www.mongodb.com/try/download/community) and download the latest version of MongoDB for Windows.
- Install MongoDB by following the instructions on the website.
- Start MongoDB by running `mongod` in the command line (you may need administrator privileges to start the service).

### 2. Clone the repository

Clone the bot repository to your local machine:
```bash
git clone https://github.com/CrDem/task-manager-bot.git
```

### 3. Create a `.env` file with your bot token

- In the root directory of the cloned project, create a file named `.env`.
- Inside the `.env` file, add your Telegram bot token in the following format:
```env
TOKEN=your_telegram_bot_token
```
Replace `your_telegram_bot_token` with the actual token from [BotFather](https://core.telegram.org/bots#botfather).

### 4. Set up a virtual environment

- Open a command prompt or PowerShell in the project directory.
- Create a virtual environment by running the following command:
```bash
python -m venv venv
```

### 5. Activate the virtual environment

Activate the virtual environment to isolate the project dependencies:
- In **PowerShell**:
```bash
.\venv\Scripts\Activate
```
- In **Command Prompt**:
```bash
venv\Scripts\activate
```

### 6. Install dependencies

Install the required dependencies by running:
```bash
pip install -r requirements.txt
```

If the `requirements.txt` file does not exist, you can manually install the dependencies:
```bash
pip install aiogram pymongo python-dotenv
```

### 7. Run the bot

After installing all the necessary dependencies and setting up the `.env` file, you can run the bot with the following command:
```bash
python bot.py
```
