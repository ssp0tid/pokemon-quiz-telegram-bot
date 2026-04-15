import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import (
    KeyboardButton,
    KeyboardButtonRow,
    ReplyKeyboardMarkup,
    ReplyKeyboardHide,
)

from database import (
    init_db,
    reset_daily_leaderboard,
    reset_weekly_leaderboard,
    get_or_create_user,
    get_top_players,
    get_user_stats,
    get_user_rank,
)
from categories import get_category_list, get_category_by_id
from questions import get_question_count
from quiz import QuizGame

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

if not API_ID or not API_HASH:
    print("❌ TELEGRAM_API_ID and TELEGRAM_API_HASH are required!")
    print("Get them from https://my.telegram.org")
    exit(1)

active_games = {}


def build_category_keyboard():
    categories = get_category_list()
    buttons = []
    for cat in categories:
        btn_text = f"{cat['emoji']} {cat['name']}"
        buttons.append(KeyboardButton(text=btn_text))

    buttons.append(KeyboardButton(text="🎲 Random Mix"))
    buttons.append(KeyboardButton(text="❌ Cancel"))

    rows = [KeyboardButtonRow([btn]) for btn in buttons[:-2]]
    rows.append(KeyboardButtonRow([buttons[-2], buttons[-1]]))

    return ReplyKeyboardMarkup(rows, resize=True)


def get_selected_category(text):
    if text in ["🎲 Random Mix", "❌ Cancel"]:
        return text
    for cat in get_category_list():
        if text == f"{cat['emoji']} {cat['name']}":
            return cat["id"]
    return None


async def cleanup_game(user_id):
    if user_id in active_games:
        del active_games[user_id]


