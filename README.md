# Task Manager Bot

This is a Telegram bot that helps you manage tasks and deadlines. It uses MongoDB as a database to store tasks and related information.

## 🚀 Launch with Docker

### 1. Clone the repository
```bash
git clone https://github.com/CrDem/task-manager-bot.git
cd task-manager-bot
```

### 2. Create a .env file
In the root directory, create a .env file and add your bot token:
```bash
TOKEN=your_telegram_bot_token
```

### 3. Launch the containers
Run the following command to build and start the Docker containers:
```bash
docker-compose up --build -d
```
**To stop the containers, run:** docker-compose down

## Launch for Windows

### 1. Install MongoDB

- Go to [MongoDB Community Downloads](https://www.mongodb.com/try/download/community) and download the latest version of MongoDB for Windows.
- Install MongoDB by following the instructions on the website.
- Start MongoDB by running `mongod` in the command line (you may need administrator privileges to start the service).

### 2. Install Erlang
RabbitMQ requires Erlang to run. Download and install Erlang:
- Go to the official Erlang website: [https://www.erlang.org/downloads](https://www.erlang.org/downloads)
- Download the installer for Windows.
- Run the installer and follow the instructions.

### 3. Install RabbitMQ
- Download the RabbitMQ installer from the official website: [https://www.rabbitmq.com/install-windows.html](https://www.rabbitmq.com/install-windows.html)
- Run the installer and follow the instructions.

### 4. Start RabbitMQ
- Open **Command Prompt (cmd)** as Administrator.
- Navigate to the `sbin` folder:
   ```sh
   cd "C:\Program Files\RabbitMQ Server\rabbitmq_server-<version>\sbin"
   ```
- Start the server manually:
   ```sh
   rabbitmq-server.bat
   ```

### 5. Clone the repository

Clone the bot repository to your local machine:
```bash
git clone https://github.com/CrDem/task-manager-bot.git
```

### 6. Create a `.env` file with your bot token

- In the root directory of the cloned project, create a file named `.env`.
- Inside the `.env` file, add your Telegram bot token in the following format:
```env
TOKEN=your_telegram_bot_token
```
Replace `your_telegram_bot_token` with the actual token from [BotFather](https://core.telegram.org/bots#botfather).

### 7. Set up a virtual environment

- Open a command prompt or PowerShell in the project directory.
- Create a virtual environment by running the following command:
```bash
python -m venv venv
```

### 8. Activate the virtual environment

Activate the virtual environment to isolate the project dependencies:
- In **PowerShell**:
```bash
.\venv\Scripts\Activate
```
- In **Command Prompt**:
```bash
venv\Scripts\activate
```

### 9. Install dependencies
Install the dependencies:
```bash
pip install -r requirements.txt
```
or manually:
```bash
pip install aiogram pymongo python-dotenv celery nest_asyncio
```

### 10. Run Celery with RabbitMQ
In terminal 1:
```bash
celery -A bot.notification beat --loglevel=info 
```
In terminal 2:
```bash
celery -A bot.notification worker --loglevel=info --pool=solo
```

> **Important:** The `--pool=solo` flag is required on Windows.

### 11. Run the bot
In terminal 3:
```bash
python main.py
```
