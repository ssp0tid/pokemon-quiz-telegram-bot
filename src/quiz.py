import asyncio
import time as time_module
from telethon.tl.types import KeyboardButton, KeyboardButtonRow, ReplyKeyboardMarkup
from questions import get_questions_for_category, get_random_questions
from categories import get_category_by_id
from hints import HintSystem
import database
from database import (
    get_or_create_user,
    update_after_question,
    update_streak,
    get_user_stats,
    get_user_rank,
    update_category_score,
    update_daily_score,
    update_weekly_score,
    create_game_session,
    update_game_session,
    complete_game_session,
)


class QuizGame:
    def __init__(self, client, event, user_id, on_end_callback=None):
        self.client = client
        self.event = event
        self.user_id = user_id
        self.on_end_callback = on_end_callback
        self.questions = []
        self.current_question_index = 0
        self.score = 0
        self.correct_answers = 0
        self.hints_used = 0
        self.timer_task = None
        self.answer_received = asyncio.Event()
        self.hint_system = HintSystem(2)
        self.question_start_time = None
        self.session_id = None
        self.category = "mixed"
        self.total_questions = 10
        self.question_timeout = 30
        self.points_correct = 10
        self.points_time_bonus = 5
        self.is_active = False
        self._cleanup_done = False

    async def start(self, category="mixed"):
        get_or_create_user(self.user_id, None, None)

        self.category = category
        self.session_id = create_game_session(self.user_id, category)

        if category == "mixed":
            self.questions = get_random_questions(self.total_questions)
        else:
            self.questions = get_questions_for_category(category, self.total_questions)

        self.is_active = True
        self.score = 0
        self.correct_answers = 0
        self.hints_used = 0
        self.current_question_index = 0
        self.hint_system.reset(self.session_id)

        category_info = get_category_by_id(category)
        category_name = category_info["name"] if category_info else "Mixed"

        await self.reply(
            f"🎮 *Pokemon Quiz Started!*\n\n"
            f"📚 Category: {category_name}\n"
            f"📝 Questions: {len(self.questions)}\n"
            f"⏱️ Time per question: {self.question_timeout}s\n"
            f"💡 Hints available: {self.hint_system.max_hints}\n\n"
            f"Get ready! Starting in 3 seconds...",
            parse_mode="md",
        )

        await asyncio.sleep(3)
        await self.show_question()

    async def show_question(self):
        if not self.is_active or self.current_question_index >= len(self.questions):
            await self._cleanup()
            return

        question = self.questions[self.current_question_index]
        self.question_start_time = time_module.time()
        self.answer_received.clear()

        available_hints = self.hint_system.get_available_hints(self.session_id)
        question_number = self.current_question_index + 1
        total = len(self.questions)

        options_text = "\n".join([f"{opt[0]}) {opt[1]}" for opt in question["options"]])
        hint_text = f"\n\n💡 Use /hint for help!" if available_hints > 0 else ""

        message = (
            f"📋 *Question {question_number}/{total}*\n\n"
            f"❓ {question['question']}\n\n"
            f"{options_text}"
            f"{hint_text}"
        )

        keyboard = ReplyKeyboardMarkup(
            [
                KeyboardButtonRow([KeyboardButton(text=opt[1])])
                for opt in question["options"]
            ],
            resize=True,
        )

        sent = await self.client.send_message(
            self.event.chat_id, message, buttons=keyboard, parse_mode="md"
        )

        self.start_timer()

    def start_timer(self):
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
        self.timer_task = asyncio.create_task(self._timer_loop())

    async def _timer_loop(self):
        try:
            await asyncio.sleep(self.question_timeout)
            if self.is_active and not self.answer_received.is_set():
                await self._handle_timeout()
        except asyncio.CancelledError:
            pass

    async def _handle_timeout(self):
        if not self.is_active:
            return

        question = self.questions[self.current_question_index]

        update_streak(self.user_id, False)

        await self.reply(
            f"⏰ *Time's up!*\n\n"
            f"The correct answer was: {question['correct_emoji']} *{question['answer']}*",
            parse_mode="md",
        )

        await asyncio.sleep(2)
        self.current_question_index += 1

        if self.current_question_index >= len(self.questions):
            await self._cleanup()
        else:
            await self.show_question()

    async def handle_answer(self, answer):
        if not self.is_active:
            return

        if self.answer_received.is_set():
            return
        self.answer_received.set()

        if self.timer_task:
            self.timer_task.cancel()

        question = self.questions[self.current_question_index]
        time_elapsed = time_module.time() - self.question_start_time
        is_correct = answer.lower().strip() == question["answer"].lower().strip()

        if is_correct:
            self.correct_answers += 1
            points = self.points_correct
            time_bonus = 0

            if time_elapsed < self.question_timeout / 2:
                time_bonus = self.points_time_bonus
                points += time_bonus

            self.score += points

            update_after_question(self.user_id, True, points, time_bonus, False)
            update_streak(self.user_id, True)
            update_category_score(self.user_id, self.category, points)
            update_game_session(self.session_id, points, True, False)
            update_daily_score(self.user_id, points, 1, 1)
            update_weekly_score(self.user_id, points, 1, 1)

            emoji = question["correct_emoji"] or "✅"
            bonus_text = f" (+{time_bonus} time bonus!)" if time_bonus > 0 else ""
            await self.reply(
                f"{emoji} *Correct!*\n\n+{points} points{bonus_text}", parse_mode="md"
            )
        else:
            update_after_question(self.user_id, False, 0, 0, False)
            update_streak(self.user_id, False)
            update_game_session(self.session_id, 0, False, False)
            update_daily_score(self.user_id, 0, 1, 0)
            update_weekly_score(self.user_id, 0, 1, 0)

            emoji = question["correct_emoji"] or "❌"
            await self.reply(
                f"❌ *Wrong!*\n\n"
                f"The correct answer was: {emoji} *{question['answer']}*",
                parse_mode="md",
            )

        await asyncio.sleep(2)
        self.current_question_index += 1

        if self.current_question_index >= len(self.questions):
            await self._cleanup()
        else:
            await self.show_question()

    async def use_hint(self):
        if not self.is_active:
            await self.reply("No active quiz to use hint on!")
            return

        question = self.questions[self.current_question_index]
        remaining = max(
            0,
            self.question_timeout - int(time_module.time() - self.question_start_time),
        )
        hint = self.hint_system.generate_hint(self.session_id, question, remaining)

        if not hint:
            await self.reply("❌ No hints remaining!")
            return

        self.hints_used += 1
        update_after_question(self.user_id, False, 0, 0, True)

        await self.reply(hint, parse_mode="md")

    async def _cleanup(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        self.is_active = False

        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None

        complete_game_session(
            self.session_id,
            self.score,
            self.correct_answers,
            len(self.questions),
            self.hints_used,
        )

        stats = get_user_stats(self.user_id)
        percentage = (
            round((self.correct_answers / len(self.questions)) * 100)
            if self.questions
            else 0
        )
        rank = get_user_rank(self.user_id)

        if percentage >= 90:
            emoji = "🏆"
        elif percentage >= 70:
            emoji = "🥈"
        elif percentage >= 50:
            emoji = "🥉"
        else:
            emoji = "🎮"

        keyboard = ReplyKeyboardMarkup(
            [
                KeyboardButtonRow([KeyboardButton(text="🎮 Play Again")]),
                KeyboardButtonRow([KeyboardButton(text="📊 My Stats")]),
            ],
            resize=True,
        )

        await self.reply(
            f"{emoji} *Quiz Complete!*\n\n"
            f"📊 *Results:*\n"
            f"• Questions: {len(self.questions)}\n"
            f"• Correct: {self.correct_answers}\n"
            f"• Score: {self.score} points\n"
            f"• Accuracy: {percentage}%\n"
            f"• Hints used: {self.hints_used}\n\n"
            f"🏅 *Your Stats:*\n"
            f"• Total Score: {stats['total_score']}\n"
            f"• Global Rank: #{rank}\n"
            f"• Current Streak: {stats['streak_current']}\n"
            f"• Best Streak: {stats['streak_best']}\n\n"
            f"Use /quiz to play again or /stats to see your detailed stats!",
            buttons=keyboard,
            parse_mode="md",
        )

        if self.on_end_callback:
            await self.on_end_callback(self.user_id)

    async def reply(self, message, parse_mode="md"):
        await self.client.send_message(
            self.event.chat_id, message, parse_mode=parse_mode
        )

    def stop(self):
        self.is_active = False
        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None
        if self.on_end_callback:
            asyncio.create_task(self.on_end_callback(self.user_id))
