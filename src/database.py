import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "./data/pokemon_quiz.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            total_score INTEGER DEFAULT 0,
            total_correct INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 0,
            quizzes_taken INTEGER DEFAULT 0,
            hints_used INTEGER DEFAULT 0,
            time_bonus_earned INTEGER DEFAULT 0,
            streak_current INTEGER DEFAULT 0,
            streak_best INTEGER DEFAULT 0,
            category_scores TEXT DEFAULT '{}',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_played DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            score INTEGER,
            date DATE,
            questions_answered INTEGER,
            correct_answers INTEGER,
            UNIQUE(user_id, date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard_weekly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            score INTEGER,
            week_start DATE,
            questions_answered INTEGER,
            correct_answers INTEGER,
            UNIQUE(user_id, week_start)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            total_score INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 0,
            hints_used INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def get_or_create_user(user_id, username, first_name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = COALESCE(excluded.username, users.username),
            first_name = COALESCE(excluded.first_name, users.first_name)
    """,
        (user_id, username, first_name),
    )
    conn.commit()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = dict(cursor.fetchone())
    conn.close()
    return user


def update_after_question(user_id, correct, points, time_bonus=0, hint_used=False):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE users SET
            total_score = total_score + ?,
            total_correct = total_correct + ?,
            total_questions = total_questions + 1,
            hints_used = hints_used + ?,
            time_bonus_earned = time_bonus_earned + ?,
            last_played = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """,
        (points, 1 if correct else 0, 1 if hint_used else 0, time_bonus, user_id),
    )
    conn.commit()
    conn.close()


def update_streak(user_id, correct):
    conn = get_db()
    cursor = conn.cursor()
    if correct:
        cursor.execute(
            """
            UPDATE users SET
                streak_current = streak_current + 1,
                streak_best = MAX(streak_best, streak_current + 1)
            WHERE user_id = ?
        """,
            (user_id,),
        )
    else:
        cursor.execute(
            "UPDATE users SET streak_current = 0 WHERE user_id = ?", (user_id,)
        )
    conn.commit()
    conn.close()


def get_top_players(limit=10, timeframe="all"):
    conn = get_db()
    cursor = conn.cursor()

    if timeframe == "daily":
        cursor.execute(
            """
            SELECT u.user_id, u.username, u.first_name, ls.score, ls.questions_answered, ls.correct_answers
            FROM leaderboard_daily ls
            JOIN users u ON u.user_id = ls.user_id
            WHERE ls.date = date('now')
            ORDER BY ls.score DESC
            LIMIT ?
        """,
            (limit,),
        )
    elif timeframe == "weekly":
        cursor.execute(
            """
            SELECT u.user_id, u.username, u.first_name, ls.score, ls.questions_answered, ls.correct_answers
            FROM leaderboard_weekly ls
            JOIN users u ON u.user_id = ls.user_id
            WHERE ls.week_start = date('now', 'weekday 0', '-6 days')
            ORDER BY ls.score DESC
            LIMIT ?
        """,
            (limit,),
        )
    else:
        cursor.execute(
            """
            SELECT user_id, username, first_name, total_score as score, total_correct, total_questions
            FROM users
            ORDER BY total_score DESC
            LIMIT ?
        """,
            (limit,),
        )

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_user_rank(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT total_score FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return None
    cursor.execute(
        "SELECT COUNT(*) + 1 as rank FROM users WHERE total_score > ?",
        (user["total_score"],),
    )
    rank = cursor.fetchone()["rank"]
    conn.close()
    return rank


def get_user_stats(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return None
    user_dict = dict(user)
    user_dict["rank"] = get_user_rank(user_id)
    user_dict["category_scores"] = json.loads(user_dict.get("category_scores", "{}"))
    conn.close()
    return user_dict


def update_category_score(user_id, category, points):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT category_scores FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    scores = json.loads(row["category_scores"]) if row else {}
    scores[category] = scores.get(category, 0) + points
    cursor.execute(
        "UPDATE users SET category_scores = ? WHERE user_id = ?",
        (json.dumps(scores), user_id),
    )
    conn.commit()
    conn.close()


def update_daily_score(user_id, score, questions, correct):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO leaderboard_daily (user_id, score, date, questions_answered, correct_answers)
        VALUES (?, ?, date('now'), ?, ?)
        ON CONFLICT(user_id, date) DO UPDATE SET
            score = leaderboard_daily.score + excluded.score,
            questions_answered = leaderboard_daily.questions_answered + excluded.questions_answered,
            correct_answers = leaderboard_daily.correct_answers + excluded.correct_answers
    """,
        (user_id, score, questions, correct),
    )
    conn.commit()
    conn.close()


def update_weekly_score(user_id, score, questions, correct):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT date('now', 'weekday 0', '-6 days') as week")
    week = cursor.fetchone()["week"]
    cursor.execute(
        """
        INSERT INTO leaderboard_weekly (user_id, score, week_start, questions_answered, correct_answers)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, week_start) DO UPDATE SET
            score = leaderboard_weekly.score + excluded.score,
            questions_answered = leaderboard_weekly.questions_answered + excluded.questions_answered,
            correct_answers = leaderboard_weekly.correct_answers + excluded.correct_answers
    """,
        (user_id, score, week, questions, correct),
    )
    conn.commit()
    conn.close()


def create_game_session(user_id, category):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO game_sessions (user_id, category) VALUES (?, ?)",
        (user_id, category),
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def update_game_session(session_id, score, correct, hints_used):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE game_sessions SET
            total_score = total_score + ?,
            correct_answers = correct_answers + ?,
            total_questions = total_questions + 1,
            hints_used = hints_used + ?
        WHERE session_id = ?
    """,
        (score, 1 if correct else 0, 1 if hints_used else 0, session_id),
    )
    conn.commit()
    conn.close()


def complete_game_session(session_id, score, correct, total, hints):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE game_sessions SET
            total_score = ?,
            correct_answers = ?,
            total_questions = ?,
            hints_used = ?,
            completed_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
    """,
        (score, correct, total, hints, session_id),
    )
    conn.commit()
    conn.close()


def reset_daily_leaderboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leaderboard_daily WHERE date < date('now')")
    conn.commit()
    conn.close()


def reset_weekly_leaderboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM leaderboard_weekly WHERE week_start < date('now', 'weekday 0', '-6 days')"
    )
    conn.commit()
    conn.close()
