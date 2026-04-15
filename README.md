# Pokemon Quiz Bot

A Telegram bot that tests your Pokemon knowledge with multiple categories, leaderboards, and hints.

## Features

- **10 Quiz Categories**: General Knowledge, Gen I-III, Types, Moves, Pokedex, Legendary, Evolution, and Hard Mode
- **Scoring System**: 10 points per correct answer + 5 bonus points for fast answers (<15s)
- **Hint System**: 3 hint types - eliminate wrong answers, time remaining, letter reveal
- **Leaderboards**: Global, daily, and weekly rankings
- **Streak Tracking**: Track your correct answer streaks
- **User Stats**: Personal statistics including accuracy, category breakdown, and rank
- **SQLite Database**: Persistent storage for all game data

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd pokemon-quiz-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Setup

### 1. Telegram API Credentials

1. Go to [my.telegram.org](https://my.telegram.org)
2. Login and click "API development tools"
3. Create a new application
4. Copy your `API_ID` and `API_HASH`

### 2. Bot Token (Optional)

To run as a Telegram bot (recommended):

1. Open Telegram and chat with [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow the prompts and copy the token

To run with a user account instead, leave `BOT_TOKEN` empty.

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
TELEGRAM_API_ID=12345
TELEGRAM_API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here
```

## Running the Bot

```bash
python -m src.bot
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and command overview |
| `/help` | How to play guide |
| `/quiz` | Start a new quiz (select category) |
| `/categories` | View all available quiz categories |
| `/stats` | Your personal statistics |
| `/leaderboard` | Global top 10 players |
| `/daily` | Today's top players |
| `/weekly` | This week's top players |
| `/hint` | Get a hint (during active quiz) |
| `/stop` | Stop current quiz |

## Categories

| Category | Description | Difficulty |
|----------|-------------|------------|
| 🎯 General Knowledge | Basic Pokemon facts | Mixed |
| 🟢 Generation I | Pokemon Red/Blue/Yellow (Kanto) | Easy |
| 🟡 Generation II | Pokemon Gold/Silver/Crystal (Johto) | Medium |
| 🔴 Generation III | Pokemon Ruby/Sapphire/Emerald (Hoenn) | Medium |
| ⚡ Pokemon Types | Type matchups and weaknesses | Medium |
| 💥 Moves & Attacks | Pokemon moves and abilities | Hard |
| 📖 Pokedex Numbers | Pokemon numbers and order | Hard |
| ⭐ Legendary Pokemon | Mythical and Legendary Pokemon | Medium |
| 🔄 Evolution | Evolution chains and methods | Medium |
| 🔥 Hard Mode | Expert-level trivia | Hard |
| 🎲 Random Mix | Questions from all categories | Mixed |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_API_ID` | - | Required. From my.telegram.org |
| `TELEGRAM_API_HASH` | - | Required. From my.telegram.org |
| `BOT_TOKEN` | - | Optional. Bot token from @BotFather |
| `QUIZ_QUESTION_TIMEOUT` | 30 | Seconds per question |
| `QUIZ_QUESTIONS_PER_SESSION` | 10 | Questions per quiz |
| `QUIZ_POINTS_CORRECT` | 10 | Points per correct answer |
| `QUIZ_POINTS_TIME_BONUS` | 5 | Bonus points for fast answers |
| `QUIZ_HINTS_ALLOWED` | 2 | Hints available per quiz |
| `DB_PATH` | `./data/pokemon_quiz.db` | SQLite database path |

## Project Structure

```
pokemon-quiz-bot/
├── src/
│   ├── bot.py          # Main bot logic and command handlers
│   ├── quiz.py         # Quiz game engine
│   ├── questions.py    # Question database (100+ questions)
│   ├── categories.py   # Category definitions
│   ├── hints.py        # Hint generation system
│   └── database.py     # SQLite database operations
├── data/               # SQLite database storage
├── .env.example        # Environment template
└── requirements.txt    # Python dependencies
```

## Scoring

- **Correct Answer**: 10 points
- **Time Bonus**: +5 points (if answered in <15 seconds)
- **Hint Penalty**: Using hints affects final stats tracking

## License

MIT
