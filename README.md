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
pip install aiogram pymongo python-dotenv celery nest_asyncio
```
#  Installation and Setup of RabbitMQ and Celery on Windows

## 1. Installing RabbitMQ

### Step 1: Install Erlang
RabbitMQ requires Erlang to run. Download and install Erlang:
1. Go to the official Erlang website:
   - [https://www.erlang.org/downloads](https://www.erlang.org/downloads)
2. Download the installer for Windows.
3. Run the installer and follow the instructions.

### Step 2: Install RabbitMQ
1. Download the RabbitMQ installer from the official website:
   - [https://www.rabbitmq.com/install-windows.html](https://www.rabbitmq.com/install-windows.html)
2. Run the installer and follow the instructions.

## 2. Starting RabbitMQ after installation

After installing RabbitMQ and seeing shortcuts like `RabbitMQ Service - start/stop`, you can start the server in different ways.

### Method 1: Start via GUI
1. Open **Windows Search** (Win + S).
2. Type `RabbitMQ Service - start`.
3. Click **Run as Administrator**.

To stop RabbitMQ:
- Type `RabbitMQ Service - stop` and run as Administrator.

### Method 2: Check RabbitMQ Status
To check if RabbitMQ is running:
1. Open **Command Prompt (cmd)**.
2. Navigate to the `sbin` folder of RabbitMQ:
   ```sh
   cd "C:\Program Files\RabbitMQ Server\rabbitmq_server-<version>\sbin"
   ```
3. Run the command:
   ```sh
   rabbitmqctl.bat status
   ```

If the service is running, you will see server status information.

### Method 3: Start Without Service (Manual Start)
If RabbitMQ is not installed as a service or needs to be started manually:
1. Open **Command Prompt (cmd)** as Administrator.
2. Navigate to the `sbin` folder:
   ```sh
   cd "C:\Program Files\RabbitMQ Server\rabbitmq_server-<version>\sbin"
   ```
3. Start the server manually:
   ```sh
   rabbitmq-server.bat
   ```

## 3. Running Celery Worker on Windows

### Install Dependencies
```sh
pip install celery nest_asyncio
```

### Running Celery with RabbitMQ
```sh
celery -A bot.bot worker --loglevel=info --pool=solo
```

> **Important:** The `--pool=solo` flag is required on Windows.

### 7. Run the bot

After installing all the necessary dependencies and setting up the `.env` file, you can run the bot with the following command:
```bash
python bot.py
```
