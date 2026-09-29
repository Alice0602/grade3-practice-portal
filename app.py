import os
import sqlite3
import json
import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, send_file

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'learning_mastery.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                week TEXT NOT NULL,
                subject TEXT NOT NULL,
                score INTEGER NOT NULL,
                max_score INTEGER NOT NULL,
                percentage REAL NOT NULL,
                tab_switches INTEGER DEFAULT 0,
                duration_seconds INTEGER DEFAULT 0,
                status TEXT DEFAULT 'COMPLETED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vocab_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                word TEXT NOT NULL,
                week TEXT NOT NULL,
                times_correct INTEGER DEFAULT 0,
                times_wrong INTEGER DEFAULT 0,
                last_practiced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_name, word)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS mistakes_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                week TEXT NOT NULL,
                question_or_word TEXT NOT NULL,
                user_answer TEXT,
                correct_answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

# ==================== COMPREHENSIVE CURRICULUM DATA ====================
VOCABULARY_BANK = {
    "week1": [
        {"word": "listen", "meaning": "pay attention to what the teacher says", "colloc": "Listen carefully in class", "audio": "listen. Listen carefully in class.", "type": "rule", "emoji": "👂"},
        {"word": "raise your hand", "meaning": "put hand up before speaking", "colloc": "Raise your hand to ask a question", "audio": "raise your hand. Raise your hand to speak.", "type": "rule", "emoji": "🙋"},
        {"word": "be nice", "meaning": "be kind and friendly to everyone", "colloc": "Always be nice to your friends", "audio": "be nice. Be kind and friendly.", "type": "rule", "emoji": "🤝"},
        {"word": "try your best", "meaning": "work hard and do not give up", "colloc": "Try your best every day", "audio": "try your best. Work hard and never give up.", "type": "rule", "emoji": "⭐"},
        {"word": "noun", "meaning": "a person, place, animal, or thing", "colloc": "A cat and a school are nouns", "audio": "noun. A person, place, animal, or thing.", "type": "grammar", "emoji": "📦"},
        {"word": "verb", "meaning": "an action word or what we do", "colloc": "Run, jump, and eat are verbs", "audio": "verb. An action word.", "type": "grammar", "emoji": "🏃"},
        {"word": "adjective", "meaning": "a word that describes a noun", "colloc": "A big red balloon", "audio": "adjective. A word that describes a noun.", "type": "grammar", "emoji": "🎨"},
        {"word": "light", "meaning": "energy we use to see the world", "colloc": "We need light to see", "audio": "light. Energy we use to see the world.", "type": "science", "emoji": "💡"},
        {"word": "darkness", "meaning": "when there is no light", "colloc": "It is dark at night", "audio": "darkness. It is dark when there is no light.", "type": "science", "emoji": "🌑"},
        {"word": "light source", "meaning": "something that makes its own light", "colloc": "The Sun and torch are light sources", "audio": "light source. Something that makes its own light.", "type": "science", "emoji": "☀️"},
        {"word": "tally chart", "meaning": "marks used to count data in groups of 5", "colloc": "Count tallies in groups of five", "audio": "tally chart. Marks used to count in groups of five.", "type": "maths", "emoji": "📊"}
    ],
    "week2": [
        {"word": "statement", "meaning": "tells something, ends with a full stop", "colloc": "The cat is cute.", "audio": "statement. Tells something and ends with a full stop.", "type": "grammar", "emoji": "📝"},
        {"word": "question", "meaning": "asks something, ends with a question mark", "colloc": "Is the cat cute?", "audio": "question. Asks something and ends with a question mark.", "type": "grammar", "emoji": "❓"},
        {"word": "walked", "meaning": "past form of walk (regular -ed)", "colloc": "She walked to school yesterday", "audio": "walked. Past simple of walk.", "type": "grammar", "emoji": "🚶"},
        {"word": "played", "meaning": "past form of play (regular -ed)", "colloc": "They played football in the park", "audio": "played. Past simple of play.", "type": "grammar", "emoji": "⚽"},
        {"word": "shouted", "meaning": "past form of shout (regular -ed)", "colloc": "He shouted for help", "audio": "shouted. Past simple of shout.", "type": "grammar", "emoji": "📢"},
        {"word": "climbed", "meaning": "past form of climb (regular -ed)", "colloc": "The monkey climbed the tall tree", "audio": "climbed. Past simple of climb.", "type": "grammar", "emoji": "🧗"},
        {"word": "ran", "meaning": "past form of run (irregular)", "colloc": "Billy ran to the window", "audio": "ran. Past simple of run.", "type": "grammar", "emoji": "🏃"},
        {"word": "saw", "meaning": "past form of see (irregular)", "colloc": "We saw blue smoke", "audio": "saw. Past simple of see.", "type": "grammar", "emoji": "👀"},
        {"word": "ate", "meaning": "past form of eat (irregular)", "colloc": "He ate a delicious apple", "audio": "ate. Past simple of eat.", "type": "grammar", "emoji": "🍎"},
        {"word": "went", "meaning": "past form of go (irregular)", "colloc": "They went to the beach", "audio": "went. Past simple of go.", "type": "grammar", "emoji": "🏖️"},
        {"word": "transparent", "meaning": "all light passes through, see clearly", "colloc": "Clear glass is transparent", "audio": "transparent. All light passes through.", "type": "science", "emoji": "🪟"},
        {"word": "translucent", "meaning": "some light passes through, see partially", "colloc": "Sunglasses are translucent", "audio": "translucent. Some light passes through.", "type": "science", "emoji": "🕶️"},
        {"word": "opaque", "meaning": "no light passes through, blocks light", "colloc": "Wood and stone are opaque", "audio": "opaque. Blocks light completely.", "type": "science", "emoji": "🧱"},
        {"word": "straight line", "meaning": "light always travels straight and cannot bend", "colloc": "Light travels in a straight line", "audio": "straight line. Light travels in a straight line.", "type": "science", "emoji": "📏"},
        {"word": "greater than", "meaning": "larger number (>)", "colloc": "400 is greater than 300", "audio": "greater than. The crocodile eats the bigger number.", "type": "maths", "emoji": "🐊"}
    ],
    "week3": [
        {"word": "telescope", "meaning": "instrument to look at stars and planets", "colloc": "Look at the moon through a telescope", "audio": "telescope. Instrument to look at space.", "type": "story", "emoji": "🔭"},
        {"word": "professor", "meaning": "a smart teacher or scientist", "colloc": "Professor Inkspot invented a machine", "audio": "professor. A scientist or teacher.", "type": "story", "emoji": "👨‍🔬"},
        {"word": "shed", "meaning": "a small wooden building in a garden", "colloc": "Billy ran to the professor's shed", "audio": "shed. A small building in a garden.", "type": "story", "emoji": "🛖"},
        {"word": "turn a dial", "meaning": "rotate a round knob with numbers", "colloc": "We turn a dial on the machine", "audio": "turn a dial. We turn a dial.", "type": "colloc", "emoji": "🎛️"},
        {"word": "push a button", "meaning": "press down a button with finger", "colloc": "We push a red button", "audio": "push a button. We push a button.", "type": "colloc", "emoji": "🔴"},
        {"word": "press a switch", "meaning": "toggle a switch for power", "colloc": "We press a switch under the screen", "audio": "press a switch. We press a switch.", "type": "colloc", "emoji": "⚡"},
        {"word": "pull a handle", "meaning": "move a handle down or toward you", "colloc": "We pull a handle beside the screen", "audio": "pull a handle. We pull a handle.", "type": "colloc", "emoji": "🕹️"},
        {"word": "incisors", "meaning": "8 chisel-like front teeth to slice food", "colloc": "Incisors slice into apples", "audio": "incisors. Front teeth used for slicing.", "type": "science", "emoji": "🦷"},
        {"word": "canines", "meaning": "4 pointed teeth to tear tough food", "colloc": "Canines tear meat", "audio": "canines. Pointed teeth used for tearing.", "type": "science", "emoji": "🧛"},
        {"word": "premolars", "meaning": "8 teeth with cusps to chew and crush", "colloc": "Premolars chew and crush food", "audio": "premolars. Teeth used for chewing and crushing.", "type": "science", "emoji": "🔨"},
        {"word": "molars", "meaning": "12 largest teeth at back to grind food", "colloc": "Molars grind food into fine pieces", "audio": "molars. Largest teeth used for grinding.", "type": "science", "emoji": "🪨"},
        {"word": "milk teeth", "meaning": "20 baby teeth in children under six", "colloc": "Children under six have 20 milk teeth", "audio": "milk teeth. Twenty teeth in young children.", "type": "science", "emoji": "👶"},
        {"word": "permanent teeth", "meaning": "32 adult teeth that last a lifetime", "colloc": "Adults have 32 permanent teeth", "audio": "permanent teeth. Thirty-two adult teeth.", "type": "science", "emoji": "🧑"},
        {"word": "place value", "meaning": "value of digit based on position (H, T, O)", "colloc": "Hundreds, Tens, and Ones", "audio": "place value. Hundreds, Tens, and Ones.", "type": "maths", "emoji": "🧱"},
        {"word": "expanded form", "meaning": "writing number as sum of place values", "colloc": "500 + 60 + 9 = 569", "audio": "expanded form. Five hundred plus sixty plus nine.", "type": "maths", "emoji": "➕"}
    ]
}