async def main():
    init_db()
    reset_daily_leaderboard()
    reset_weekly_leaderboard()

    if BOT_TOKEN:
        client = TelegramClient("bot", API_ID, API_HASH)
        await client.start(bot_token=BOT_TOKEN)
    else:
        client = TelegramClient("user_session", API_ID, API_HASH)
        await client.start()

    print("🎮 Pokemon Quiz Bot started!")
    print(f"⏱️ Question timeout: {os.getenv('QUIZ_QUESTION_TIMEOUT', 30)}s")
    print(f"📝 Questions per session: {os.getenv('QUIZ_QUESTIONS_PER_SESSION', 10)}")
    print(f"💡 Hints allowed: {os.getenv('QUIZ_HINTS_ALLOWED', 2)}")

    @client.on(events.NewMessage(pattern="/start"))
    async def handle_start(event):
        user = event.sender
        get_or_create_user(user.id, getattr(user, "username", None), user.first_name)

        await event.reply(
            "🎮 *Welcome to Pokemon Quiz Bot!*\n\n"
            "I'm here to test your Pokemon knowledge! 🐾\n\n"
            "*Available Commands:*\n"
            "• /quiz - Start a quiz\n"
            "• /categories - View quiz categories\n"
            "• /stats - Your personal stats\n"
            "• /leaderboard - Global rankings\n"
            "• /daily - Today's top players\n"
            "• /weekly - This week's top players\n"
            "• /help - How to play\n\n"
            "Use /quiz to start your Pokemon adventure!",
            parse_mode="md",
        )

    @client.on(events.NewMessage(pattern="/help"))
    async def handle_help(event):
        await event.reply(
            "📖 *How to Play*\n\n"
            "1️⃣ Use /quiz to start a quiz\n"
            "2️⃣ Choose a category\n"
            "3️⃣ Tap answer on reply keyboard\n"
            "4️⃣ Answer quickly for bonus points!\n"
            "5️⃣ Use /hint if you're stuck\n\n"
            "🎯 *Scoring:*\n"
            "• Correct: 10 points\n"
            "• Time bonus: +5 points (<15s)\n\n"
            "Good luck, Trainer! 🌟",
            parse_mode="md",
        )

    @client.on(events.NewMessage(pattern="/quiz"))
    async def handle_quiz(event):
        user_id = event.sender.id

        if user_id in active_games:
            await event.reply(
                "⚠️ You already have an active quiz!\nUse /stop to cancel.",
                parse_mode="md",
            )
            return

        keyboard = build_category_keyboard()

        await event.reply(
            "🎮 *Select a Category*\n\nChoose your Pokemon quiz category:",
            buttons=keyboard,
            parse_mode="md",
        )

    @client.on(events.NewMessage(pattern="/categories"))
    async def handle_categories(event):
        categories = get_category_list()
        text = "📚 *Available Categories*\n\n"

        for cat in categories:
            count = get_question_count(cat["id"])
            text += f"{cat['emoji']} *{cat['name']}*\n"
            text += f"   {cat['description']}\n"
            text += f"   📝 {count} questions\n\n"

        await event.reply(text, parse_mode="md")

    @client.on(events.NewMessage(pattern="/stats"))
    async def handle_stats(event):
        user_id = event.sender.id
        stats = get_user_stats(user_id)

        if not stats:
            await event.reply("❌ No stats found. Play a quiz first!")
            return

        accuracy = (
            round((stats["total_correct"] / stats["total_questions"]) * 100)
            if stats["total_questions"] > 0
            else 0
        )

        category_text = ""
        if stats["category_scores"] and len(stats["category_scores"]) > 0:
            sorted_cats = sorted(
                stats["category_scores"].items(), key=lambda x: x[1], reverse=True
            )[:5]
            category_text = "\n📊 *Top Categories:*\n"
            for cat, score in sorted_cats:
                cat_info = get_category_by_id(cat)
                cat_name = cat_info["name"] if cat_info else cat
                category_text += f"• {cat_name}: {score} pts\n"

        await event.reply(
            f"👤 *Your Stats*\n\n"
            f"🏆 Global Rank: #{stats['rank']}\n"
            f"⭐ Total Score: {stats['total_score']}\n"
            f"✅ Correct: {stats['total_correct']}/{stats['total_questions']}\n"
            f"📈 Accuracy: {accuracy}%\n"
            f"🎮 Quizzes: {stats['quizzes_taken']}\n"
            f"🔥 Current Streak: {stats['streak_current']}\n"
            f"💎 Best Streak: {stats['streak_best']}\n"
            f"💡 Hints Used: {stats['hints_used']}\n"
            f"⏱️ Time Bonus: {stats['time_bonus_earned']} pts"
            f"{category_text}",
            parse_mode="md",
        )

    @client.on(events.NewMessage(pattern="/leaderboard"))
    async def handle_leaderboard(event):
        top_players = get_top_players(10, "all")

        if not top_players:
            await event.reply("No players yet. Be the first!")
            return

        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        text = "🏆 *Global Leaderboard*\n\n"

        for i, player in enumerate(top_players):
            name = player["first_name"] or player["username"] or "Anonymous"
            text += f"{emojis[i]} {name}: {player['score']} pts\n"

        await event.reply(text, parse_mode="md")

    @client.on(events.NewMessage(pattern="/daily"))
    async def handle_daily(event):
        top_players = get_top_players(10, "daily")

        if not top_players:
            await event.reply(
                "📅 *Daily Leaderboard*\n\nNo activity today yet.\nBe the first! 🏃",
                parse_mode="md",
            )
            return

        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        text = "📅 *Today's Top Players*\n\n"

        for i, player in enumerate(top_players):
            name = player["first_name"] or player["username"] or "Anonymous"
            acc = (
                round((player["correct_answers"] / player["questions_answered"]) * 100)
                if player["questions_answered"] > 0
                else 0
            )
            text += f"{emojis[i]} {name}: {player['score']} pts ({acc}%)\n"

        await event.reply(text, parse_mode="md")

    @client.on(events.NewMessage(pattern="/weekly"))
    async def handle_weekly(event):
        top_players = get_top_players(10, "weekly")

        if not top_players:
            await event.reply(
                "📅 *Weekly Leaderboard*\n\nNo activity this week.\nStart playing! 🏃",
                parse_mode="md",
            )
            return

        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        text = "📅 *This Week's Top Players*\n\n"

        for i, player in enumerate(top_players):
            name = player["first_name"] or player["username"] or "Anonymous"
            acc = (
                round((player["correct_answers"] / player["questions_answered"]) * 100)
                if player["questions_answered"] > 0
                else 0
            )
            text += f"{emojis[i]} {name}: {player['score']} pts ({acc}%)\n"

        await event.reply(text, parse_mode="md")

    @client.on(events.NewMessage(pattern="/stop"))
    async def handle_stop(event):
        user_id = event.sender.id

        if user_id in active_games:
            game = active_games[user_id]
            game.stop()
            await event.reply("✅ Quiz stopped.", buttons=ReplyKeyboardHide())
        else:
            await event.reply("No active quiz to stop.")

    @client.on(events.NewMessage(pattern="/hint"))
    async def handle_hint(event):
        user_id = event.sender.id

        if user_id not in active_games:
            await event.reply("❌ No active quiz. Start with /quiz!")
            return

        game = active_games[user_id]
        if not game.is_active:
            await event.reply("❌ No active quiz. Start with /quiz!")
            return
        await game.use_hint()

    @client.on(
        events.NewMessage(
            func=lambda e: (
                e.message.message in ["❌ Cancel", "🎲 Random Mix"]
                or any(
                    e.message.message == f"{cat['emoji']} {cat['name']}"
                    for cat in get_category_list()
                )
            )
        )
    )
    async def handle_category_selection(event):
        user_id = event.sender.id
        text = event.message.message

        if user_id in active_games:
            return

        if text == "❌ Cancel":
            await event.reply(
                "❌ Quiz cancelled. Use /quiz to start.", buttons=ReplyKeyboardHide()
            )
            return

        category = "mixed"
        if text == "🎲 Random Mix":
            category = "mixed"
        else:
            for cat in get_category_list():
                if text == f"{cat['emoji']} {cat['name']}":
                    category = cat["id"]
                    break

        await event.reply("🎮 Starting quiz! Get ready...", buttons=ReplyKeyboardHide())

        async def on_game_end(uid):
            if uid in active_games:
                del active_games[uid]

        game = QuizGame(client, event, user_id, on_end_callback=on_game_end)
        active_games[user_id] = game
        asyncio.create_task(game.start(category))

    @client.on(events.NewMessage())
    async def handle_answer(event):
        user_id = event.sender.id

        if user_id not in active_games:
            return

        game = active_games[user_id]
        if not game.is_active:
            return

        answer = event.message.message.strip()
        if not answer:
            return

        await game.handle_answer(answer)

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
