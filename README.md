# Task Management Telegram Bot

A Telegram bot for managing task lists, allowing users to register, add tasks, view their task list, manage tasks, and search for tasks based on keywords or phrases.

## Features

### 1. User Registration
- The bot offers the user the option to register via the `/start` command or any other activation command.
- During registration, the user provides their name and phone number.

### 2. Add a Task
- Users can add a new task with or without tags to their task list.

### 3. View Task List
- Users can view their list of tasks at any time.

### 4. Manage Tasks
- Users can mark tasks as completed, so they will not see them again.

### 5. Search Tasks
- Users can search for tasks by keywords or phrases or/and tags.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/balconyRewrap/test_task.git
   ```

2. Navigate to the project directory:
   ```bash
   cd test_task
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (API token, database credentials, etc.) in a `.env` file:
   ```
   API_TOKEN=your_telegram_bot_token
   REDIS_HOST = your_redis_host
   REDIS_PORT = your_redis_port
   MARIADB_HOST=your_db_host
   MARIADB_USER=your_db_user
   MARIADB_PASSWORD=your_db_password
   MARIADB_DATABASE=your_db_name
   ```

## Usage

1. Start the bot by running the following command:
   ```bash
   python run_bot.py
   ```

2. Interact with the bot:
   - Use the `/start` command to register.
   - Add tasks by sending a command to the bot.
   - View your tasks or search for tasks using keywords.

## Contributing

Feel free to fork this project, submit issues, and send pull requests. If you want to improve functionality or fix bugs, please follow the contribution guidelines.

