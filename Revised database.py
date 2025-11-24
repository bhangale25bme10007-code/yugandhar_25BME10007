# database.py

import sqlite3
from datetime import date, timedelta

DB_FILE = "expenses.db"

def connect_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def initialize_database():
    con = connect_db()
    cursor = con.cursor()

    # Create table for transactions if not present.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            t_date TEXT NOT NULL,
            t_type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT
        )
        """
    )

    # Create goals table to store monthly and weekly spending limits.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS goals (
            goal_type TEXT PRIMARY KEY,
            amount REAL NOT NULL
        )
        """
    )

    con.commit()
    con.close()

def insert_transaction(t_type, amount, category, t_date=None, note=""):
    if t_date is None:
        t_date = date.today().isoformat()
    con = connect_db()
    cursor = con.cursor()
    cursor.execute(
        """
        INSERT INTO transactions (t_date, t_type, category, amount, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        (t_date, t_type, category, amount, note),
    )
    con.commit()
    con.close()

def fetch_all_transactions():
    con = connect_db()
    cursor = con.cursor()
    cursor.execute(
        """
        SELECT id, t_date, t_type, category, amount, note
        FROM transactions
        ORDER BY t_date DESC, id DESC
        """
    )
    results = cursor.fetchall()
    con.close()
    return results

def fetch_summary():
    con = connect_db()
    cursor = con.cursor()
    cursor.execute("SELECT IFNULL(SUM(amount), 0) FROM transactions WHERE t_type='income'")
    total_income = cursor.fetchone()[0] or 0
    cursor.execute("SELECT IFNULL(SUM(amount), 0) FROM transactions WHERE t_type='expense'")
    total_expense = cursor.fetchone()[0] or 0
    balance = total_income - total_expense
    con.close()
    return total_income, total_expense, balance

def put_goal(goal_type, amount):
    con = connect_db()
    cursor = con.cursor()
    cursor.execute(
        """
        INSERT INTO goals (goal_type, amount)
        VALUES (?, ?)
        ON CONFLICT(goal_type) DO UPDATE SET amount=excluded.amount
        """,
        (goal_type, amount),
    )
    con.commit()
    con.close()

def fetch_goal(goal_type):
    con = connect_db()
    cursor = con.cursor()
    cursor.execute("SELECT amount FROM goals WHERE goal_type=?", (goal_type,))
    row = cursor.fetchone()
    con.close()
    return row[0] if row else None

def _date_range(goal_type):
    today = date.today()
    if goal_type == "monthly":
        start = today.replace(day=1)
        end = today
    elif goal_type == "weekly":
        start = today - timedelta(days=today.weekday())
        end = today
    else:
        start, end = today, today
    return start, end

def fetch_goal_progress(goal_type):
    goal_val = fetch_goal(goal_type)
    if goal_val is None:
        return None, 0.0, 0.0, "No goal currently set."
    start_date, end_date = _date_range(goal_type)
    con = connect_db()
    cursor = con.cursor()
    cursor.execute(
        """
        SELECT IFNULL(SUM(amount), 0)
        FROM transactions
        WHERE t_type='expense'
        AND DATE(t_date) BETWEEN DATE(?) AND DATE(?)
        """,
        (start_date.isoformat(), end_date.isoformat()),
    )
    spent = cursor.fetchone()[0] or 0.0
    con.close()

    remaining = goal_val - spent
    if remaining < 0:
        status_text = f"You have surpassed your {goal_type} budget by {abs(remaining):.2f}."
    elif remaining <= 0.2 * goal_val:
        status_text = f"Almost at your {goal_type} budget limit. Remaining: {remaining:.2f}."
    else:
        status_text = f"Within {goal_type} budget. Remaining: {remaining:.2f}."
    return goal_val, spent, remaining, status_text
