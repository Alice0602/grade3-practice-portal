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
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA busy_timeout = 5000;')
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
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
        # Classroom Rules
        {"word": "listen", "meaning": "pay attention to what the teacher says", "vietnamese": "Lắng nghe cẩn thận giáo viên và bạn bè", "mnemonic": "Dùng đôi tai 👂 tập trung lắng nghe để hiểu bài thật tốt.", "colloc": "Listen carefully in class", "colloc_vi": "Lắng nghe cẩn thận trong giờ học", "audio": "listen. Listen carefully in class.", "type": "rule", "svg_type": "listen", "emoji": "👂"},
        {"word": "raise your hand", "meaning": "put hand up before speaking", "vietnamese": "Giơ tay phát biểu trước khi nói", "mnemonic": "Muốn nói hoặc hỏi điều gì, nhớ giơ tay 🙋 xin phép trước.", "colloc": "Raise your hand to ask a question", "colloc_vi": "Giơ tay khi muốn đặt câu hỏi", "audio": "raise your hand. Raise your hand to speak.", "type": "rule", "svg_type": "raise_hand", "emoji": "🙋"},
        {"word": "be nice", "meaning": "be kind and friendly to everyone", "vietnamese": "Tử tế, thân thiện, hòa đồng với bạn bè", "mnemonic": "Luôn mỉm cười, bắt tay 🤝 và giúp đỡ bạn bè trong lớp.", "colloc": "Always be nice to your friends", "colloc_vi": "Luôn thân thiện, tốt bụng với bạn bè", "audio": "be nice. Be kind and friendly.", "type": "rule", "svg_type": "be_nice", "emoji": "🤝"},
        {"word": "try your best", "meaning": "work hard and do not give up", "vietnamese": "Cố gắng hết sức mình, không bỏ cuộc", "mnemonic": "Chăm chỉ làm bài và kiên trì ⭐ sẽ nhận được điểm thưởng cao.", "colloc": "Try your best every day", "colloc_vi": "Cố gắng hết sức mỗi ngày", "audio": "try your best. Work hard and never give up.", "type": "rule", "svg_type": "try_best", "emoji": "⭐"},
        {"word": "ask for help", "meaning": "tell the teacher when you do not understand", "vietnamese": "Hỏi xin sự giúp đỡ khi không hiểu bài", "mnemonic": "Khi gặp bài khó hoặc không hiểu, hãy mạnh dạn hỏi thầy cô ❓.", "colloc": "Ask for help when you do not understand", "colloc_vi": "Hỏi xin sự giúp đỡ khi con không hiểu", "audio": "ask for help when you do not understand.", "type": "rule", "svg_type": "ask_help", "emoji": "❓"},
        {"word": "bring your books", "meaning": "have all your books and pencils ready", "vietnamese": "Mang đầy đủ sách vở và đồ dùng học tập", "mnemonic": "Chuẩn bị sách, vở và bút chì 🎒 sẵn sàng trước khi vào lớp.", "colloc": "Bring your books and pencils to class", "colloc_vi": "Mang sách và bút chì đến lớp", "audio": "bring your books and pencils to class.", "type": "rule", "svg_type": "books", "emoji": "📚"},

        # Grammar: Nouns, Verbs, Adjectives
        {"word": "noun", "meaning": "a person, place, animal, or thing", "vietnamese": "Danh từ: chỉ Người, Nơi chốn, Động vật, Đồ vật", "mnemonic": "Mọi thứ nhìn thấy, sờ thấy hoặc gọi tên được đều là Danh từ (bác sĩ, mèo, trường học, quả chuối).", "colloc": "A doctor, cat, and school are nouns", "colloc_vi": "Bác sĩ, con mèo và trường học đều là danh từ", "audio": "noun. A person, place, animal, or thing.", "type": "grammar", "svg_type": "noun", "emoji": "📦"},
        {"word": "verb", "meaning": "an action word or what we do", "vietnamese": "Động từ: từ chỉ Hành động hoặc việc chúng ta làm", "mnemonic": "Cơ thể cử động như chạy (run), nhảy (jump), ăn (eat), ngủ (sleep) là Động từ.", "colloc": "Run, jump, and eat are verbs", "colloc_vi": "Chạy, nhảy và ăn là các động từ", "audio": "verb. An action word.", "type": "grammar", "svg_type": "verb", "emoji": "🏃"},
        {"word": "adjective", "meaning": "a word that describes a noun", "vietnamese": "Tính từ: từ miêu tả đặc điểm, màu sắc, kích thước", "mnemonic": "Màu đỏ (red), to lớn (big), vui vẻ (happy), nhanh nhẹn (fast) là Tính từ miêu tả danh từ.", "colloc": "A big red balloon", "colloc_vi": "Một quả bóng bay to màu đỏ", "audio": "adjective. A word that describes a noun.", "type": "grammar", "svg_type": "adjective", "emoji": "🎨"},
        {"word": "doctor", "meaning": "a person who helps sick people (noun)", "vietnamese": "Bác sĩ: người khám và chữa bệnh (Danh từ chỉ người)", "mnemonic": "Người mặc áo blouse trắng 👨‍⚕️ chăm sóc bệnh nhân.", "colloc": "The doctor is in the hospital", "colloc_vi": "Bác sĩ đang ở trong bệnh viện", "audio": "doctor. A person who helps sick people.", "type": "grammar", "svg_type": "person", "emoji": "👨‍⚕️"},
        {"word": "banana", "meaning": "a sweet yellow fruit (noun)", "vietnamese": "Quả chuối: loại trái cây màu vàng ngọt ngào (Danh từ chỉ vật)", "mnemonic": "Quả chuối cong cong màu vàng 🍌 rất giàu dinh dưỡng.", "colloc": "He ate a yellow banana", "colloc_vi": "Cậu ấy đã ăn một quả chuối màu vàng", "audio": "banana. A sweet yellow fruit.", "type": "grammar", "svg_type": "thing", "emoji": "🍌"},
        {"word": "shout", "meaning": "to speak very loudly with a strong voice (verb)", "vietnamese": "Hét to / La lớn tiếng (Động từ chỉ hành động)", "mnemonic": "Mở to miệng hét toáng lên 📢 để mọi người ở xa nghe thấy.", "colloc": "Do not shout in the classroom", "colloc_vi": "Đừng la hét to trong lớp học", "audio": "shout. To speak very loudly.", "type": "grammar", "svg_type": "action", "emoji": "📢"},
        {"word": "climb", "meaning": "to go up using your hands and feet (verb)", "vietnamese": "Leo trèo bằng cả tay và chân (Động từ)", "mnemonic": "Chú khỉ hoặc bạn nhỏ dùng tay chân trèo lên cây 🧗.", "colloc": "Monkeys climb tall trees", "colloc_vi": "Những chú khỉ leo lên những cái cây cao", "audio": "climb. To go up using hands and feet.", "type": "grammar", "svg_type": "action", "emoji": "🧗"},
        {"word": "strong", "meaning": "having great physical power (adjective)", "vietnamese": "Khỏe mạnh, lực lưỡng (Tính từ)", "mnemonic": "Cánh tay cuồn cuộn cơ bắp 💪 nâng được vật nặng.", "colloc": "An elephant is very strong", "colloc_vi": "Con voi rất là khỏe mạnh", "audio": "strong. Having great physical power.", "type": "grammar", "svg_type": "adj", "emoji": "💪"},
        {"word": "weak", "meaning": "having little power or strength (adjective)", "vietnamese": "Yếu ớt, thiếu sức mạnh (Tính từ)", "mnemonic": "Cơ thể mệt mỏi, không đủ sức nâng vật nặng.", "colloc": "He feels weak when he is sick", "colloc_vi": "Cậu ấy cảm thấy yếu ớt khi bị ốm", "audio": "weak. Having little strength.", "type": "grammar", "svg_type": "adj", "emoji": "🥀"},

        # Science: Light & Dark
        {"word": "light", "meaning": "energy we use to see the world", "vietnamese": "Ánh sáng: dạng năng lượng giúp mắt ta nhìn thấy vạn vật", "mnemonic": "Nhờ có ánh sáng 💡 mắt ta mới nhìn thấy màu sắc và đồ vật xung quanh.", "colloc": "We need light to see", "colloc_vi": "Chúng ta cần ánh sáng để nhìn thấy", "audio": "light. Energy we use to see the world.", "type": "science", "svg_type": "light", "emoji": "💡"},
        {"word": "darkness", "meaning": "when there is no light", "vietnamese": "Bóng tối: xảy ra khi hoàn toàn không có ánh sáng", "mnemonic": "Khi tắt hết đèn hoặc đêm không trăng 🌑, không có ánh sáng chiếu tới mắt.", "colloc": "It is dark when there is no light", "colloc_vi": "Trời tối khi không có ánh sáng", "audio": "darkness. It is dark when there is no light.", "type": "science", "svg_type": "darkness", "emoji": "🌑"},
        {"word": "light source", "meaning": "something that makes its own light", "vietnamese": "Nguồn sáng: vật tự nó phát ra ánh sáng của chính mình", "mnemonic": "Mặt Trời ☀️, ngọn lửa, đèn pin tự phát sáng là nguồn sáng. Mặt Trăng chỉ phản chiếu, không phải nguồn sáng!", "colloc": "The Sun and torch are light sources", "colloc_vi": "Mặt Trời và đèn pin là các nguồn phát sáng", "audio": "light source. Something that makes its own light.", "type": "science", "svg_type": "light_source", "emoji": "☀️"},
        {"word": "torch", "meaning": "a small portable battery lamp (flashlight)", "vietnamese": "Đèn pin cầm tay (nguồn sáng nhân tạo)", "mnemonic": "Chiếc đèn pin nhỏ cầm tay 🔦 bấm nút là phát ra chùm sáng trong đêm.", "colloc": "He turned on the torch in the dark", "colloc_vi": "Cậu ấy đã bật đèn pin trong bóng tối", "audio": "torch. A small portable lamp.", "type": "science", "svg_type": "light_source", "emoji": "🔦"},
        {"word": "candle", "meaning": "a wax stick with a wick that burns for light", "vietnamese": "Ngọn nến bằng sáp thắp sáng (nguồn sáng)", "mnemonic": "Cây nến sinh nhật 🕯️ thắp lửa cháy bập bùng phát ra ánh sáng vàng ấm áp.", "colloc": "A burning candle makes light", "colloc_vi": "Một ngọn nến đang cháy phát ra ánh sáng", "audio": "candle. A stick that burns for light.", "type": "science", "svg_type": "light_source", "emoji": "🕯️"},
        {"word": "reflector", "meaning": "an object that bounces light off instead of making it", "vietnamese": "Vật phản xạ: không tự phát sáng mà chỉ hắt tia sáng lại", "mnemonic": "Gương soi và Mặt Trăng 🪞 không tự phát sáng, chỉ phản chiếu ánh sáng từ nguồn khác.", "colloc": "A mirror is a reflector of light", "colloc_vi": "Gương là một vật phản xạ ánh sáng", "audio": "reflector. An object that bounces light off.", "type": "science", "svg_type": "reflector", "emoji": "🪞"},

        # Maths: Tally & Data
        {"word": "tally chart", "meaning": "marks used to count data in groups of 5", "vietnamese": "Bảng gạch đếm dữ liệu theo từng nhóm 5 gạch", "mnemonic": "Cứ 4 gạch đứng và 1 gạch chéo ngang |||| tạo thành 1 bó 5 gạch giúp đếm cực nhanh.", "colloc": "Count tallies in groups of five", "colloc_vi": "Đếm các dấu gạch theo từng nhóm 5", "audio": "tally chart. Marks used to count in groups of five.", "type": "maths", "svg_type": "tally", "emoji": "📊"},
        {"word": "data", "meaning": "information collected by counting or measuring", "vietnamese": "Dữ liệu / Số liệu thu thập được", "mnemonic": "Các con số ghi chép lại sau khi điều tra sở thích của cả lớp 📈.", "colloc": "Collect data about favorite fruit", "colloc_vi": "Thu thập số liệu về loại trái cây yêu thích", "audio": "data. Information collected by counting.", "type": "maths", "svg_type": "data", "emoji": "📋"},
        {"word": "most popular", "meaning": "liked or chosen by the most people", "vietnamese": "Phổ biến nhất / Được nhiều người yêu thích nhất", "mnemonic": "Số học sinh chọn đông nhất (như Đà Lạt có 5 học sinh chọn trong bài).", "colloc": "Đà Lạt was the most popular destination", "colloc_vi": "Đà Lạt là điểm đến được yêu thích nhất", "audio": "most popular. Liked by the most people.", "type": "maths", "svg_type": "data", "emoji": "🌟"}
    ],
    "week2": [
        # Sentence Structure
        {"word": "statement", "meaning": "tells something, ends with a full stop", "vietnamese": "Câu kể / Câu trần thuật: kể sự việc, kết thúc bằng dấu chấm (.)", "mnemonic": "Bắt đầu bằng chữ hoa, cuối câu có dấu chấm . (Ví dụ: The cat is cute.)", "colloc": "The cat is cute.", "colloc_vi": "Con mèo rất dễ thương.", "audio": "statement. Tells something and ends with a full stop.", "type": "grammar", "svg_type": "statement", "emoji": "📝"},
        {"word": "question", "meaning": "asks something, ends with a question mark", "vietnamese": "Câu hỏi: dùng để hỏi thông tin, kết thúc bằng dấu hỏi (?)", "mnemonic": "Động từ nhảy lên trước chủ ngữ, cuối câu bắt buộc có dấu ? (Ví dụ: Is the cat cute?)", "colloc": "Is the cat cute?", "colloc_vi": "Con mèo có dễ thương không?", "audio": "question. Asks something and ends with a question mark.", "type": "grammar", "svg_type": "question", "emoji": "❓"},
        {"word": "full stop", "meaning": "a dot (.) put at the end of a statement", "vietnamese": "Dấu chấm (.) đặt ở cuối câu kể", "mnemonic": "Dấu chấm tròn nhỏ kết thúc một câu trần thuật trọn vẹn.", "colloc": "Put a full stop at the end of the statement", "colloc_vi": "Đặt dấu chấm ở cuối câu kể", "audio": "full stop. A dot put at the end of a statement.", "type": "grammar", "svg_type": "punct", "emoji": "⏺️"},
        {"word": "question mark", "meaning": "a mark (?) put at the end of a question", "vietnamese": "Dấu chấm hỏi (?) đặt ở cuối câu hỏi", "mnemonic": "Chiếc móc câu có dấu chấm bên dưới ❓ chuyên dùng để hỏi.", "colloc": "Put a question mark at the end of the question", "colloc_vi": "Đặt dấu hỏi ở cuối câu hỏi", "audio": "question mark. Put at the end of a question.", "type": "grammar", "svg_type": "punct", "emoji": "❓"},
        {"word": "was there a", "meaning": "question for one singular thing in the past", "vietnamese": "Có một... ở đó phải không? (Dùng cho danh từ số ít)", "mnemonic": "Chỉ 1 đồ vật: Was there a book? (Có 1 cuốn sách phải không?)", "colloc": "Was there a melon on the plate?", "colloc_vi": "Có một quả dưa trên đĩa phải không?", "audio": "was there a melon on the plate?", "type": "grammar", "svg_type": "singular", "emoji": "1️⃣"},
        {"word": "were there some", "meaning": "question for plural things in the past", "vietnamese": "Có một vài... ở đó phải không? (Dùng cho danh từ số nhiều)", "mnemonic": "Từ 2 đồ vật trở lên: Were there some oranges? (Có vài quả cam phải không?)", "colloc": "Were there some chocolates in the box?", "colloc_vi": "Có vài thanh sô-cô-la trong hộp phải không?", "audio": "were there some chocolates in the box?", "type": "grammar", "svg_type": "plural", "emoji": "🔢"},

        # Regular Past Verbs (-ed)
        {"word": "walked", "meaning": "past form of walk (regular -ed)", "vietnamese": "Đã đi bộ: dạng quá khứ của walk (thêm đuôi -ed)", "mnemonic": "Hành động đã xảy ra trong quá khứ: walk + ed = walked.", "colloc": "She walked to school yesterday", "colloc_vi": "Hôm qua bạn ấy đã đi bộ đến trường", "audio": "walked. Past simple of walk.", "type": "grammar", "svg_type": "walked", "emoji": "🚶"},
        {"word": "played", "meaning": "past form of play (regular -ed)", "vietnamese": "Đã chơi đùa: dạng quá khứ của play (thêm đuôi -ed)", "mnemonic": "Đã chơi trò chơi hoặc thể thao hôm qua: play + ed = played.", "colloc": "They played football in the park", "colloc_vi": "Họ đã chơi bóng đá trong công viên", "audio": "played. Past simple of play.", "type": "grammar", "svg_type": "played", "emoji": "⚽"},
        {"word": "shouted", "meaning": "past form of shout (regular -ed)", "vietnamese": "Đã la hét / kêu to: dạng quá khứ của shout (thêm đuôi -ed)", "mnemonic": "Hét toáng lên vì ngạc nhiên hoặc gọi bạn: shout + ed = shouted.", "colloc": "He shouted for help", "colloc_vi": "Cậu ấy đã hét to lên để gọi người giúp", "audio": "shouted. Past simple of shout.", "type": "grammar", "svg_type": "shouted", "emoji": "📢"},
        {"word": "climbed", "meaning": "past form of climb (regular -ed)", "vietnamese": "Đã leo trèo: dạng quá khứ của climb (thêm đuôi -ed)", "mnemonic": "Trèo cây hoặc leo núi trong quá khứ: climb + ed = climbed.", "colloc": "The monkey climbed the tall tree", "colloc_vi": "Chú khỉ đã leo lên cái cây cao", "audio": "climbed. Past simple of climb.", "type": "grammar", "svg_type": "climbed", "emoji": "🧗"},

        # Irregular Past Verbs
        {"word": "ran", "meaning": "past form of run (irregular)", "vietnamese": "Đã chạy: dạng quá khứ bất quy tắc của run (run &rarr; ran)", "mnemonic": "Chữ u biến thành chữ a (run &rarr; ran). Tuyệt đối không thêm -ed!", "colloc": "Billy ran to the window", "colloc_vi": "Billy đã chạy ngay lại phía cửa sổ", "audio": "ran. Past simple of run.", "type": "grammar", "svg_type": "ran", "emoji": "🏃"},
        {"word": "saw", "meaning": "past form of see (irregular)", "vietnamese": "Đã nhìn thấy: dạng quá khứ bất quy tắc của see (see &rarr; saw)", "mnemonic": "Mắt đã thấy điều gì đó hôm qua: see biến thành saw.", "colloc": "We saw blue smoke", "colloc_vi": "Chúng tôi đã nhìn thấy một làn khói màu xanh lam", "audio": "saw. Past simple of see.", "type": "grammar", "svg_type": "saw", "emoji": "👀"},
        {"word": "ate", "meaning": "past form of eat (irregular)", "vietnamese": "Đã ăn: dạng quá khứ bất quy tắc của eat (eat &rarr; ate)", "mnemonic": "Đảo vị trí chữ cái e-a-t thành a-t-e (eat &rarr; ate: đã ăn xong quả táo).", "colloc": "He ate a delicious apple", "colloc_vi": "Cậu ấy đã ăn một quả táo thơm ngon", "audio": "ate. Past simple of eat.", "type": "grammar", "svg_type": "ate", "emoji": "🍎"},
        {"word": "went", "meaning": "past form of go (irregular)", "vietnamese": "Đã đi: dạng quá khứ bất quy tắc của go (go &rarr; went)", "mnemonic": "Đã đi du lịch hoặc đi học hôm qua: go đổi thành went.", "colloc": "They went to the beach", "colloc_vi": "Họ đã đi nghỉ mát ở bãi biển", "audio": "went. Past simple of go.", "type": "grammar", "svg_type": "went", "emoji": "🏖️"},
        {"word": "wrote", "meaning": "past form of write (irregular)", "vietnamese": "Đã viết: dạng quá khứ bất quy tắc của write (write &rarr; wrote)", "mnemonic": "Dùng bút viết vào vở hôm qua: write đổi thành wrote.", "colloc": "She wrote a letter to her friend", "colloc_vi": "Bạn ấy đã viết một bức thư cho bạn mình", "audio": "wrote. Past simple of write.", "type": "grammar", "svg_type": "wrote", "emoji": "✍️"},
        {"word": "swam", "meaning": "past form of swim (irregular)", "vietnamese": "Đã bơi lội: dạng quá khứ bất quy tắc của swim (swim &rarr; swam)", "mnemonic": "Chữ i biến thành chữ a: swim &rarr; swam (đã bơi trong hồ).", "colloc": "The fish swam in the river", "colloc_vi": "Chú cá đã bơi lội dưới dòng sông", "audio": "swam. Past simple of swim.", "type": "grammar", "svg_type": "swam", "emoji": "🏊"},
        {"word": "was", "meaning": "past form of is / am (singular)", "vietnamese": "Đã thì / là / ở (quá khứ của is và am, dùng cho số ít)", "mnemonic": "He was happy, She was a teacher (Hôm qua cô ấy từng là...).", "colloc": "He was in the garden", "colloc_vi": "Cậu ấy đã ở trong vườn", "audio": "was. Past simple of is and am.", "type": "grammar", "svg_type": "singular", "emoji": "👤"},
        {"word": "were", "meaning": "past form of are (plural)", "vietnamese": "Đã thì / là / ở (quá khứ của are, dùng cho số nhiều)", "mnemonic": "They were at school (Họ đã ở trường học).", "colloc": "They were very happy yesterday", "colloc_vi": "Hôm qua họ đã rất vui vẻ", "audio": "were. Past simple of are.", "type": "grammar", "svg_type": "plural", "emoji": "👥"},

        # Science: Opacity & Light
        {"word": "transparent", "meaning": "all light passes through, see clearly", "vietnamese": "Vật trong suốt: cho toàn bộ ánh sáng đi qua, nhìn rõ thấu 100%", "mnemonic": "Cốc thủy tinh trong veo, nước sạch 🪟 &rarr; nhìn xuyên qua rõ mồn một.", "colloc": "Clear glass is transparent", "colloc_vi": "Kính trong suốt là vật liệu trong suốt", "audio": "transparent. All light passes through.", "type": "science", "svg_type": "transparent", "emoji": "🪟"},
        {"word": "translucent", "meaning": "some light passes through, see partially", "vietnamese": "Vật bán trong suốt: chỉ cho một phần ánh sáng đi qua, nhìn mờ mờ", "mnemonic": "Kính râm chống chói 🕶️, giấy can vẽ &rarr; nhìn qua thấy mờ ảo, không rõ nét.", "colloc": "Sunglasses are translucent", "colloc_vi": "Kính râm là vật liệu bán trong suốt", "audio": "translucent. Some light passes through.", "type": "science", "svg_type": "translucent", "emoji": "🕶️"},
        {"word": "opaque", "meaning": "no light passes through, blocks light", "vietnamese": "Vật đục cản sáng: chặn đứng hoàn toàn ánh sáng, tạo ra bóng tối", "mnemonic": "Bức tường gạch, cánh cửa gỗ, hòn đá 🧱 &rarr; chặn toàn bộ tia sáng tạo thành bóng đen.", "colloc": "Wood and stone are opaque", "colloc_vi": "Gỗ và đá là những vật liệu đục cản sáng", "audio": "opaque. Blocks light completely.", "type": "science", "svg_type": "opaque", "emoji": "🧱"},
        {"word": "straight line", "meaning": "light always travels straight and cannot bend", "vietnamese": "Đường thẳng: tia sáng luôn truyền thẳng, không thể tự bẻ cong", "mnemonic": "Ánh sáng như mũi tên bay thẳng tắp 📏, gặp vật cản thì bị chặn chứ không biết uốn lượn.", "colloc": "Light travels in a straight line", "colloc_vi": "Ánh sáng luôn luôn truyền theo đường thẳng", "audio": "straight line. Light travels in a straight line.", "type": "science", "svg_type": "straight_line", "emoji": "📏"},
        {"word": "shadow", "meaning": "a dark shape made when light is blocked by an opaque object", "vietnamese": "Bóng tối / Cái bóng: tạo ra khi vật cản sáng chặn tia sáng", "mnemonic": "Đứng dưới trời nắng, cơ thể con là vật đục chắn tia sáng tạo ra chiếc bóng đen trên mặt đất.", "colloc": "The tree casts a dark shadow", "colloc_vi": "Cái cây tạo ra một bóng râm đen", "audio": "shadow. A dark shape made when light is blocked.", "type": "science", "svg_type": "shadow", "emoji": "👤"},

        # Maths: Comparing Numbers
        {"word": "greater than", "meaning": "larger number (>)", "vietnamese": "Lớn hơn (dấu >)", "mnemonic": "Chú cá sấu đói bụng 🐊 luôn há to miệng về phía số lớn hơn (400 > 300).", "colloc": "400 is greater than 300", "colloc_vi": "Bốn trăm lớn hơn ba trăm (400 > 300)", "audio": "greater than. The crocodile eats the bigger number.", "type": "maths", "svg_type": "greater_than", "emoji": "🐊"},
        {"word": "less than", "meaning": "smaller number (<)", "vietnamese": "Nhỏ hơn (dấu <)", "mnemonic": "Mũi nhọn cá sấu chọc vào số bé hơn, miệng há về số to (200 < 500).", "colloc": "200 is less than 500", "colloc_vi": "Hai trăm nhỏ hơn năm trăm (200 < 500)", "audio": "less than. Two hundred is less than five hundred.", "type": "maths", "svg_type": "less_than", "emoji": "🐊"},
        {"word": "equal to", "meaning": "having the exact same value (=)", "vietnamese": "Bằng nhau (dấu =)", "mnemonic": "Hai số bằng y hệt nhau thì dùng dấu bằng (150 = 150).", "colloc": "150 is equal to 150", "colloc_vi": "Một trăm năm mươi bằng một trăm năm mươi", "audio": "equal to. Both numbers have the same value.", "type": "maths", "svg_type": "equal_to", "emoji": "🟰"}
    ],
    "week3": [
        # Story & Machines
        {"word": "telescope", "meaning": "instrument to look at stars and planets", "vietnamese": "Kính viễn vọng / Kính thiên văn để ngắm các vì sao và hành tinh", "mnemonic": "Ống kính nhìn xa tít tắp 🔭 vào vũ trụ bao la để ngắm nhìn Mặt Trăng và sao Thổ.", "colloc": "Look at the moon through a telescope", "colloc_vi": "Ngắm nhìn Mặt Trăng qua kính viễn vọng", "audio": "telescope. Instrument to look at space.", "type": "story", "svg_type": "telescope", "emoji": "🔭"},
        {"word": "professor", "meaning": "a smart teacher or scientist", "vietnamese": "Giáo sư / Nhà khoa học tài ba chế tạo máy móc", "mnemonic": "Giáo sư Inkspot 👨‍🔬 là nhà khoa học thông minh sống ngay cạnh nhà của Billy.", "colloc": "Professor Inkspot invented a machine", "colloc_vi": "Giáo sư Inkspot đã phát minh ra một cỗ máy", "audio": "professor. A scientist or teacher.", "type": "story", "svg_type": "professor", "emoji": "👨‍🔬"},
        {"word": "shed", "meaning": "a small wooden building in a garden", "vietnamese": "Nhà kho nhỏ bằng gỗ trong vườn để dụng cụ và máy móc", "mnemonic": "Gian nhà gỗ nhỏ 🛖 bên cạnh vườn nơi giáo sư cặm cụi nghiên cứu cỗ máy không gian.", "colloc": "Billy ran to the professor's shed", "colloc_vi": "Billy chạy sang gian nhà kho của giáo sư", "audio": "shed. A small building in a garden.", "type": "story", "svg_type": "shed", "emoji": "🛖"},
        {"word": "half past six", "meaning": "6:30 in the morning when Billy woke up with a BANG", "vietnamese": "Sáu rưỡi sáng (6:30) lúc Billy giật mình tỉnh giấc bởi tiếng nổ lớn", "mnemonic": "Kim ngắn chỉ giữa số 6 và 7, kim dài chỉ số 6: đúng 6 giờ 30 phút sáng ⏰.", "colloc": "Billy woke up at half past six", "colloc_vi": "Billy đã thức giấc vào lúc 6 giờ 30 phút sáng", "audio": "half past six. Six thirty in the morning.", "type": "story", "svg_type": "when", "emoji": "⏰"},
        {"word": "turn a dial", "meaning": "rotate a round knob with numbers", "vietnamese": "Xoay núm vặn tròn chia vạch số", "mnemonic": "Dùng ngón tay xoay núm vặn tròn 🎛️ (như chỉnh góc kính viễn vọng hoặc vặn âm lượng).", "colloc": "We turn a dial on the machine", "colloc_vi": "Chúng ta xoay núm vặn trên cỗ máy", "audio": "turn a dial. We turn a dial.", "type": "colloc", "svg_type": "turn_dial", "emoji": "🎛️"},
        {"word": "push a button", "meaning": "press down a button with finger", "vietnamese": "Bấm / Nhấn nút tròn bằng ngón tay", "mnemonic": "Lấy ngón tay ấn mạnh vào chiếc nút đỏ 🔴 kêu 'Tít!' để phóng xung năng lượng.", "colloc": "We push a red button", "colloc_vi": "Chúng ta bấm một chiếc nút màu đỏ", "audio": "push a button. We push a button.", "type": "colloc", "svg_type": "push_button", "emoji": "🔴"},
        {"word": "press a switch", "meaning": "toggle a switch for power", "vietnamese": "Bật / Gạt công tắc nguồn điện", "mnemonic": "Gạt công tắc bập bênh ⚡ để đèn LED xanh sáng lên và khởi động cỗ máy.", "colloc": "We press a switch under the screen", "colloc_vi": "Chúng ta bật công tắc bên dưới màn hình", "audio": "press a switch. We press a switch.", "type": "colloc", "svg_type": "press_switch", "emoji": "⚡"},
        {"word": "pull a handle", "meaning": "move a handle down or toward you", "vietnamese": "Kéo cần gạt xuống dưới", "mnemonic": "Nắm lấy tay cầm 🕹️ và kéo mạnh cần gạt xuống để quét không gian vũ trụ.", "colloc": "We pull a handle beside the screen", "colloc_vi": "Chúng ta kéo chiếc cần gạt cạnh màn hình", "audio": "pull a handle. We pull a handle.", "type": "colloc", "svg_type": "pull_handle", "emoji": "🕹️"},
        {"word": "screen", "meaning": "flat surface on a machine that shows pictures", "vietnamese": "Màn hình: mặt phẳng hiển thị hình ảnh không gian", "mnemonic": "Màn hình vuông vức 🖥️ ở giữa cỗ máy hiển thị các vì sao và hành tinh lấp lánh.", "colloc": "A square screen showed deep space", "colloc_vi": "Một màn hình vuông hiển thị không gian sâu thẳm", "audio": "screen. A flat surface that shows pictures.", "type": "story", "svg_type": "screen", "emoji": "🖥️"},
        {"word": "whirring sound", "meaning": "a rapid buzzing or rotating noise made by a machine", "vietnamese": "Tiếng vù vù / rè rè do cánh quạt máy quay tít", "mnemonic": "Âm thanh máy móc chạy kêu vù vù như cánh quạt điện.", "colloc": "The machine made a strange whirring sound", "colloc_vi": "Cỗ máy phát ra tiếng vù vù kỳ lạ", "audio": "whirring sound. A buzzing sound made by a machine.", "type": "story", "svg_type": "sound", "emoji": "🌀"},

        # Question Words
        {"word": "who", "meaning": "asks about a person", "vietnamese": "Ai? (Hỏi về NGƯỜI)", "mnemonic": "Hỏi về con người hoặc nhân vật: Who is your teacher? (Ai là giáo viên của con?)", "colloc": "Who is your best friend?", "colloc_vi": "Ai là người bạn thân nhất của con?", "audio": "who asks about a person.", "type": "qword", "svg_type": "who", "emoji": "👤"},
        {"word": "where", "meaning": "asks about a place or location", "vietnamese": "Ở đâu? (Hỏi về NƠI CHỐN, ĐỊA ĐIỂM)", "mnemonic": "Hỏi về vị trí: Where do you live? (Con sống ở đâu?)", "colloc": "Where do you live?", "colloc_vi": "Con sống ở đâu thế?", "audio": "where asks about a place.", "type": "qword", "svg_type": "where", "emoji": "📍"},
        {"word": "what", "meaning": "asks about a thing or action", "vietnamese": "Cái gì? (Hỏi về ĐỒ VẬT hoặc HÀNH ĐỘNG)", "mnemonic": "Hỏi về sự vật: What do you like to eat? (Con thích ăn món gì?)", "colloc": "What is in your backpack?", "colloc_vi": "Có cái gì trong cặp sách của con thế?", "audio": "what asks about a thing or action.", "type": "qword", "svg_type": "what", "emoji": "📦"},
        {"word": "when", "meaning": "asks about time", "vietnamese": "Khi nào? / Bao giờ? (Hỏi về THỜI GIAN)", "mnemonic": "Hỏi về giờ giấc, ngày tháng: When is your birthday? (Khi nào là sinh nhật con?)", "colloc": "When does school start?", "colloc_vi": "Khi nào thì trường học bắt đầu?", "audio": "when asks about time.", "type": "qword", "svg_type": "when", "emoji": "⏰"},
        {"word": "why", "meaning": "asks for a reason (answered with Because)", "vietnamese": "Tại sao? (Hỏi về LÝ DO, câu trả lời bắt đầu bằng Because)", "mnemonic": "Hỏi nguyên nhân: Why do you go to school? - Because I want to learn.", "colloc": "Why are you happy?", "colloc_vi": "Tại sao con lại vui vẻ thế?", "audio": "why asks for a reason.", "type": "qword", "svg_type": "why", "emoji": "💡"},
        {"word": "how", "meaning": "asks about manner, process, or feelings", "vietnamese": "Như thế nào? / Bằng cách nào? (Hỏi về CÁCH THỨC hoặc CẢM XÚC)", "mnemonic": "Hỏi cách làm: How do you cook an egg? (Con nấu trứng bằng cách nào?)", "colloc": "How do you feel today?", "colloc_vi": "Hôm nay con cảm thấy thế nào?", "audio": "how asks about feelings or manner.", "type": "qword", "svg_type": "how", "emoji": "⚙️"},

        # Science: Teeth & Digestion
        {"word": "incisors", "meaning": "8 chisel-like front teeth to slice food", "vietnamese": "Răng cửa (8 chiếc: 4 trên, 4 dưới) - Dùng để CẮT LÁT / CẮN thức ăn", "mnemonic": "Răng ở ngay mặt trước, mỏng và phẳng như lưỡi kéo dùng cắn ngập vào quả táo 🍎.", "colloc": "Incisors slice into apples", "colloc_vi": "Răng cửa dùng để cắn và cắt lát quả táo", "audio": "incisors. Front teeth used for slicing.", "type": "science", "svg_type": "incisors", "emoji": "🦷"},
        {"word": "canines", "meaning": "4 pointed teeth to tear tough food", "vietnamese": "Răng nanh (4 chiếc) - Dùng để XÉ thức ăn dai", "mnemonic": "Chiếc răng nhọn hoắt như răng nanh ma cà rồng 🧛 cạnh răng cửa, chuyên xé thịt gà, thịt bò dai.", "colloc": "Canines tear tough meat", "colloc_vi": "Răng nanh dùng để xé thịt dai", "audio": "canines. Pointed teeth used for tearing.", "type": "science", "svg_type": "canines", "emoji": "🧛"},
        {"word": "premolars", "meaning": "8 teeth with cusps to chew and crush", "vietnamese": "Răng tiền hàm (8 chiếc) - Dùng để NHAI và ĐẬP VỤN thức ăn", "mnemonic": "Nằm giữa răng nanh và răng hàm, có 2 gờ nhô lên như búa 🔨 đập vụn thức ăn.", "colloc": "Premolars chew and crush food", "colloc_vi": "Răng tiền hàm dùng để nhai và đập vỡ thức ăn", "audio": "premolars. Teeth used for chewing and crushing.", "type": "science", "svg_type": "premolars", "emoji": "🔨"},
        {"word": "molars", "meaning": "12 largest teeth at back to grind food", "vietnamese": "Răng hàm (12 chiếc - RĂNG TO NHẤT) - Dùng để NGHIỀN MỊN thức ăn", "mnemonic": "Răng to nhất nằm sâu trong cùng, mặt phẳng như cối đá 🪨 nghiền nát thức ăn trước khi nuốt.", "colloc": "Molars grind food into fine pieces", "colloc_vi": "Răng hàm dùng để nghiền nát thức ăn thành miếng nhỏ mịn", "audio": "molars. Largest teeth used for grinding.", "type": "science", "svg_type": "molars", "emoji": "🪨"},
        {"word": "milk teeth", "meaning": "20 baby teeth in children under six", "vietnamese": "Răng sữa (trẻ em dưới 6 tuổi có đúng 20 chiếc)", "mnemonic": "Trẻ nhỏ dưới sáu tuổi có 20 chiếc răng sữa xinh xắn 👶, sau này sẽ rụng để mọc răng vĩnh viễn.", "colloc": "Children under six have 20 milk teeth", "colloc_vi": "Trẻ em dưới sáu tuổi có tổng cộng 20 chiếc răng sữa", "audio": "milk teeth. Twenty teeth in young children.", "type": "science", "svg_type": "milk_teeth", "emoji": "👶"},
        {"word": "permanent teeth", "meaning": "32 adult teeth that last a lifetime", "vietnamese": "Răng vĩnh viễn (người lớn có 32 chiếc răng chắc khỏe)", "mnemonic": "Người lớn 🧑 có 32 chiếc răng vĩnh viễn theo ta suốt đời, nếu mất sẽ không mọc lại được!", "colloc": "Adults have 32 permanent teeth", "colloc_vi": "Người lớn có 32 chiếc răng vĩnh viễn", "audio": "permanent teeth. Thirty-two adult teeth.", "type": "science", "svg_type": "permanent_teeth", "emoji": "🧑"},
        {"word": "slice", "meaning": "to cut into thin pieces using sharp front teeth", "vietnamese": "Cắt lát / Cắn đứt thức ăn (chức năng của răng cửa Incisors)", "mnemonic": "Cắn phập một nhát ngọt xớt như dao cắt lát bánh mì 🔪.", "colloc": "We slice bread with incisors", "colloc_vi": "Chúng ta cắt lát thức ăn bằng răng cửa", "audio": "slice. To cut into thin pieces.", "type": "science", "svg_type": "action", "emoji": "🔪"},
        {"word": "tear", "meaning": "to pull apart tough meat using sharp pointed teeth", "vietnamese": "Cắn xé thức ăn dai (chức năng của răng nanh Canines)", "mnemonic": "Gặm thịt đùi gà dai, dùng răng nanh nhọn cắn xé mạnh 🍗.", "colloc": "Canines tear tough meat off the bone", "colloc_vi": "Răng nanh cắn xé thịt dai ra khỏi xương", "audio": "tear. To pull apart tough food.", "type": "science", "svg_type": "action", "emoji": "🍗"},
        {"word": "chew", "meaning": "to crush food with your teeth before swallowing", "vietnamese": "Nhai và đập vụn thức ăn (chức năng của răng tiền hàm Premolars)", "mnemonic": "Hai hàm răng khép lại nhai đi nhai lại giúp thức ăn vỡ nhỏ 🍞.", "colloc": "Chew your food well before swallowing", "colloc_vi": "Hãy nhai kỹ thức ăn trước khi nuốt", "audio": "chew. To crush food with your teeth.", "type": "science", "svg_type": "action", "emoji": "👄"},
        {"word": "grind", "meaning": "to crush food into fine, smooth particles", "vietnamese": "Nghiền nát thành bột mịn (chức năng của răng hàm Molars)", "mnemonic": "Xay nhuyễn hạt đậu phộng cứng ngắc thành bột nhuyễn mịn 🥜.", "colloc": "Molars grind hard nuts into a paste", "colloc_vi": "Răng hàm nghiền các hạt cứng thành bột mịn", "audio": "grind. To crush food into fine pieces.", "type": "science", "svg_type": "action", "emoji": "🥜"},

        # Maths: Place Value & Expanded Form
        {"word": "place value", "meaning": "value of digit based on position (H, T, O)", "vietnamese": "Giá trị theo hàng của chữ số: Hàng Trăm, Hàng Chục, Hàng Đơn vị", "mnemonic": "Cùng là chữ số 5: ở hàng Trăm là 500, hàng Chục là 50, hàng Đơn vị là 5 🧱.", "colloc": "Hundreds, Tens, and Ones", "colloc_vi": "Hàng Trăm, hàng Chục và hàng Đơn vị", "audio": "place value. Hundreds, Tens, and Ones.", "type": "maths", "svg_type": "place_value", "emoji": "🧱"},
        {"word": "expanded form", "meaning": "writing number as sum of place values", "vietnamese": "Dạng khai triển của số: viết thành tổng các hàng", "mnemonic": "Viết tách số 569 thành: 500 + 60 + 9 ➕ để thấy rõ giá trị từng chữ số.", "colloc": "500 + 60 + 9 = 569", "colloc_vi": "Năm trăm cộng sáu mươi cộng chín bằng 569", "audio": "expanded form. Five hundred plus sixty plus nine.", "type": "maths", "svg_type": "expanded_form", "emoji": "➕"},
        {"word": "hundreds flat", "meaning": "a large square block made of 100 small unit cubes", "vietnamese": "Tấm vuông hàng Trăm (gồm 100 khối lập phương nhỏ ghép lại)", "mnemonic": "Tấm lưới vuông 10 hàng x 10 cột = đúng 100 ô vuông nhỏ.", "colloc": "One flat represents one hundred", "colloc_vi": "Một tấm vuông đại diện cho một trăm", "audio": "hundreds flat. A block of one hundred units.", "type": "maths", "svg_type": "place_value", "emoji": "🟦"},
        {"word": "tens rod", "meaning": "a long stick made of 10 unit cubes", "vietnamese": "Thanh hàng Chục (gồm 10 khối lập phương nhỏ xếp thẳng hàng)", "mnemonic": "Một chiếc que dài dựng đứng chứa đúng 10 khối vuông nhỏ.", "colloc": "Six rods represent sixty", "colloc_vi": "Sáu thanh que đại diện cho sáu mươi", "audio": "tens rod. A stick of ten units.", "type": "maths", "svg_type": "place_value", "emoji": "🟩"},
        {"word": "ones cube", "meaning": "a single small unit cube representing 1", "vietnamese": "Khối lập phương đơn vị (đại diện cho số 1)", "mnemonic": "Một cục xúc xắc nhỏ xíu đại diện cho 1 đơn vị.", "colloc": "Nine cubes represent nine ones", "colloc_vi": "Chín khối nhỏ đại diện cho 9 đơn vị", "audio": "ones cube. A single small unit cube.", "type": "maths", "svg_type": "place_value", "emoji": "🟨"}
    ],
    "week4": [
        # English: Story & Machine Action Verbs
        {"word": "true", "meaning": "something that is correct or real (a fact)", "vietnamese": "Đúng / Sự thật: điều gì đó chính xác hoặc có thật (a fact)", "mnemonic": "Sự thật hiển nhiên không thể bàn cãi (như Mặt Trời mọc hướng Đông) là True ✅.", "colloc": "It is true that the Sun makes light", "colloc_vi": "Sự thật là Mặt Trời tự phát ra ánh sáng", "audio": "true. Something that is correct or real.", "type": "story", "svg_type": "true_false", "emoji": "✅"},
        {"word": "false", "meaning": "something that is not correct or not real", "vietnamese": "Sai: điều gì đó không chính xác hoặc không có thật", "mnemonic": "Thông tin sai lệch hoặc bịa đặt không đúng sự thật là False ❌.", "colloc": "It is false to say dogs can fly", "colloc_vi": "Nói rằng chó biết bay là sai sự thật", "audio": "false. Something that is not correct.", "type": "story", "svg_type": "true_false", "emoji": "❌"},
        {"word": "turn a dial", "meaning": "rotate a round knob with scale marks", "vietnamese": "Xoay núm vặn tròn chia vạch (để chỉnh số, âm lượng)", "mnemonic": "Xoay núm tròn vặn đài radio 🎛️ hoặc xoay góc kính thiên văn.", "colloc": "We turn a dial to focus the telescope", "colloc_vi": "Chúng ta xoay núm vặn để lấy nét kính thiên văn", "audio": "turn a dial. Rotate a round knob.", "type": "colloc", "svg_type": "turn_dial", "emoji": "🎛️"},
        {"word": "press a switch", "meaning": "toggle a switch for electrical power", "vietnamese": "Bật / Gạt công tắc điện (bật đèn, quạt điện)", "mnemonic": "Gạt ngón tay bật công tắc ⚡ để bật đèn trần hoặc cấp nguồn cho máy móc.", "colloc": "Press a switch to turn on the lights", "colloc_vi": "Bật công tắc để thắp sáng đèn", "audio": "press a switch. Toggle a switch for power.", "type": "colloc", "svg_type": "press_switch", "emoji": "⚡"},
        {"word": "pull a handle", "meaning": "move a lever handle down or towards you", "vietnamese": "Kéo cần gạt / tay nắm xuống", "mnemonic": "Cầm cần gạt 🕹️ kéo mạnh xuống để mở cửa hoặc khởi động chế độ quét.", "colloc": "Pull a handle to open the heavy door", "colloc_vi": "Kéo cần gạt để mở cánh cửa nặng", "audio": "pull a handle. Move a lever down.", "type": "colloc", "svg_type": "pull_handle", "emoji": "🕹️"},
        {"word": "push a button", "meaning": "press down on a round button with finger", "vietnamese": "Bấm nút tròn bằng ngón tay (chuông cửa, thang máy)", "mnemonic": "Lấy ngón tay trỏ ấn nút tròn đỏ 🔴 kêu 'Tít!' gọi thang máy.", "colloc": "Push a button to call the elevator", "colloc_vi": "Bấm nút tròn để gọi thang máy", "audio": "push a button. Press down with finger.", "type": "colloc", "svg_type": "push_button", "emoji": "🔴"},

        # English: Past Simple (-ed) & Punctuation
        {"word": "pointed", "meaning": "past form of point (+ed): aimed finger at", "vietnamese": "Đã chỉ tay vào (quá khứ của point: point + ed)", "mnemonic": "Giáo sư chỉ tay 👉 về phía kính viễn vọng: Professor Inkspot pointed.", "colloc": "He pointed at the giant telescope", "colloc_vi": "Ông ấy đã chỉ tay về phía chiếc kính viễn vọng khổng lồ", "audio": "pointed. Past simple of point.", "type": "grammar", "svg_type": "pointed", "emoji": "👉"},
        {"word": "moved", "meaning": "past form of move (+d): changed position", "vietnamese": "Đã di chuyển / nhúc nhích (quá khứ của move: move + d)", "mnemonic": "Cỗ máy bắt đầu nhúc nhích và chuyển động: The machine moved slowly.", "colloc": "The big machine moved slowly", "colloc_vi": "Cỗ máy to lớn đã di chuyển chậm rãi", "audio": "moved. Past simple of move.", "type": "grammar", "svg_type": "action", "emoji": "🚜"},
        {"word": "waited", "meaning": "past form of wait (+ed): stayed patiently", "vietnamese": "Đã kiên nhẫn chờ đợi (quá khứ của wait: wait + ed)", "mnemonic": "Đứng chờ đợi ⏳ đèn đỏ chuyển sang xanh: They waited patiently.", "colloc": "They waited for the red lights to shine", "colloc_vi": "Họ đã chờ đợi những ánh đèn đỏ phát sáng", "audio": "waited. Past simple of wait.", "type": "grammar", "svg_type": "action", "emoji": "⏳"},
        {"word": "gasped", "meaning": "past form of gasp (+ed): breathed in with surprise", "vietnamese": "Đã há hốc mồm ngạc nhiên / thở hắt ra vì kinh ngạc", "mnemonic": "Bất ngờ há hốc miệng 😲 khi cỗ máy bắn ra tia sáng lấp lánh.", "colloc": "Everyone gasped in surprise", "colloc_vi": "Mọi người đều há hốc mồm kinh ngạc", "audio": "gasped. Breathed in with surprise.", "type": "grammar", "svg_type": "action", "emoji": "😲"},
        {"word": "speech marks", "meaning": "quotation marks (\" \") used when someone is talking", "vietnamese": "Dấu ngoặc kép / Dấu lời thoại (“ ”) bao quanh lời nói trực tiếp", "mnemonic": "Cặp dấu ngoặc kép 💬 ôm trọn câu nói của nhân vật. Nhớ dấu phẩy (,) nằm BÊN TRONG ngoặc kép: “I like reading,” Emma said.", "colloc": "“Look at my book,” Ben said.", "colloc_vi": "“Hãy nhìn cuốn sách của tớ này,” Ben nói.", "audio": "speech marks. Used when someone is talking.", "type": "grammar", "svg_type": "speech_marks", "emoji": "💬"},

        # Mathematics: Estimation, Midpoint & Life Number Lines
        {"word": "estimate", "meaning": "to guess roughly without exact counting", "vietnamese": "Ước lượng: đoán gần đúng khi số nằm ở giữa các vạch mốc", "mnemonic": "Không cần đếm từng số 🎯, ta dùng điểm chính giữa để ước đoán nhanh vị trí.", "colloc": "We need to estimate the number", "colloc_vi": "Chúng ta cần ước lượng con số này", "audio": "estimate. To guess roughly without exact counting.", "type": "maths", "svg_type": "estimate", "emoji": "🎯"},
        {"word": "midpoint", "meaning": "the exact halfway point between two benchmark numbers", "vietnamese": "Điểm chính giữa (midpoint): số nằm ngay chính giữa 2 mốc", "mnemonic": "Giữa 0 và 100 là 50 ⚖️. Giữa 20 và 30 là 25. Giữa 40 và 50 là 45.", "colloc": "Fifty is the midpoint between 0 and 100", "colloc_vi": "Số 50 là điểm chính giữa của 0 và 100", "audio": "midpoint. The exact halfway point.", "type": "maths", "svg_type": "midpoint", "emoji": "⚖️"},
        {"word": "ruler", "meaning": "a measuring tool with a number line in centimetres (cm)", "vietnamese": "Thước kẻ: có vạch trục số để đo chiều dài bằng xăng-ti-mét (cm)", "mnemonic": "Cây thước kẻ kẻ thẳng 📏 có các vạch số từ 0 đến 20 cm.", "colloc": "Measure length using a ruler", "colloc_vi": "Đo chiều dài bằng cây thước kẻ", "audio": "ruler. A tool with a number line in centimetres.", "type": "maths", "svg_type": "ruler", "emoji": "📏"},
        {"word": "thermometer", "meaning": "a tool with a number line to measure temperature in degrees Celsius (°C)", "vietnamese": "Nhiệt kế: có vạch trục số để đo nhiệt độ nóng/lạnh (°C)", "mnemonic": "Cột thủy ngân màu đỏ 🌡️ dâng lên cao khi trời nóng, tụt xuống khi trời lạnh.", "colloc": "Check temperature on a thermometer", "colloc_vi": "Kiểm tra nhiệt độ trên nhiệt kế", "audio": "thermometer. Tool to measure temperature.", "type": "maths", "svg_type": "thermometer", "emoji": "🌡️"},
        {"word": "scale", "meaning": "a weighing tool with a number line in kilograms (kg)", "vietnamese": "Chiếc cân: có vạch trục số để đo cân nặng bằng ki-lô-gam (kg)", "mnemonic": "Đặt túi táo lên đĩa cân ⚖️, kim đồng hồ quay chỉ số kg.", "colloc": "Weigh heavy fruit on a scale", "colloc_vi": "Cân hoa quả nặng trên chiếc cân", "audio": "scale. A tool to measure weight in kilograms.", "type": "maths", "svg_type": "scale", "emoji": "⚖️"},

        # Science: Light Travelling & Shadows
        {"word": "straight line", "meaning": "light always travels straight and cannot bend", "vietnamese": "Đường thẳng: ánh sáng luôn truyền thẳng, không thể tự bẻ cong quanh góc", "mnemonic": "Tia sáng thẳng tắp như mũi tên 📏, không thể tự uốn lượn quanh góc tường.", "colloc": "Light always travels in a straight line", "colloc_vi": "Ánh sáng luôn truyền theo một đường thẳng", "audio": "straight line. Light travels in a straight line.", "type": "science", "svg_type": "straight_line", "emoji": "📏"},
        {"word": "shadow", "meaning": "dark shape made when an opaque object blocks light", "vietnamese": "Chiếc bóng / Bóng tối: hình đen tạo ra khi vật cản sáng chặn tia sáng", "mnemonic": "Đứng dưới nắng, cơ thể con cản ánh sáng 👤 tạo ra bóng đen trên mặt đất.", "colloc": "Opaque objects block light to cast shadows", "colloc_vi": "Vật cản sáng chặn tia sáng để tạo nên bóng", "audio": "shadow. Dark shape made when light is blocked.", "type": "science", "svg_type": "shadow", "emoji": "👤"},
        {"word": "bigger shadow", "meaning": "shadow becomes bigger when object is nearer to light", "vietnamese": "Bóng to hơn: xảy ra khi đưa vật lại GẦN nguồn sáng", "mnemonic": "Đưa tay lại gần đèn pin 🔦 &rarr; bóng bàn tay trên tường phóng to khổng lồ!", "colloc": "Nearer to light makes a bigger shadow", "colloc_vi": "Lại gần nguồn sáng tạo ra chiếc bóng to hơn", "audio": "nearer to light makes a bigger shadow.", "type": "science", "svg_type": "shadow", "emoji": "🔍"},
        {"word": "smaller shadow", "meaning": "shadow becomes smaller when object is further away from light", "vietnamese": "Bóng nhỏ hơn: xảy ra khi đưa vật ra XA nguồn sáng", "mnemonic": "Kéo vật ra xa đèn pin &rarr; bóng thu nhỏ lại gọn gàng.", "colloc": "Further from light makes a smaller shadow", "colloc_vi": "Càng xa nguồn sáng thì bóng càng nhỏ lại", "audio": "further away makes a smaller shadow.", "type": "science", "svg_type": "shadow", "emoji": "🔎"},
        {"word": "shortest shadow", "meaning": "at 12 p.m. (midday) when Sun is highest overhead", "vietnamese": "Bóng ngắn nhất: vào lúc 12 giờ trưa khi Mặt Trời lên cao nhất trên đỉnh đầu", "mnemonic": "12 giờ trưa ☀️ Mặt Trời chiếu thẳng đứng từ trên đầu xuống &rarr; bóng thu tròn sát dưới chân.", "colloc": "At midday the shadow is shortest", "colloc_vi": "Vào giữa trưa chiếc bóng là ngắn nhất", "audio": "at midday the shadow is shortest.", "type": "science", "svg_type": "shadow", "emoji": "🕛"},
        {"word": "longest shadow", "meaning": "at 8 a.m. and 5 p.m. when Sun is low in the sky", "vietnamese": "Bóng dài nhất: vào sáng sớm (8 a.m.) và chiều muộn (5 p.m.) khi Mặt Trời ở vị trí thấp", "mnemonic": "Mặt Trời chiếu xiên từ chân trời 🌅 &rarr; bóng cây đổ dài ngoằng trên mặt đất.", "colloc": "Early morning casts the longest shadow", "colloc_vi": "Sáng sớm tạo ra bóng đổ dài nhất", "audio": "early morning casts the longest shadow.", "type": "science", "svg_type": "shadow", "emoji": "🌅"}
    ]
}

