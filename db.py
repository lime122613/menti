"""
db.py - SQLite 데이터베이스 관리 모듈
"""

import sqlite3
import json
import threading
import random
import string
from datetime import datetime

# 동시 쓰기 충돌 방지를 위한 Lock
_lock = threading.Lock()
DB_PATH = "responses.db"


def get_connection():
    """DB 연결 반환 (thread-safe)"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """테이블 초기화"""
    with _lock:
        conn = get_connection()
        c = conn.cursor()

        # 질문 테이블
        c.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL,  -- 'multiple' | 'short' | 'wordcloud' | 'slider'
                options TEXT,                 -- JSON 배열 (객관식 선택지)
                slider_min INTEGER DEFAULT 0,
                slider_max INTEGER DEFAULT 100,
                is_active INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 응답 테이블
        c.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_code TEXT NOT NULL,
                user_id TEXT NOT NULL,
                answer TEXT NOT NULL,
                submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(question_code, user_id)
            )
        """)

        conn.commit()
        conn.close()


def generate_code(length=6):
    """6자리 참여 코드 생성"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ──────────────────────────────────────────
# 질문 CRUD
# ──────────────────────────────────────────

def create_question(question_text, question_type, options=None,
                    slider_min=0, slider_max=100):
    """새 질문 생성 및 코드 반환"""
    code = generate_code()
    options_json = json.dumps(options, ensure_ascii=False) if options else None

    with _lock:
        conn = get_connection()
        try:
            conn.execute("""
                INSERT INTO questions (code, question_text, question_type, options, slider_min, slider_max)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (code, question_text, question_type, options_json, slider_min, slider_max))
            conn.commit()
        finally:
            conn.close()
    return code


def get_question_by_code(code):
    """코드로 질문 조회"""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM questions WHERE code = ?", (code,)
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d["options"]:
            d["options"] = json.loads(d["options"])
        return d
    return None


def get_all_questions():
    """모든 질문 목록 조회"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM questions ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        if d["options"]:
            d["options"] = json.loads(d["options"])
        result.append(d)
    return result


def get_active_question():
    """현재 활성화된 질문 조회"""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM questions WHERE is_active = 1 LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d["options"]:
            d["options"] = json.loads(d["options"])
        return d
    return None


def set_active_question(code):
    """특정 질문 활성화 (나머지 비활성화)"""
    with _lock:
        conn = get_connection()
        conn.execute("UPDATE questions SET is_active = 0")
        if code:
            conn.execute(
                "UPDATE questions SET is_active = 1 WHERE code = ?", (code,)
            )
        conn.commit()
        conn.close()


def delete_question(code):
    """질문 및 해당 응답 삭제"""
    with _lock:
        conn = get_connection()
        conn.execute("DELETE FROM responses WHERE question_code = ?", (code,))
        conn.execute("DELETE FROM questions WHERE code = ?", (code,))
        conn.commit()
        conn.close()


# ──────────────────────────────────────────
# 응답 CRUD
# ──────────────────────────────────────────

def submit_response(question_code, user_id, answer):
    """응답 제출 (중복 시 업데이트)"""
    with _lock:
        conn = get_connection()
        try:
            conn.execute("""
                INSERT INTO responses (question_code, user_id, answer)
                VALUES (?, ?, ?)
                ON CONFLICT(question_code, user_id)
                DO UPDATE SET answer = excluded.answer,
                              submitted_at = CURRENT_TIMESTAMP
            """, (question_code, user_id, answer))
            conn.commit()
            return True
        except Exception as e:
            print(f"응답 저장 오류: {e}")
            return False
        finally:
            conn.close()


def get_responses(question_code):
    """특정 질문의 모든 응답 조회"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT answer, submitted_at FROM responses WHERE question_code = ?",
        (question_code,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_response_count(question_code):
    """응답 수 조회"""
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM responses WHERE question_code = ?",
        (question_code,)
    ).fetchone()[0]
    conn.close()
    return count


def clear_responses(question_code):
    """특정 질문의 응답 초기화"""
    with _lock:
        conn = get_connection()
        conn.execute(
            "DELETE FROM responses WHERE question_code = ?", (question_code,)
        )
        conn.commit()
        conn.close()


def has_user_responded(question_code, user_id):
    """사용자가 이미 응답했는지 확인"""
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM responses WHERE question_code = ? AND user_id = ?",
        (question_code, user_id)
    ).fetchone()[0]
    conn.close()
    return count > 0