# ==================== ROUTES ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/practice')
def practice():
    week = request.args.get('week', 'week3')
    mode = request.args.get('mode', 'vocab')
    student = request.args.get('student', 'Student')
    return render_template('practice.html', week=week, mode=mode, student=student)

@app.route('/api/vocab_bank')
def get_vocab_bank():
    week = request.args.get('week', 'all')
    if week == 'all':
        all_words = []
        for w_key in VOCABULARY_BANK:
            for item in VOCABULARY_BANK[w_key]:
                item_copy = dict(item)
                item_copy['week'] = w_key
                all_words.append(item_copy)
        return jsonify(all_words)
    else:
        words = VOCABULARY_BANK.get(week, [])
        for item in words:
            item['week'] = week
        return jsonify(words)

@app.route('/api/submit_attempt', methods=['POST'])
def submit_attempt():
    data = request.json or {}
    student_name = data.get('student_name', 'Student').strip()
    week = data.get('week', 'week3')
    subject = data.get('subject', 'Vocabulary & Exercises')
    score = int(data.get('score', 0))
    max_score = int(data.get('max_score', 100))
    percentage = round((score / max_score) * 100, 1) if max_score > 0 else 0
    tab_switches = int(data.get('tab_switches', 0))
    duration_seconds = int(data.get('duration_seconds', 0))
    status = data.get('status', 'COMPLETED')
    mistakes = data.get('mistakes', [])

    with get_db() as conn:
        # Register or update student
        conn.execute('INSERT OR IGNORE INTO students (name) VALUES (?)', (student_name,))
        
        # Insert test attempt
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO test_attempts (student_name, week, subject, score, max_score, percentage, tab_switches, duration_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_name, week, subject, score, max_score, percentage, tab_switches, duration_seconds, status))
        attempt_id = cur.lastrowid

        # Insert mistakes log
        for m in mistakes:
            conn.execute('''
                INSERT INTO mistakes_log (student_name, week, question_or_word, user_answer, correct_answer)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_name, week, m.get('item', ''), m.get('user_answer', ''), m.get('correct_answer', '')))

        conn.commit()

    return jsonify({"success": True, "attempt_id": attempt_id, "percentage": percentage})

@app.route('/api/record_vocab', methods=['POST'])
def record_vocab():
    data = request.json or {}
    student_name = data.get('student_name', 'Student').strip()
    word = data.get('word', '').strip().lower()
    week = data.get('week', 'week3')
    is_correct = bool(data.get('is_correct', False))

    if not word:
        return jsonify({"error": "No word"}), 400

    with get_db() as conn:
        conn.execute('INSERT OR IGNORE INTO students (name) VALUES (?)', (student_name,))
        
        # Check existing stats
        row = conn.execute('SELECT * FROM vocab_stats WHERE student_name = ? AND word = ?', (student_name, word)).fetchone()
        if row:
            if is_correct:
                conn.execute('''
                    UPDATE vocab_stats 
                    SET times_correct = times_correct + 1, last_practiced = CURRENT_TIMESTAMP
                    WHERE student_name = ? AND word = ?
                ''', (student_name, word))
            else:
                conn.execute('''
                    UPDATE vocab_stats 
                    SET times_wrong = times_wrong + 1, last_practiced = CURRENT_TIMESTAMP
                    WHERE student_name = ? AND word = ?
                ''', (student_name, word))
        else:
            conn.execute('''
                INSERT INTO vocab_stats (student_name, word, week, times_correct, times_wrong)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_name, word, week, 1 if is_correct else 0, 0 if is_correct else 1))

        conn.commit()

    return jsonify({"success": True})