# ==================== SLIDE-ALIGNED 10-QUESTION GRAND CHALLENGE EXAMS ====================
GRAND_CHALLENGE_BANK = {
    "week1": [
        {
            "id": 1,
            "subject": "English",
            "question": "Classroom rule: \"Raise your _______ before speaking.\"",
            "audio": "Classroom rule: Raise your hand before speaking.",
            "options": ["hand", "pencil", "book", "foot"],
            "answer": "hand",
            "explanation": "Nội quy bài học W1E1: \"Raise your hand before speaking\" (Hãy giơ tay xin phép trước khi phát biểu)."
        },
        {
            "id": 2,
            "subject": "English",
            "question": "What is the definition of a NOUN in Grade 3 English?",
            "audio": "What is the definition of a noun?",
            "options": [
                "A person, place, animal, or thing",
                "An action word that we do",
                "A word that describes colours only",
                "A punctuation mark at the end of a sentence"
            ],
            "answer": "A person, place, animal, or thing",
            "explanation": "Định nghĩa chuẩn W1E1: Danh từ (Noun) là từ chỉ Người (doctor), Nơi chốn (school), Con vật (cat), hoặc Đồ vật (banana)."
        },
        {
            "id": 3,
            "subject": "English",
            "question": "Which word in the following list is a VERB (an action word)?",
            "audio": "Which word in the following list is a verb?",
            "options": ["jump", "pencil", "school", "banana"],
            "answer": "jump",
            "explanation": "Động từ (Verb) chỉ hành động chúng ta làm: \"jump\" (nhảy) là động từ, còn pencil, school, banana là danh từ."
        },
        {
            "id": 4,
            "subject": "English",
            "question": "An ADJECTIVE is a word that _______ a noun.",
            "audio": "An adjective is a word that describes a noun.",
            "options": ["describes", "eats", "counts", "destroys"],
            "answer": "describes",
            "explanation": "Quy tắc ngữ pháp W1E2: \"An adjective is a word that describes a noun\" (Tính từ dùng để miêu tả đặc điểm danh từ)."
        },
        {
            "id": 5,
            "subject": "English",
            "question": "In the sentence: \"A cat jumps over the house\", which word is the VERB?",
            "audio": "In the sentence: A cat jumps over the house, which word is the verb?",
            "options": ["jumps", "cat", "house", "over"],
            "answer": "jumps",
            "explanation": "Trong bài tập Thám tử ngữ pháp W1E2: \"cat\" và \"house\" là Danh từ (Nouns), \"jumps\" (nhảy) là Động từ (Verb)."
        },
        {
            "id": 6,
            "subject": "Mathematics",
            "question": "In the Summer Vacation tally chart: Đà Lạt has 5 tallies (|||| crossed) and Hà Nội has 4 tallies (||||). Which destination is MORE popular?",
            "audio": "Which destination is more popular: Da Lat or Ha Noi?",
            "options": [
                "Đà Lạt (5 > 4)",
                "Hà Nội (4)",
                "Both are equal",
                "Vũng Tàu (1)"
            ],
            "answer": "Đà Lạt (5 > 4)",
            "explanation": "Bảng số liệu W1M: Đà Lạt có 5 gạch kiểm đếm, Hà Nội có 4 gạch. Vì 5 > 4 nên Đà Lạt là điểm đến phổ biến hơn (Most popular)."
        },
        {
            "id": 7,
            "subject": "Mathematics",
            "question": "In a pictogram, the key says: 1 🙂 = 2 students. How many students do 3 smileys (🙂 🙂 🙂) represent?",
            "audio": "In a pictogram, if one smiley equals two students, how many students do three smileys represent?",
            "options": ["6 students", "3 students", "5 students", "8 students"],
            "answer": "6 students",
            "explanation": "Toán biểu đồ tranh W1M: 3 biểu tượng 🙂 x 2 học sinh = 6 học sinh (3 x 2 = 6)."
        },
        {
            "id": 8,
            "subject": "Science",
            "question": "What is LIGHT?",
            "audio": "What is light?",
            "options": [
                "An energy we use to see the world around us",
                "A solid obstacle that creates darkness",
                "A buzzing sound made by machines",
                "Something that only exists at midnight"
            ],
            "answer": "An energy we use to see the world around us",
            "explanation": "Khái niệm cốt lõi W1S: \"Light is an energy we use to see the world around us. We need light to see\" (Ánh sáng là dạng năng lượng giúp ta nhìn thấy thế giới xung quanh)."
        },
        {
            "id": 9,
            "subject": "Science",
            "question": "Which of the following is a REFLECTOR (does NOT make its own light, only bounces light)?",
            "audio": "Which of the following is a reflector?",
            "options": ["A mirror", "The Sun", "A torch", "A burning candle"],
            "answer": "A mirror",
            "explanation": "Phân loại W1S: Mặt Trời, đèn pin và nến là nguồn sáng (Light sources). Chiếc gương (A mirror) chỉ phản xạ lại ánh sáng (Reflector)."
        },
        {
            "id": 10,
            "subject": "Science",
            "question": "The Sun, stars, and fire are all examples of:",
            "audio": "The Sun, stars, and fire are all examples of natural light or man-made light?",
            "options": [
                "Natural light (Ánh sáng tự nhiên)",
                "Man-made light (Ánh sáng nhân tạo)",
                "Reflectors (Vật phản xạ)",
                "Opaque objects (Vật cản sáng)"
            ],
            "answer": "Natural light (Ánh sáng tự nhiên)",
            "explanation": "Phân loại W1S: Mặt Trời, ngôi sao và lửa là nguồn sáng tự nhiên (Natural light). Đèn pin, bóng đèn là nhân tạo (Man-made light)."
        }
    ],
    "week2": [
        {
            "id": 1,
            "subject": "English",
            "question": "A STATEMENT tells something. It begins with a capital letter and ends with a _______.",
            "audio": "A statement tells something and ends with a what?",
            "options": ["full stop (.)", "question mark (?)", "comma (,)", "exclamation mark (!)"],
            "answer": "full stop (.)",
            "explanation": "Quy tắc câu trần thuật W2E1: Câu kể (Statement) kể lại một việc và kết thúc bằng dấu chấm (full stop .)."
        },
        {
            "id": 2,
            "subject": "English",
            "question": "A QUESTION asks something. It begins with a capital letter and ends with a _______.",
            "audio": "A question asks something and ends with a what?",
            "options": ["question mark (?)", "full stop (.)", "comma (,)", "colon (:)"],
            "answer": "question mark (?)",
            "explanation": "Quy tắc câu hỏi W2E1: Câu hỏi (Question) bắt đầu bằng động từ/từ để hỏi và kết thúc bằng dấu hỏi (question mark ?)."
        },
        {
            "id": 3,
            "subject": "English",
            "question": "Complete the question for ONE singular object: \"_______ a melon on the plate?\"",
            "audio": "Complete the question: blank a melon on the plate?",
            "options": ["Was there", "Were there", "Did there", "Are there"],
            "answer": "Was there",
            "explanation": "Quy tắc ngữ pháp W2E1: Dùng \"Was there a / an...\" cho 1 đồ vật số ít (a melon: singular)."
        },
        {
            "id": 4,
            "subject": "English",
            "question": "Complete the question for PLURAL objects: \"_______ chocolates in the box?\"",
            "audio": "Complete the question: blank chocolates in the box?",
            "options": ["Were there some", "Was there a", "Is there a", "Did there some"],
            "answer": "Were there some",
            "explanation": "Quy tắc ngữ pháp W2E1: Dùng \"Were there some...\" cho danh từ số nhiều (chocolates: plural)."
        },
        {
            "id": 5,
            "subject": "English",
            "question": "What is the past simple form of the irregular verb \"eat\"?",
            "audio": "What is the past simple form of the irregular verb eat?",
            "options": ["ate", "eated", "eating", "eaten"],
            "answer": "ate",
            "explanation": "Bảng động từ bất quy tắc W2E2: \"eat\" đổi thành \"ate\" (tuyệt đối không thêm -ed thành eated)."
        },
        {
            "id": 6,
            "subject": "English",
            "question": "Transform the statement into a past question: \"She walked to school.\"",
            "audio": "Transform the statement into a past question: She walked to school.",
            "options": [
                "Did she walk to school?",
                "Did she walked to school?",
                "Was she walked to school?",
                "Does she walk to school?"
            ],
            "answer": "Did she walk to school?",
            "explanation": "Công thức câu hỏi quá khứ W2E2: Did + S + V(nguyên mẫu)? Khi có trợ động từ \"Did\", động từ \"walked\" phải về nguyên mẫu \"walk\"."
        },
        {
            "id": 7,
            "subject": "Mathematics",
            "question": "Compare using the Crocodile Rule: 450 _______ 540",
            "audio": "Compare four hundred and fifty and five hundred and forty.",
            "options": [
                "< (450 is less than 540)",
                "> (450 is greater than 540)",
                "=",
                "+"
            ],
            "answer": "< (450 is less than 540)",
            "explanation": "Quy tắc cá sấu W2M: Miệng cá sấu luôn há to về phía số lớn hơn (540 > 450, tức 450 < 540)."
        },
        {
            "id": 8,
            "subject": "Mathematics",
            "question": "In the recycling project: Class 3A collected 350 bottles. Class 3B collected 420 bottles. Which statement is TRUE?",
            "audio": "Class 3A collected 350 bottles. Class 3B collected 420 bottles. Which statement is true?",
            "options": [
                "Class 3B collected more (420 > 350)",
                "Class 3A collected more (350 > 420)",
                "Both classes collected equal bottles",
                "Class 3B collected fewer bottles"
            ],
            "answer": "Class 3B collected more (420 > 350)",
            "explanation": "Bài toán thực tế tái chế rác W2M: 420 > 350, do đó lớp 3B thu gom được nhiều hơn lớp 3A."
        },
        {
            "id": 9,
            "subject": "Science",
            "question": "Light always travels in a _______ and cannot bend around corners.",
            "audio": "Light always travels in a what line?",
            "options": ["straight line", "curved wave", "circle", "zigzag line"],
            "answer": "straight line",
            "explanation": "Định luật truyền sáng W2S: Ánh sáng luôn truyền theo đường thẳng (straight line) và không thể tự bẻ cong qua vật cản."
        },
        {
            "id": 10,
            "subject": "Science",
            "question": "An object is _______ when it BLOCKS light completely and casts a dark shadow (like a wooden door or textbook).",
            "audio": "An object is what when it blocks light completely?",
            "options": ["opaque", "transparent", "translucent", "reflective"],
            "answer": "opaque",
            "explanation": "Phân loại vật liệu W2S: Vật đục cản sáng (Opaque) ngăn chặn 100% ánh sáng đi qua và tạo ra bóng đen (shadow)."
        }
    ],
    "week3": [
        {
            "id": 1,
            "subject": "English",
            "question": "In the story \"Professor Inkspot's Telescope\", what time did Billy wake up to a loud BANG?",
            "audio": "What time was it when Billy woke up in the story?",
            "options": [
                "Half past six (6:30)",
                "Seven o'clock (7:00)",
                "Eight o'clock (8:00)",
                "Half past seven (7:30)"
            ],
            "answer": "Half past six (6:30)",
            "explanation": "Chi tiết mở đầu câu chuyện trong slide W3E1: \"Bang! Billy woke up with a start at half past six in the morning.\""
        },
        {
            "id": 2,
            "subject": "English",
            "question": "What did Billy see coming from Professor Inkspot's shed next door?",
            "audio": "What did Billy see coming from Professor Inkspot's shed?",
            "options": [
                "A small cloud of blue smoke",
                "A flock of birds",
                "A shower of sparks",
                "Rain and snow"
            ],
            "answer": "A small cloud of blue smoke",
            "explanation": "Chi tiết câu chuyện slide W3E1: Billy nhìn ra ngoài và thấy \"a small cloud of blue smoke\" (làn khói nhỏ màu xanh lam) bốc lên từ gian nhà kho."
        },
        {
            "id": 3,
            "subject": "English",
            "question": "What action verb do we use with a DIAL on the machine?",
            "audio": "What action verb do we use with a dial on the machine?",
            "options": ["turn a dial", "push a dial", "pull a dial", "press a dial"],
            "answer": "turn a dial",
            "explanation": "Cụm từ máy móc slide W3E1: \"turn a dial\" (xoay núm vặn tròn chia vạch)."
        },
        {
            "id": 4,
            "subject": "English",
            "question": "What action verb do we use with a HANDLE beside the square screen?",
            "audio": "What action verb do we use with a handle beside the screen?",
            "options": ["pull a handle", "push a handle", "turn a handle", "type a handle"],
            "answer": "pull a handle",
            "explanation": "Cụm từ máy móc slide W3E1: \"pull a handle\" (kéo chiếc cần gạt xuống)."
        },
        {
            "id": 5,
            "subject": "English",
            "question": "\"_______ did you eat the teacher's bánh mì?\" — \"Because I was hungry!\"",
            "audio": "Blank did you eat the teacher's bánh mì? Because I was hungry.",
            "options": ["Why", "Who", "Where", "When"],
            "answer": "Why",
            "explanation": "Quy tắc từ để hỏi W3E2: \"Why\" hỏi về lý do/nguyên nhân, câu trả lời bắt đầu bằng \"Because\" (Bởi vì...)."
        },
        {
            "id": 6,
            "subject": "Mathematics",
            "question": "What number is represented by: 5 Hundreds + 6 Tens + 9 Ones?",
            "audio": "What number is represented by 5 Hundreds, 6 Tens, and 9 Ones?",
            "options": ["569", "659", "596", "965"],
            "answer": "569",
            "explanation": "Giá trị vị trí hàng số slide W3M: 5 Hàng Trăm + 6 Hàng Chục + 9 Hàng Đơn vị = 569."
        },
        {
            "id": 7,
            "subject": "Mathematics",
            "question": "How do you write the number 835 in EXPANDED FORM?",
            "audio": "How do you write 835 in expanded form?",
            "options": [
                "800 + 30 + 5",
                "800 + 50 + 3",
                "80 + 30 + 5",
                "800 + 300 + 5"
            ],
            "answer": "800 + 30 + 5",
            "explanation": "Dạng khai triển số W3M: $835 = 800 + 30 + 5$ (tách rõ giá trị từng hàng: 8 Trăm, 3 Chục, 5 Đơn vị)."
        },
        {
            "id": 8,
            "subject": "Science",
            "question": "How many MILK TEETH (baby teeth) do young children under six years old have?",
            "audio": "How many milk teeth do young children have?",
            "options": ["20 teeth", "32 teeth", "28 teeth", "16 teeth"],
            "answer": "20 teeth",
            "explanation": "Kiến thức nha khoa slide W3S: Trẻ em dưới sáu tuổi có đúng 20 chiếc răng sữa (milk teeth). Người lớn có 32 răng vĩnh viễn (permanent teeth)."
        },
        {
            "id": 9,
            "subject": "Science",
            "question": "Which type of teeth are flat and sharp like a CHISEL, used for SLICING and CUTTING food (like biting an apple)?",
            "audio": "Which teeth are shaped like a chisel and used for slicing?",
            "options": [
                "Incisors (Răng cửa)",
                "Canines (Răng nanh)",
                "Premolars (Răng tiền hàm)",
                "Molars (Răng hàm)"
            ],
            "answer": "Incisors (Răng cửa)",
            "explanation": "Chức năng răng slide W3S: Răng cửa (Incisors - 8 chiếc) có rìa phẳng sắc như lưỡi đục, chuyên dùng để cắn và cắt lát thức ăn (slice and cut)."
        },
        {
            "id": 10,
            "subject": "Science",
            "question": "Which teeth are the LARGEST teeth at the back with a flat bumpy surface, used for GRINDING food finely?",
            "audio": "Which teeth are the largest teeth used for grinding food?",
            "options": [
                "Molars (Răng hàm)",
                "Incisors (Răng cửa)",
                "Canines (Răng nanh)",
                "Premolars (Răng tiền hàm)"
            ],
            "answer": "Molars (Răng hàm)",
            "explanation": "Chức năng răng slide W3S: Răng hàm (Molars - 12 chiếc) là những chiếc răng lớn nhất ở sâu trong cùng, mặt phẳng gồ ghề dùng để nghiền nát thức ăn (grind food)."
        }
    ],
    "week4": [
        {
            "id": 1,
            "subject": "English",
            "question": "In the story \"Professor Inkspot's Telescope\", what time did Billy jump out of bed when he heard the loud BANG?",
            "audio": "What time did Billy jump out of bed when he heard the loud BANG?",
            "options": [
                "Half past six (6:30)",
                "Seven o'clock (7:00)",
                "Eight o'clock (8:00)",
                "Nine o'clock (9:00)"
            ],
            "answer": "Half past six (6:30)",
            "explanation": "Chi tiết cốt truyện trong Language Book p. 14: \"Bang! Billy woke up with a start at half past six in the morning.\" (Billy nhảy ra khỏi giường lúc 6:30 sáng)."
        },
        {
            "id": 2,
            "subject": "English",
            "question": "Which verb correctly completes the phrase: \"We _______ a switch to turn on the machine's power\"?",
            "audio": "Which verb correctly completes: We blank a switch to turn on the machine's power?",
            "options": ["press a switch", "turn a switch", "pull a switch", "push a switch"],
            "answer": "press a switch",
            "explanation": "Cụm động từ máy móc chuẩn slide: \"press a switch\" (bật/gạt công tắc điện), \"turn a dial\" (xoay núm vặn), \"pull a handle\" (kéo cần gạt), \"push a button\" (bấm nút tròn)."
        },
        {
            "id": 3,
            "subject": "English",
            "question": "What does the word TRUE mean in Grade 3 English?",
            "audio": "What does the word true mean in English?",
            "options": [
                "Something that is correct or real (a fact)",
                "Something that is not correct or not real",
                "A fictional make-up story",
                "A question without an answer"
            ],
            "answer": "Something that is correct or real (a fact)",
            "explanation": "Định nghĩa chuẩn trong slide: \"True means something that is correct or real. It is a fact.\" (True nghĩa là điều gì đó chính xác hoặc có thật - là một sự thật)."
        },
        {
            "id": 4,
            "subject": "English",
            "question": "What is the past simple tense of the regular verb \"look\"?",
            "audio": "What is the past simple tense of the regular verb look?",
            "options": ["looked", "looking", "looks", "lookt"],
            "answer": "looked",
            "explanation": "Quy tắc quá khứ đơn có quy tắc: Động từ regular thêm đuôi -ed: look &rarr; looked (Billy looked inside the shed)."
        },
        {
            "id": 5,
            "subject": "English",
            "question": "According to Cambridge rules (Practice Book p. 5), where must the comma (,) go in direct speech?",
            "audio": "According to Cambridge rules, where must the comma go in direct speech?",
            "options": [
                "INSIDE the speech marks: “I like reading,” Emma said.",
                "OUTSIDE the speech marks: “I like reading”, Emma said.",
                "At the start of the sentence before speech marks",
                "After the reporting verb: “I like reading” Emma, said."
            ],
            "answer": "INSIDE the speech marks: “I like reading,” Emma said.",
            "explanation": "Quy tắc dấu lời thoại chuẩn Cambridge (Practice Book p. 5): Dấu phẩy (,) BẮT BUỘC phải nằm BÊN TRONG dấu ngoặc kép: “Look at my book,” Ben said."
        },
        {
            "id": 6,
            "subject": "Mathematics",
            "question": "In the number 475, what is the PLACE VALUE of digit 7?",
            "audio": "In the number 475, what is the place value of digit 7?",
            "options": [
                "70 (7 tens)",
                "7 (7 ones)",
                "700 (7 hundreds)",
                "475"
            ],
            "answer": "70 (7 tens)",
            "explanation": "Giá trị hàng số slide W4M: Chữ số 7 nằm ở hàng Chục (Tens) nên có giá trị là 70 (Place value = 70)."
        },
        {
            "id": 7,
            "subject": "Mathematics",
            "question": "What is the correct EXPANDED FORM of the number 569?",
            "audio": "What is the correct expanded form of the number 569?",
            "options": [
                "500 + 60 + 9",
                "50 + 60 + 9",
                "500 + 6 + 9",
                "500 + 69"
            ],
            "answer": "500 + 60 + 9",
            "explanation": "Dạng khai triển số: 569 gồm 5 Hàng Trăm (500), 6 Hàng Chục (60) và 9 Hàng Đơn vị (9) &rarr; 569 = 500 + 60 + 9."
        },
        {
            "id": 8,
            "subject": "Mathematics",
            "question": "On a number line, what is the exact HALFWAY POINT (midpoint) between 20 and 30?",
            "audio": "On a number line, what is the exact halfway point between 20 and 30?",
            "options": ["25", "22", "28", "20"],
            "answer": "25",
            "explanation": "Điểm chính giữa (midpoint) slide W4M: Điểm chính giữa giữa 20 và 30 là 25 (20 + 5 = 25). Tương tự: giữa 0 và 100 là 50, giữa 40 và 50 là 45."
        },
        {
            "id": 9,
            "subject": "Science",
            "question": "Which statement about LIGHT is scientifically correct?",
            "audio": "Which statement about light is scientifically correct?",
            "options": [
                "Light always travels in a straight line and cannot bend",
                "Light always bends around corners easily",
                "Light travels in a zigzag circle",
                "Transparent materials block light completely"
            ],
            "answer": "Light always travels in a straight line and cannot bend",
            "explanation": "Đặc tính truyền sáng slide W4S: \"Light travels in straight lines; cannot bend or move around corners.\" (Ánh sáng luôn truyền theo đường thẳng, không thể tự bẻ cong quanh góc tường)."
        },
        {
            "id": 10,
            "subject": "Science",
            "question": "At 12 p.m. (midday) when the Sun is directly overhead, what happens to tree shadows?",
            "audio": "At 12 p.m. midday when the Sun is directly overhead, what happens to tree shadows?",
            "options": [
                "The shadow is the SHORTEST, gathered right under the tree",
                "The shadow is the LONGEST, stretching far to the West",
                "The shadow disappears and turns into rainbow colours",
                "The shadow is identical to the shadow at 8 a.m."
            ],
            "answer": "The shadow is the SHORTEST, gathered right under the tree",
            "explanation": "Quy luật bóng Mặt Trời slide W4S (p. 23-26): Lúc 12 giờ trưa (midday) khi Mặt Trời lên cao nhất trên đỉnh đầu, bóng cây ngắn nhất (shortest) thu tròn dưới gốc cây. Sáng sớm (8 a.m.) và chiều muộn (5 p.m.) bóng đổ dài nhất (longest)."
        }
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
    limit = request.args.get('limit', type=int)
    import random

    if week == 'all':
        all_words = []
        for w_key in VOCABULARY_BANK:
            for item in VOCABULARY_BANK[w_key]:
                item_copy = dict(item)
                item_copy['week'] = w_key
                all_words.append(item_copy)
        if limit and limit > 0 and len(all_words) > limit:
            random.shuffle(all_words)
            return jsonify(all_words[:limit])
        return jsonify(all_words)
    else:
        words = [dict(item) for item in VOCABULARY_BANK.get(week, [])]
        for item in words:
            item['week'] = week
        if limit and limit > 0 and len(words) > limit:
            random.shuffle(words)
            return jsonify(words[:limit])
        return jsonify(words)

@app.route('/api/grand_challenge')
def get_grand_challenge():
    week = request.args.get('week', 'week3')
    questions = GRAND_CHALLENGE_BANK.get(week, GRAND_CHALLENGE_BANK.get('week3', []))
    return jsonify(questions)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response

@app.route('/api/submit_attempt', methods=['POST', 'OPTIONS'])
def submit_attempt():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True}), 200

    data = request.json or {}
    student_name = (data.get('student_name') or 'Student').strip()
    if not student_name:
        student_name = 'Student'
    week = data.get('week', 'week4')
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

@app.route('/api/record_vocab', methods=['POST', 'OPTIONS'])
def record_vocab():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True}), 200

    data = request.json or {}
    student_name = (data.get('student_name') or 'Student').strip()
    if not student_name:
        student_name = 'Student'
    word = data.get('word', '').strip().lower()
    week = data.get('week', 'week4')
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

        # 3. High-risk Weak Words & Mistake Questions combined
        weak_words_rows = conn.execute('''
            SELECT word, week, SUM(times_wrong) as total_wrong, SUM(times_correct) as total_correct
            FROM vocab_stats
            GROUP BY word
            HAVING total_wrong > 0
            UNION ALL
            SELECT question_or_word as word, week, COUNT(*) as total_wrong, 0 as total_correct
            FROM mistakes_log
            GROUP BY question_or_word
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