# ==================== TEACHER DASHBOARD ====================
@app.route('/teacher')
def teacher_dashboard():
    return render_template('teacher.html')

@app.route('/api/teacher_data')
def get_teacher_data():
    with get_db() as conn:
        # 1. Total statistics
        total_attempts = conn.execute('SELECT COUNT(*) FROM test_attempts').fetchone()[0]
        avg_score = conn.execute('SELECT AVG(percentage) FROM test_attempts').fetchone()[0] or 0
        total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]

        # 2. Recent attempts
        attempts_rows = conn.execute('''
            SELECT id, student_name, week, subject, score, max_score, percentage, tab_switches, duration_seconds, status, created_at
            FROM test_attempts
            ORDER BY id DESC
            LIMIT 50
        ''').fetchall()
        attempts = [dict(r) for r in attempts_rows]

        # 3. High-risk Weak Words (Top words students fail repeatedly)
        weak_words_rows = conn.execute('''
            SELECT word, week, SUM(times_wrong) as total_wrong, SUM(times_correct) as total_correct
            FROM vocab_stats
            GROUP BY word
            HAVING total_wrong > 0
            ORDER BY total_wrong DESC
            LIMIT 15
        ''').fetchall()
        weak_words = [dict(r) for r in weak_words_rows]

        # 4. Student leaderboard / summaries
        student_rows = conn.execute('''
            SELECT student_name, COUNT(*) as tests_taken, AVG(percentage) as avg_pct, MAX(percentage) as max_pct
            FROM test_attempts
            GROUP BY student_name
            ORDER BY avg_pct DESC
        ''').fetchall()
        student_stats = [dict(r) for r in student_rows]

    return jsonify({
        "total_attempts": total_attempts,
        "avg_score": round(avg_score, 1),
        "total_students": total_students,
        "attempts": attempts,
        "weak_words": weak_words,
        "student_stats": student_stats
    })

@app.route('/teacher/export_csv')
def export_csv():
    with get_db() as conn:
        rows = conn.execute('''
            SELECT id, student_name, week, subject, score, max_score, percentage, tab_switches, duration_seconds, status, created_at
            FROM test_attempts
            ORDER BY id DESC
        ''').fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Student Name', 'Week', 'Subject', 'Score', 'Max Score', 'Percentage (%)', 'Tab Switches (Violations)', 'Duration (seconds)', 'Status', 'Date & Time'])
    for r in rows:
        writer.writerow([r['id'], r['student_name'], r['week'], r['subject'], r['score'], r['max_score'], r['percentage'], r['tab_switches'], r['duration_seconds'], r['status'], r['created_at']])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=student_attempts_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 GRADE 3 LEARNING MASTERY & DATABASE PORTAL")
    print("Teacher Dashboard URL: http://localhost:5000/teacher")
    print("Student Practice URL:  http://localhost:5000/")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)
