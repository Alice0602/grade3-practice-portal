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
    ],
    "week5": [
        {
                "word": "beginning",
                "meaning": "the start of a story introducing characters and setting",
                "vietnamese": "Mở đầu câu chuyện: giới thiệu nhân vật (Characters) và bối cảnh (Setting)",
                "mnemonic": "Bắt đầu câu chuyện luôn cho ta biết: Ai ở đâu và khi nào? 🌅",
                "colloc": "The beginning introduces characters and setting",
                "colloc_vi": "Phần mở đầu giới thiệu các nhân vật và bối cảnh",
                "audio": "beginning. The start of a story.",
                "type": "story",
                "svg_type": "default",
                "emoji": "🌅"
        },
        {
                "word": "middle",
                "meaning": "the main part where a problem or event happens",
                "vietnamese": "Thân truyện: diễn biến sự kiện hoặc một vấn đề rắc rối xảy ra",
                "mnemonic": "Phần giữa truyện luôn có kịch tính, sự cố xảy ra cần giải quyết 🌪️.",
                "colloc": "A big problem happens in the middle",
                "colloc_vi": "Một vấn đề lớn xảy ra ở phần thân truyện",
                "audio": "middle. The main part where a problem happens.",
                "type": "story",
                "svg_type": "default",
                "emoji": "🌪️"
        },
        {
                "word": "end",
                "meaning": "the conclusion where the problem is solved",
                "vietnamese": "Kết truyện: cách vấn đề được tháo gỡ và giải quyết ổn thỏa",
                "mnemonic": "Kết thúc có hậu, cỗ máy hoạt động hoặc bài học được rút ra 🏁.",
                "colloc": "The problem is solved at the end",
                "colloc_vi": "Vấn đề được giải quyết ở phần kết truyện",
                "audio": "end. The conclusion where the problem is solved.",
                "type": "story",
                "svg_type": "default",
                "emoji": "🏁"
        },
        {
                "word": "character",
                "meaning": "a person, animal or creature in a story",
                "vietnamese": "Nhân vật: người, động vật hoặc sinh vật trong truyện",
                "mnemonic": "Nhân vật trả lời cho câu hỏi: Who is in the story? (Ai trong truyện?) 🧙",
                "colloc": "Professor Inkspot and Billy are main characters",
                "colloc_vi": "Giáo sư Inkspot và Billy là các nhân vật chính",
                "audio": "character. A person or creature in a story.",
                "type": "story",
                "svg_type": "default",
                "emoji": "🧙"
        },
        {
                "word": "setting",
                "meaning": "where and when a story takes place",
                "vietnamese": "Bối cảnh: địa điểm (Where) và thời gian (When) diễn ra câu chuyện",
                "mnemonic": "Bối cảnh trả lời câu hỏi: Where and When? (Ở đâu và vào lúc nào?) 🏡",
                "colloc": "The setting was a wooden shed one morning",
                "colloc_vi": "Bối cảnh là một gian nhà kho bằng gỗ vào một buổi sáng",
                "audio": "setting. Where and when a story takes place.",
                "type": "story",
                "svg_type": "default",
                "emoji": "🏡"
        },
        {
                "word": "problem",
                "meaning": "something that goes wrong and needs to be fixed",
                "vietnamese": "Vấn đề rắc rối: sự việc trục trặc xảy ra cần được giải quyết",
                "mnemonic": "Cỗ máy xì khói xanh hoặc phát ra tiếng nổ lạ ⚠️.",
                "colloc": "The loud noise was a sudden problem",
                "colloc_vi": "Tiếng ồn lớn là một vấn đề bất ngờ xảy ra",
                "audio": "problem. Something that goes wrong.",
                "type": "story",
                "svg_type": "default",
                "emoji": "⚠️"
        },
        {
                "word": "solution",
                "meaning": "the way a problem is fixed or resolved",
                "vietnamese": "Giải pháp: cách thức tháo gỡ hoặc khắc phục vấn đề",
                "mnemonic": "Ý tưởng thông minh để sửa chữa cỗ máy và kết thúc câu chuyện 💡.",
                "colloc": "Billy found a clever solution",
                "colloc_vi": "Billy đã tìm ra một giải pháp thông minh",
                "audio": "solution. The way a problem is fixed.",
                "type": "story",
                "svg_type": "default",
                "emoji": "💡"
        },
        {
                "word": "woke up",
                "meaning": "past form of wake up: stopped sleeping",
                "vietnamese": "Đã tỉnh giấc: dạng quá khứ bất quy tắc của wake up",
                "mnemonic": "Chữ a biến thành o (wake up &rarr; woke up) ⏰ lúc 6:30 sáng.",
                "colloc": "Billy woke up at half past six",
                "colloc_vi": "Billy đã thức giấc vào lúc 6 giờ 30 phút sáng",
                "audio": "woke up. Past simple of wake up.",
                "type": "grammar",
                "svg_type": "default",
                "emoji": "⏰"
        },
        {
                "word": "found",
                "meaning": "past form of find: discovered something",
                "vietnamese": "Đã tìm thấy / phát hiện ra: dạng quá khứ của find",
                "mnemonic": "Tìm thấy cỗ máy bí ẩn trong nhà kho: find đổi thành found 🔍.",
                "colloc": "They found a mysterious machine in the shed",
                "colloc_vi": "Họ đã tìm thấy một cỗ máy bí ẩn trong gian nhà kho",
                "audio": "found. Past simple of find.",
                "type": "grammar",
                "svg_type": "default",
                "emoji": "🔍"
        },
        {
                "word": "heard",
                "meaning": "past form of hear: perceived a sound",
                "vietnamese": "Đã nghe thấy: dạng quá khứ của hear (thêm d)",
                "mnemonic": "Đôi tai nghe thấy tiếng nổ lớn: hear thêm d thành heard 👂.",
                "colloc": "He heard a loud BANG outside",
                "colloc_vi": "Cậu ấy đã nghe thấy một tiếng nổ lớn bên ngoài",
                "audio": "heard. Past simple of hear.",
                "type": "grammar",
                "svg_type": "default",
                "emoji": "👂"
        },
        {
                "word": "said",
                "meaning": "past form of say: spoke words",
                "vietnamese": "Đã nói: dạng quá khứ bất quy tắc của say",
                "mnemonic": "Giáo sư nói lời chào: say đổi thành said 💬.",
                "colloc": "Professor Inkspot said hello to Billy",
                "colloc_vi": "Giáo sư Inkspot đã nói lời chào với Billy",
                "audio": "said. Past simple of say.",
                "type": "grammar",
                "svg_type": "default",
                "emoji": "💬"
        },
        {
                "word": "partitioning",
                "meaning": "breaking numbers into hundreds, tens, and ones to add or subtract",
                "vietnamese": "Tách số theo hàng: phân tách số thành Trăm, Chục, Đơn vị để tính nhanh",
                "mnemonic": "Tách $341 = 300 + 40 + 1$ ghép thành từng mảnh ghép dễ tính 🧩.",
                "colloc": "Use partitioning to add 341 and 526",
                "colloc_vi": "Dùng cách tách số để cộng 341 và 526",
                "audio": "partitioning. Breaking numbers into parts.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "🧩"
        },
        {
                "word": "column addition",
                "meaning": "adding numbers written vertically in columns",
                "vietnamese": "Đặt tính rồi tính cộng: đặt các hàng đơn vị, chục, trăm thẳng cột",
                "mnemonic": "Xếp các con số thẳng hàng dọc rồi cộng từ phải sang trái ➕.",
                "colloc": "Align the digits for column addition",
                "colloc_vi": "Xếp thẳng hàng các chữ số khi đặt tính cộng",
                "audio": "column addition. Adding numbers vertically.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "➕"
        },
        {
                "word": "regrouping",
                "meaning": "carrying ten to the next column when adding or borrowing when subtracting",
                "vietnamese": "Nhớ sang hàng kế tiếp khi cộng hoặc mượn khi trừ",
                "mnemonic": "Hàng chục cộng lại ra 12 thì viết 2 nhớ 1 sang hàng trăm 🔄.",
                "colloc": "Regroup 12 tens into 1 hundred and 2 tens",
                "colloc_vi": "Chuyển 12 chục thành 1 trăm và 2 chục",
                "audio": "regrouping. Carrying or borrowing numbers.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "🔄"
        },
        {
                "word": "digestive system",
                "meaning": "the body organs that break down food into energy and nutrients",
                "vietnamese": "Hệ tiêu hóa: chuỗi các cơ quan phân hủy thức ăn để nuôi sống cơ thể",
                "mnemonic": "Thức ăn bắt đầu từ miệng và đi qua cả một hệ thống tiêu hóa kỳ diệu 🥪.",
                "colloc": "Food travels through the digestive system",
                "colloc_vi": "Thức ăn di chuyển qua toàn bộ hệ tiêu hóa",
                "audio": "digestive system. Organs that break down food.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🥪"
        },
        {
                "word": "saliva",
                "meaning": "liquid in the mouth that softens food and starts digestion",
                "vietnamese": "Nước bọt: chất lỏng trong khoang miệng làm mềm và bước đầu tiêu hóa thức ăn",
                "mnemonic": "Nước bọt tiết ra làm ướt thức ăn giúp răng nhai và họng nuốt dễ dàng 💧.",
                "colloc": "Saliva softens food in the mouth",
                "colloc_vi": "Nước bọt làm mềm thức ăn trong khoang miệng",
                "audio": "saliva. Liquid in the mouth that softens food.",
                "type": "science",
                "svg_type": "default",
                "emoji": "💧"
        },
        {
                "word": "oesophagus",
                "meaning": "the muscular tube connecting the mouth to the stomach (gullet)",
                "vietnamese": "Thực quản: ống cơ co bóp nhịp nhàng đẩy thức ăn từ miệng xuống dạ dày",
                "mnemonic": "Chiếc ống dẫn dài nối thẳng từ cuống họng xuống dạ dày 🥖.",
                "colloc": "Muscles push food down the oesophagus",
                "colloc_vi": "Cơ bắp co bóp đẩy thức ăn trôi xuống thực quản",
                "audio": "oesophagus. The muscular tube connecting mouth to stomach.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🥖"
        },
        {
                "word": "stomach",
                "meaning": "a muscular sac that mixes food with acids to break it down",
                "vietnamese": "Dạ dày: túi cơ co bóp nhào trộn thức ăn với dịch axit thành chất lỏng",
                "mnemonic": "Chiếc túi cơ bắp nhào lộn thức ăn như máy xay sinh tố 🥣.",
                "colloc": "Acids in the stomach break down food into liquid",
                "colloc_vi": "Axit trong dạ dày phân hủy thức ăn thành dạng lỏng",
                "audio": "stomach. A muscular sac that mixes food with acids.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🥣"
        },
        {
                "word": "small intestine",
                "meaning": "a long folded tube that absorbs essential nutrients into the blood",
                "vietnamese": "Ruột non: ống dài gấp khúc hấp thụ chất dinh dưỡng quý giá vào dòng máu",
                "mnemonic": "Ống ruột dài ngoằn ngoèo lọc lấy toàn bộ vitamin và dưỡng chất nuôi cơ thể 🩸.",
                "colloc": "The small intestine absorbs nutrients into blood",
                "colloc_vi": "Ruột non hấp thụ các chất dinh dưỡng vào máu",
                "audio": "small intestine. Absorbs nutrients into the blood.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🩸"
        }
],
    "week6": [
        {
                "word": "marvellous",
                "meaning": "wonderful, amazing, really really good",
                "vietnamese": "Tuyệt vời, kỳ diệu, phi thường (rất rất tốt)",
                "mnemonic": "Phương thuốc kỳ diệu thần kỳ của cậu bé George ✨.",
                "colloc": "George made a marvellous medicine",
                "colloc_vi": "George đã tạo nên một phương thuốc kỳ diệu",
                "audio": "marvellous. Wonderful and really good.",
                "type": "story",
                "svg_type": "default",
                "emoji": "✨"
        },
        {
                "word": "medicine",
                "meaning": "substance taken to treat illness or feel better",
                "vietnamese": "Thuốc chữa bệnh: dung dịch hoặc viên uống giúp hồi phục sức khỏe",
                "mnemonic": "Uống thuốc đúng giờ để mau khỏi bệnh 💊.",
                "colloc": "Grandma takes four spoons of medicine",
                "colloc_vi": "Bà uống 4 thìa thuốc chữa bệnh",
                "audio": "medicine. Substance taken to treat illness.",
                "type": "story",
                "svg_type": "default",
                "emoji": "💊"
        },
        {
                "word": "grumpy",
                "meaning": "bad-tempered, easily annoyed, always complaining",
                "vietnamese": "Cáu kỉnh, gắt gỏng, khó tính hay càu nhàu",
                "mnemonic": "Khuôn mặt nhăn nhó lúc nào cũng bực mình và cáu gắt 😠.",
                "colloc": "Grandma was very grumpy and cross",
                "colloc_vi": "Bà ngoại rất cáu kỉnh và bực dọc",
                "audio": "grumpy. Bad-tempered and easily annoyed.",
                "type": "story",
                "svg_type": "default",
                "emoji": "😠"
        },
        {
                "word": "mixture",
                "meaning": "different ingredients mixed together to form a new substance",
                "vietnamese": "Hỗn hợp: nhiều chất và nguyên liệu được trộn lẫn vào nhau",
                "mnemonic": "Trộn kem đánh răng, dầu gội và gia vị tạo thành một hỗn hợp kỳ lạ 🧪.",
                "colloc": "He stirred the bubbling mixture",
                "colloc_vi": "Cậu ấy khuấy đều hỗn hợp đang sủi bọt",
                "audio": "mixture. Different ingredients mixed together.",
                "type": "story",
                "svg_type": "default",
                "emoji": "🧪"
        },
        {
                "word": "saucepan",
                "meaning": "a deep metal cooking pot with a long handle",
                "vietnamese": "Chiếc chảo/nồi sâu lòng có cán cầm dài để nấu trên bếp",
                "mnemonic": "Chiếc nồi kim loại sâu lòng có cán dài 🍳 đặt trên bếp lửa.",
                "colloc": "He cooked the medicine in a giant saucepan",
                "colloc_vi": "Cậu ấy đun sôi thuốc trong chiếc nồi cán dài khổng lồ",
                "audio": "saucepan. A cooking pot with a long handle.",
                "type": "story",
                "svg_type": "default",
                "emoji": "🍳"
        },
        {
                "word": "past continuous",
                "meaning": "action that was in progress in the past (was/were + V-ing)",
                "vietnamese": "Thì quá khứ tiếp diễn: hành động đang diễn ra tại thời điểm quá khứ",
                "mnemonic": "Công thức: was/were + V-ing (đang diễn ra trong quá khứ) ⏳.",
                "colloc": "George was mixing the medicine",
                "colloc_vi": "George đang pha chế nồi thuốc",
                "audio": "past continuous. Was or were plus V-ing.",
                "type": "grammar",
                "svg_type": "default",
                "emoji": "⏳"
        },
        {
                "word": "was",
                "meaning": "used with singular subjects (I, he, she, it) in past continuous",
                "vietnamese": "Dùng cho chủ ngữ số ít (I, he, she, it, George, Grandma)",
                "mnemonic": "1 người/vật dùng WAS: George was mixing 👤.",
                "colloc": "Grandma was sleeping in her armchair",
                "colloc_vi": "Bà đang ngủ trong chiếc ghế bành",
                "audio": "was. Used with singular subjects.",
                "type": "grammar",
                "svg_type": "default",
                "emoji": "👤"
        },
        {
                "word": "were",
                "meaning": "used with plural subjects (you, we, they, chickens) in past continuous",
                "vietnamese": "Dùng cho chủ ngữ số nhiều (you, we, they, danh từ số nhiều)",
                "mnemonic": "2 người/vật trở lên dùng WERE: Chickens were running 👥.",
                "colloc": "The brown chickens were running frantically",
                "colloc_vi": "Đàn gà màu nâu đang chạy nhốn nháo",
                "audio": "were. Used with plural subjects.",
                "type": "grammar",
                "svg_type": "default",
                "emoji": "👥"
        },
        {
                "word": "2D shape",
                "meaning": "a flat shape with two dimensions: height and width",
                "vietnamese": "Hình 2 chiều: hình phẳng có 2 kích thước là chiều cao và chiều rộng",
                "mnemonic": "Hình phẳng nằm gọn trên trang giấy: có chiều dài và chiều rộng 📐.",
                "colloc": "A 2D shape has height and width",
                "colloc_vi": "Hình 2 chiều có chiều cao và chiều rộng",
                "audio": "2D shape. A flat shape with height and width.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "📐"
        },
        {
                "word": "quadrilateral",
                "meaning": "any flat 2D shape with exactly four straight sides",
                "vietnamese": "Tứ giác: bất kỳ hình phẳng nào có đúng 4 cạnh thẳng",
                "mnemonic": "Chữ 'quad' nghĩa là 4: hình 4 cạnh (hình vuông, chữ nhật, hình thoi) 🔲.",
                "colloc": "A square is a quadrilateral with 4 equal sides",
                "colloc_vi": "Hình vuông là một tứ giác có 4 cạnh bằng nhau",
                "audio": "quadrilateral. A shape with four straight sides.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "🔲"
        },
        {
                "word": "polygon",
                "meaning": "a closed flat shape with three or more straight sides",
                "vietnamese": "Đa giác: hình phẳng khép kín có từ 3 cạnh thẳng trở lên",
                "mnemonic": "Hình khép kín bằng các đoạn thẳng: tam giác, tứ giác, ngũ giác... 🔷",
                "colloc": "A polygon has straight sides and vertices",
                "colloc_vi": "Đa giác có các cạnh thẳng và các đỉnh góc",
                "audio": "polygon. A closed shape with straight sides.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "🔷"
        },
        {
                "word": "regular shape",
                "meaning": "a shape where all sides are equal and all angles are equal",
                "vietnamese": "Hình đều: hình có tất cả các cạnh bằng nhau và các góc bằng nhau",
                "mnemonic": "Hình vuông là hình đều vì 4 cạnh bằng nhau và 4 góc vuông ⭐.",
                "colloc": "An equilateral triangle is a regular polygon",
                "colloc_vi": "Tam giác đều là một đa giác đều",
                "audio": "regular shape. All sides and angles are equal.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "⭐"
        },
        {
                "word": "symmetry",
                "meaning": "when two halves of a shape match identically across a line",
                "vietnamese": "Tính đối xứng: hai nửa của hình trùng khít nhau qua trục đối xứng",
                "mnemonic": "Gấp đôi hình lại theo đường thẳng mà 2 bên trùng khít như cánh bướm 🦋.",
                "colloc": "The shape has a vertical line of symmetry",
                "colloc_vi": "Hình này có một trục đối xứng thẳng đứng",
                "audio": "symmetry. Two halves match identically.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "🦋"
        },
        {
                "word": "carnivore",
                "meaning": "an animal that eats ONLY meat and hunts prey",
                "vietnamese": "Động vật ăn thịt: loài động vật chỉ ăn thịt của con mồi",
                "mnemonic": "Hổ, sư tử, cá mập 🐅: chỉ săn và ăn thịt tươi sống.",
                "colloc": "A tiger is a carnivore with sharp teeth",
                "colloc_vi": "Hổ là loài ăn thịt có hàm răng sắc bén",
                "audio": "carnivore. An animal that eats only meat.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🐅"
        },
        {
                "word": "herbivore",
                "meaning": "an animal that eats ONLY plants, leaves, and grass",
                "vietnamese": "Động vật ăn cỏ / thực vật: loài chỉ ăn cỏ, cành lá, hoa quả",
                "mnemonic": "Bò, hươu, voi 🐘: ăn cỏ xanh và nghiền nát cành lá.",
                "colloc": "A cow is a herbivore that grazes on grass",
                "colloc_vi": "Bò là loài ăn thực vật gặm cỏ trên đồng",
                "audio": "herbivore. An animal that eats only plants.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🐘"
        },
        {
                "word": "omnivore",
                "meaning": "an animal that eats BOTH meat and plants",
                "vietnamese": "Động vật ăn tạp: loài ăn cả thịt và thực vật (rau củ quả)",
                "mnemonic": "Con người và gấu 🐻: ăn cả cá, thịt và rau củ quả.",
                "colloc": "Humans and bears are omnivores",
                "colloc_vi": "Con người và gấu là những loài ăn tạp",
                "audio": "omnivore. An animal that eats meat and plants.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🐻"
        },
        {
                "word": "sharp canines",
                "meaning": "long pointed teeth used by carnivores to grip and tear meat",
                "vietnamese": "Răng nanh nhọn sắc: vũ khí của động vật ăn thịt để ngoạm và xé thịt",
                "mnemonic": "Răng nanh nhọn như dao găm 🦷 giúp hổ và cá mập xé thịt con mồi.",
                "colloc": "Carnivores need sharp canines to tear meat",
                "colloc_vi": "Động vật ăn thịt cần răng nanh nhọn để xé thịt",
                "audio": "sharp canines. Long pointed teeth to tear meat.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🦷"
        },
        {
                "word": "flat molars",
                "meaning": "broad flat teeth used by herbivores to grind tough plant fibers",
                "vietnamese": "Răng hàm to phẳng: răng của động vật ăn cỏ để nghiền nát chất xơ thực vật",
                "mnemonic": "Mặt răng phẳng rộng như cối xay 🪨 giúp bò và ngựa nhai nghiền cỏ khô.",
                "colloc": "Herbivores have flat molars for chewing grass",
                "colloc_vi": "Động vật ăn cỏ có răng hàm phẳng để nhai cỏ",
                "audio": "flat molars. Broad teeth used to grind plants.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🪨"
        }
],
    "week7": [
        {
                "word": "plus",
                "meaning": "the addition symbol (+), means to add or put together",
                "vietnamese": "Dấu cộng (+): biểu thị phép tính cộng gộp các số lại với nhau",
                "mnemonic": "Thấy dấu thập đỏ ➕ là ta làm phép cộng (add).",
                "colloc": "When we see a plus symbol, we need to add",
                "colloc_vi": "Khi thấy dấu cộng, ta cần thực hiện phép tính cộng",
                "audio": "plus. The addition symbol, means to add.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "➕"
        },
        {
                "word": "minus",
                "meaning": "the subtraction symbol (-), means to take away or subtract",
                "vietnamese": "Dấu trừ (-): biểu thị phép tính trừ bớt đi từ một số",
                "mnemonic": "Thấy dấu gạch ngang ➖ là ta làm phép trừ bớt đi (subtract).",
                "colloc": "When we see a minus symbol, we need to subtract",
                "colloc_vi": "Khi thấy dấu trừ, ta cần thực hiện phép tính trừ",
                "audio": "minus. The subtraction symbol, means to subtract.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "➖"
        },
        {
                "word": "number pattern",
                "meaning": "a repeated or predictable sequence of numbers",
                "vietnamese": "Quy luật số: chuỗi số lặp lại theo một trật tự dễ nhận biết",
                "mnemonic": "Quy luật chữ số hàng đơn vị giúp tính nhẩm siêu tốc 🔢.",
                "colloc": "Identify the addition number pattern",
                "colloc_vi": "Nhận biết quy luật của phép tính cộng",
                "audio": "number pattern. A repeated sequence of numbers.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "🔢"
        },
        {
                "word": "ones place",
                "meaning": "the last digit on the right representing individual units",
                "vietnamese": "Hàng đơn vị: vị trí chữ số ngoài cùng bên phải của một số",
                "mnemonic": "Cộng 2 vào số có đuôi 2 luôn cho chữ số 4 ở hàng đơn vị 1️⃣.",
                "colloc": "Adding 2 to 42 gives 4 in the ones place",
                "colloc_vi": "Cộng 2 vào 42 cho chữ số 4 ở hàng đơn vị",
                "audio": "ones place. The last digit on the right.",
                "type": "maths",
                "svg_type": "default",
                "emoji": "1️⃣"
        },
        {
                "word": "roots",
                "meaning": "the underground plant part that absorbs water and anchors the plant",
                "vietnamese": "Rễ cây: bộ phận nằm trong lòng đất hút nước và giữ chặt cây",
                "mnemonic": "Rễ cây cắm sâu vào đất hút nước 🥕 như hàng triệu ống hút nhỏ.",
                "colloc": "Roots absorb water from the soil",
                "colloc_vi": "Rễ cây hút nước từ trong lòng đất",
                "audio": "roots. Absorbs water and anchors the plant.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🥕"
        },
        {
                "word": "stem",
                "meaning": "the main plant stalk that supports leaves and transports water",
                "vietnamese": "Thân cây: nâng đỡ cành lá vươn lên và vận chuyển nước từ rễ lên lá",
                "mnemonic": "Thân cây như xa lộ giao thông 🌱 đưa dòng nước lên tận các cành lá.",
                "colloc": "The stem supports the plant and transports water",
                "colloc_vi": "Thân cây nâng đỡ cây và vận chuyển nước",
                "audio": "stem. Supports the plant and transports water.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🌱"
        },
        {
                "word": "leaves",
                "meaning": "plural of leaf; green parts that use sunlight to make food/energy",
                "vietnamese": "Lá cây (số nhiều của leaf): dùng ánh sáng mặt trời để tạo thức ăn (quang hợp)",
                "mnemonic": "1 chiếc lá là leaf, nhiều chiếc lá là leaves 🍃 hứng ánh nắng mặt trời.",
                "colloc": "Leaves use sunlight to make energy",
                "colloc_vi": "Lá cây dùng ánh sáng mặt trời để tạo năng lượng",
                "audio": "leaves. Plural of leaf; use sunlight to make food.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🍃"
        },
        {
                "word": "flower",
                "meaning": "the colorful plant part that creates seeds for reproduction",
                "vietnamese": "Hoa: bộ phận rực rỡ sắc màu tạo hạt giống để sinh sản cây mới",
                "mnemonic": "Bông hoa xinh đẹp 🌸 thu hút ong bướm và tạo hạt giống duy trì nòi giống.",
                "colloc": "The flower creates seeds for new plants",
                "colloc_vi": "Hoa tạo ra các hạt giống để mọc cây mới",
                "audio": "flower. Creates seeds for reproduction.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🌸"
        },
        {
                "word": "absorb",
                "meaning": "to soak up or take in water from the surrounding soil",
                "vietnamese": "Hút / Hấp thụ: hút nước và dưỡng chất từ đất",
                "mnemonic": "Rễ cây ngấm và hút nước 🧽 như miếng bọt biển hút nước.",
                "colloc": "Roots absorb water and nutrients",
                "colloc_vi": "Rễ cây hút nước và các chất dinh dưỡng",
                "audio": "absorb. To soak up or take in water.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🧽"
        },
        {
                "word": "transport",
                "meaning": "to carry or move something from one place to another",
                "vietnamese": "Vận chuyển: dẫn truyền nước và chất dinh dưỡng đi khắp cây",
                "mnemonic": "Các ống dẫn vận chuyển dòng nước 🚚 từ dưới gốc lên đến ngọn.",
                "colloc": "The stem transports water to the leaves",
                "colloc_vi": "Thân cây vận chuyển nước lên các lá cây",
                "audio": "transport. To carry or move from one place to another.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🚚"
        },
        {
                "word": "aim",
                "meaning": "a sentence about what we want to find out in an experiment",
                "vietnamese": "Mục tiêu thí nghiệm: câu văn nêu rõ ta muốn tìm hiểu điều gì",
                "mnemonic": "Bước đầu tiên trong khoa học: Xác định mục tiêu muốn khám phá 🎯.",
                "colloc": "The aim tells what we want to find out",
                "colloc_vi": "Mục tiêu nêu rõ điều chúng ta muốn tìm hiểu",
                "audio": "aim. What we want to find out in an experiment.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🎯"
        },
        {
                "word": "materials",
                "meaning": "the equipment and things we use to do an experiment",
                "vietnamese": "Dụng cụ & vật liệu: những đồ vật dùng để làm thí nghiệm",
                "mnemonic": "Cốc thủy tinh, nước màu, cọng cần tây 🧪 là các materials.",
                "colloc": "List down the materials for the experiment",
                "colloc_vi": "Liệt kê các dụng cụ và vật liệu cho thí nghiệm",
                "audio": "materials. The things we use to do an experiment.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🧪"
        },
        {
                "word": "method",
                "meaning": "a list of instructions that tells us what to do step by step",
                "vietnamese": "Phương pháp / Các bước tiến hành: hướng dẫn từng bước cần làm",
                "mnemonic": "Bản hướng dẫn chi tiết từng bước 📋 để thực hiện thí nghiệm chính xác.",
                "colloc": "Follow the method step by step",
                "colloc_vi": "Làm theo các bước tiến hành từng bước một",
                "audio": "method. Instructions that tell us what to do.",
                "type": "science",
                "svg_type": "default",
                "emoji": "📋"
        },
        {
                "word": "prediction",
                "meaning": "what you think will happen in the experiment before doing it",
                "vietnamese": "Dự đoán: suy nghĩ của con về kết quả trước khi bắt tay vào làm",
                "mnemonic": "Đoán trước điều gì sẽ xảy ra 🔮 (không có đúng hay sai khi dự đoán).",
                "colloc": "Make a prediction before testing",
                "colloc_vi": "Đưa ra dự đoán trước khi tiến hành thử nghiệm",
                "audio": "prediction. What you think will happen.",
                "type": "science",
                "svg_type": "default",
                "emoji": "🔮"
        },
        {
                "word": "fair test",
                "meaning": "an experiment where we change ONLY ONE thing",
                "vietnamese": "Thí nghiệm công bằng: thí nghiệm mà ta chỉ thay đổi duy nhất 1 yếu tố",
                "mnemonic": "Chỉ thay đổi 1 thứ duy nhất ⚖️, giữ nguyên tất cả những yếu tố còn lại.",
                "colloc": "Change only one thing to make it a fair test",
                "colloc_vi": "Chỉ thay đổi một yếu tố để thí nghiệm được công bằng",
                "audio": "fair test. Change only one thing in an experiment.",
                "type": "science",
                "svg_type": "default",
                "emoji": "⚖️"
        },
        {
                "word": "conclusion",
                "meaning": "what we learned at the end of the experiment",
                "vietnamese": "Kết luận: bài học khoa học rút ra ở cuối thí nghiệm",
                "mnemonic": "Viết lại điều em học được 📜 sau khi quan sát kết quả thí nghiệm.",
                "colloc": "Write a conclusion about water transport",
                "colloc_vi": "Viết kết luận về sự vận chuyển nước của cây",
                "audio": "conclusion. What we learned at the end.",
                "type": "science",
                "svg_type": "default",
                "emoji": "📜"
        }
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
            "options": [
                "hand",
                "book",
                "foot",
                "desk"
            ],
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
                "An action word of what people do",
                "A word that describes noun color",
                "A mark put at end of a sentence"
            ],
            "answer": "A person, place, animal, or thing",
            "explanation": "Định nghĩa chuẩn W1E1: Danh từ (Noun) là từ chỉ Người (doctor), Nơi chốn (school), Con vật (cat), hoặc Đồ vật (banana)."
        },
        {
            "id": 3,
            "subject": "English",
            "question": "Which word in the following list is a VERB (an action word)?",
            "audio": "Which word in the following list is a verb?",
            "options": [
                "jump",
                "desk",
                "tree",
                "lion"
            ],
            "answer": "jump",
            "explanation": "Động từ (Verb) chỉ hành động chúng ta làm: \"jump\" (nhảy) là động từ, còn desk, tree, lion là danh từ."
        },
        {
            "id": 4,
            "subject": "English",
            "question": "An ADJECTIVE is a word that _______ a noun.",
            "audio": "An adjective is a word that describes a noun.",
            "options": [
                "describes",
                "multiplies",
                "celebrates",
                "identifies"
            ],
            "answer": "describes",
            "explanation": "Quy tắc ngữ pháp W1E2: \"An adjective is a word that describes a noun\" (Tính từ dùng để miêu tả đặc điểm danh từ)."
        },
        {
            "id": 5,
            "subject": "English",
            "question": "In the sentence: \"A cat jumps over the house\", which word is the VERB?",
            "audio": "In the sentence: A cat jumps over the house, which word is the verb?",
            "options": [
                "jumps",
                "house",
                "cat",
                "over"
            ],
            "answer": "jumps",
            "explanation": "Trong bài tập Thám tử ngữ pháp W1E2: \"cat\" và \"house\" là Danh từ (Nouns), \"jumps\" (nhảy) là Động từ (Verb)."
        },
        {
            "id": 6,
            "subject": "Mathematics",
            "question": "In the Summer Vacation tally chart: Đà Lạt has 5 tallies (|||| crossed) and Hà Nội has 4 tallies (||||). Which statement is correct?",
            "audio": "Which statement is correct about Da Lat and Ha Noi?",
            "options": [
                "Đà Lạt has more votes (5 > 4)",
                "Hà Nội has more votes (4 > 5)",
                "Both have equal votes (5 = 5)",
                "Đà Lạt has zero votes (5 = 0)"
            ],
            "answer": "Đà Lạt has more votes (5 > 4)",
            "explanation": "Bảng số liệu W1M: Đà Lạt có 5 gạch kiểm đếm, Hà Nội có 4 gạch. Vì 5 > 4 nên Đà Lạt là điểm đến phổ biến hơn (Most popular)."
        },
        {
            "id": 7,
            "subject": "Mathematics",
            "question": "In a pictogram, the key says: 1 🙂 = 2 students. How many students do 3 smileys (🙂 🙂 🙂) represent?",
            "audio": "If one smiley equals two students, how many students do three smileys represent?",
            "options": [
                "6 students",
                "3 students",
                "5 students",
                "8 students"
            ],
            "answer": "6 students",
            "explanation": "Toán biểu đồ tranh W1M: 3 biểu tượng 🙂 x 2 học sinh = 6 học sinh (3 x 2 = 6)."
        },
        {
            "id": 8,
            "subject": "Science",
            "question": "What is LIGHT in Grade 3 Science?",
            "audio": "What is light in Grade 3 Science?",
            "options": [
                "An energy we use to see the world around us",
                "A solid barrier that stops rays of the sun",
                "A buzzing sound made by rapid machine fans",
                "A shadow produced when opaque items block"
            ],
            "answer": "An energy we use to see the world around us",
            "explanation": "Khái niệm cốt lõi W1S: \"Light is an energy we use to see the world around us. We need light to see\" (Ánh sáng là dạng năng lượng giúp ta nhìn thấy thế giới xung quanh)."
        },
        {
            "id": 9,
            "subject": "Science",
            "question": "Which of the following is a REFLECTOR (does NOT make its own light, only bounces light)?",
            "audio": "Which of the following is a reflector?",
            "options": [
                "A glass mirror",
                "The bright Sun",
                "A battery torch",
                "A lit wax candle"
            ],
            "answer": "A glass mirror",
            "explanation": "Phân loại W1S: Mặt Trời, đèn pin và nến là nguồn sáng (Light sources). Chiếc gương (A mirror) chỉ phản xạ lại ánh sáng (Reflector)."
        },
        {
            "id": 10,
            "subject": "Science",
            "question": "The Sun, stars, and fire are all examples of:",
            "audio": "The Sun, stars, and fire are examples of what light?",
            "options": [
                "Natural light",
                "Man-made light",
                "Reflected light",
                "Artificial light"
            ],
            "answer": "Natural light",
            "explanation": "Phân loại W1S: Mặt Trời, ngôi sao và lửa là nguồn sáng tự nhiên (Natural light). Đèn pin, bóng đèn là nhân tạo (Man-made light)."
        }
    ],
    "week2": [
        {
            "id": 1,
            "subject": "English",
            "question": "A STATEMENT tells something. It begins with a capital letter and ends with a _______.",
            "audio": "A statement tells something and ends with a what?",
            "options": [
                "full stop (.)",
                "question mark (?)",
                "exclamation mark (!)",
                "quotation marks (\")"
            ],
            "answer": "full stop (.)",
            "explanation": "Quy tắc câu trần thuật W2E1: Câu kể (Statement) kể lại một việc và kết thúc bằng dấu chấm (full stop .)."
        },
        {
            "id": 2,
            "subject": "English",
            "question": "A QUESTION asks something. It begins with a capital letter and ends with a _______.",
            "audio": "A question asks something and ends with a what?",
            "options": [
                "question mark (?)",
                "full stop mark (.)",
                "exclamation mark (!)",
                "quotation marks (\")"
            ],
            "answer": "question mark (?)",
            "explanation": "Quy tắc câu hỏi W2E1: Câu hỏi (Question) bắt đầu bằng động từ/từ để hỏi và kết thúc bằng dấu hỏi (question mark ?)."
        },
        {
            "id": 3,
            "subject": "English",
            "question": "Complete the question for ONE singular object: \"_______ a melon on the plate?\"",
            "audio": "Complete the question: blank a melon on the plate?",
            "options": [
                "Was there",
                "Were there",
                "Did there",
                "Are there"
            ],
            "answer": "Was there",
            "explanation": "Quy tắc ngữ pháp W2E1: Dùng \"Was there a / an...\" cho 1 đồ vật số ít (a melon: singular)."
        },
        {
            "id": 4,
            "subject": "English",
            "question": "Complete the question for PLURAL objects: \"_______ chocolates in the box?\"",
            "audio": "Complete the question: blank chocolates in the box?",
            "options": [
                "Were there some",
                "Was there a one",
                "Did there exist",
                "Are there a lot"
            ],
            "answer": "Were there some",
            "explanation": "Quy tắc ngữ pháp W2E1: Dùng \"Were there some...\" cho danh từ số nhiều (chocolates: plural)."
        },
        {
            "id": 5,
            "subject": "English",
            "question": "What is the past simple form of the irregular verb \"eat\"?",
            "audio": "What is the past simple form of the irregular verb eat?",
            "options": [
                "ate",
                "eated",
                "eating",
                "eaten"
            ],
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
                "Was she walk to school?",
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
                "< (less than)",
                "> (greater than)",
                "= (equal to)",
                "+ (plus sum)"
            ],
            "answer": "< (less than)",
            "explanation": "Quy tắc cá sấu W2M: Miệng cá sấu luôn há to về phía số lớn hơn (540 > 450, tức 450 < 540)."
        },
        {
            "id": 8,
            "subject": "Mathematics",
            "question": "In the recycling project: Class 3A collected 350 bottles. Class 3B collected 420 bottles. Which statement is TRUE?",
            "audio": "Which statement is true about the collected bottles?",
            "options": [
                "Class 3B collected more (420 > 350)",
                "Class 3A collected more (350 > 420)",
                "Both collected equal (420 = 350)",
                "Class 3B collected fewer (420 < 350)"
            ],
            "answer": "Class 3B collected more (420 > 350)",
            "explanation": "Bài toán thực tế tái chế rác W2M: 420 > 350, do đó lớp 3B thu gom được nhiều hơn lớp 3A."
        },
        {
            "id": 9,
            "subject": "Science",
            "question": "Light always travels in a _______ and cannot bend around corners.",
            "audio": "Light always travels in a what line?",
            "options": [
                "straight line",
                "curved stream",
                "circular path",
                "zigzag course"
            ],
            "answer": "straight line",
            "explanation": "Định luật truyền sáng W2S: Ánh sáng luôn truyền theo đường thẳng (straight line) và không thể tự bẻ cong qua vật cản."
        },
        {
            "id": 10,
            "subject": "Science",
            "question": "An object is _______ when it BLOCKS light completely and casts a dark shadow (like a wooden door or textbook).",
            "audio": "An object is what when it blocks light completely?",
            "options": [
                "opaque",
                "transparent",
                "translucent",
                "reflective"
            ],
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
                "A bright burst of orange fire",
                "A golden shower of spark light",
                "A heavy stream of white water"
            ],
            "answer": "A small cloud of blue smoke",
            "explanation": "Chi tiết câu chuyện slide W3E1: Billy nhìn ra ngoài và thấy \"a small cloud of blue smoke\" (làn khói nhỏ màu xanh lam) bốc lên từ gian nhà kho."
        },
        {
            "id": 3,
            "subject": "English",
            "question": "What action verb do we use with a DIAL on the machine?",
            "audio": "What action verb do we use with a dial on the machine?",
            "options": [
                "turn a dial",
                "push a dial",
                "pull a dial",
                "type a dial"
            ],
            "answer": "turn a dial",
            "explanation": "Cụm từ máy móc slide W3E1: \"turn a dial\" (xoay núm vặn tròn chia vạch)."
        },
        {
            "id": 4,
            "subject": "English",
            "question": "What action verb do we use with a HANDLE beside the square screen?",
            "audio": "What action verb do we use with a handle beside the screen?",
            "options": [
                "pull a handle",
                "push a handle",
                "turn a handle",
                "type a handle"
            ],
            "answer": "pull a handle",
            "explanation": "Cụm từ máy móc slide W3E1: \"pull a handle\" (kéo chiếc cần gạt xuống)."
        },
        {
            "id": 5,
            "subject": "English",
            "question": "\"_______ did you eat the teacher's bánh mì?\" — \"Because I was hungry!\"",
            "audio": "Blank did you eat the teacher's bánh mì? Because I was hungry.",
            "options": [
                "Why",
                "Who",
                "When",
                "What"
            ],
            "answer": "Why",
            "explanation": "Quy tắc từ để hỏi W3E2: \"Why\" hỏi về lý do/nguyên nhân, câu trả lời bắt đầu bằng \"Because\" (Bởi vì...)."
        },
        {
            "id": 6,
            "subject": "Mathematics",
            "question": "What number is represented by: 5 Hundreds + 6 Tens + 9 Ones?",
            "audio": "What number is represented by 5 Hundreds, 6 Tens, and 9 Ones?",
            "options": [
                "569",
                "659",
                "596",
                "965"
            ],
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
            "explanation": "Dạng khai triển số W3M: 835 = 800 + 30 + 5 (tách rõ giá trị từng hàng: 8 Trăm, 3 Chục, 5 Đơn vị)."
        },
        {
            "id": 8,
            "subject": "Science",
            "question": "How many MILK TEETH (baby teeth) do young children under six years old have?",
            "audio": "How many milk teeth do young children have?",
            "options": [
                "20 teeth",
                "32 teeth",
                "28 teeth",
                "16 teeth"
            ],
            "answer": "20 teeth",
            "explanation": "Kiến thức nha khoa slide W3S: Trẻ em dưới sáu tuổi có đúng 20 chiếc răng sữa (milk teeth). Người lớn có 32 răng vĩnh viễn (permanent teeth)."
        },
        {
            "id": 9,
            "subject": "Science",
            "question": "Which type of teeth are flat and sharp like a CHISEL, used for SLICING and CUTTING food?",
            "audio": "Which teeth are shaped like a chisel and used for slicing?",
            "options": [
                "Incisors",
                "Canines",
                "Premolars",
                "Molars"
            ],
            "answer": "Incisors",
            "explanation": "Chức năng răng slide W3S: Răng cửa (Incisors - 8 chiếc) có rìa phẳng sắc như lưỡi đục, chuyên dùng để cắn và cắt lát thức ăn (slice and cut)."
        },
        {
            "id": 10,
            "subject": "Science",
            "question": "Which teeth are the LARGEST teeth at the back with a flat surface, used for GRINDING food finely?",
            "audio": "Which teeth are the largest teeth used for grinding food?",
            "options": [
                "Molars",
                "Incisors",
                "Canines",
                "Premolars"
            ],
            "answer": "Molars",
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
            "explanation": "Chi tiết cốt truyện trong Language Book p. 14: \"Bang! Billy woke up with a start at half past six in the morning.\""
        },
        {
            "id": 2,
            "subject": "English",
            "question": "Which phrase correctly completes: \"We _______ to turn on the machine's electrical power\"?",
            "audio": "Which phrase correctly completes: We blank to turn on the machine's power?",
            "options": [
                "press a switch",
                "turn a switch",
                "pull a switch",
                "push a switch"
            ],
            "answer": "press a switch",
            "explanation": "Cụm động từ máy móc chuẩn slide: \"press a switch\" (bật/gạt công tắc điện), \"turn a dial\" (xoay núm vặn), \"pull a handle\" (kéo cần gạt), \"push a button\" (bấm nút tròn)."
        },
        {
            "id": 3,
            "subject": "English",
            "question": "What does the word TRUE mean in Grade 3 English?",
            "audio": "What does the word true mean in English?",
            "options": [
                "Something that is completely correct or real (a fact)",
                "Something that is completely incorrect or untrue (a lie)",
                "Something that is an invented story or myth (fiction)",
                "Something that is a confusing riddle without an answer"
            ],
            "answer": "Something that is completely correct or real (a fact)",
            "explanation": "Định nghĩa chuẩn trong slide: \"True means something that is correct or real. It is a fact.\" (True nghĩa là điều gì đó chính xác hoặc có thật - là một sự thật)."
        },
        {
            "id": 4,
            "subject": "English",
            "question": "What is the past simple tense of the regular verb \"look\"?",
            "audio": "What is the past simple tense of the regular verb look?",
            "options": [
                "looked",
                "looking",
                "looks",
                "lookt"
            ],
            "answer": "looked",
            "explanation": "Quy tắc quá khứ đơn có quy tắc: Động từ regular thêm đuôi -ed: look &rarr; looked (Billy looked inside the shed)."
        },
        {
            "id": 5,
            "subject": "English",
            "question": "According to Cambridge rules (Practice Book p. 5), where must the comma (,) go in direct speech?",
            "audio": "According to Cambridge rules, where must the comma go in direct speech?",
            "options": [
                "INSIDE speech marks: “I like reading,” Emma said.",
                "OUTSIDE speech marks: “I like reading”, Emma said.",
                "AT START of sentence: ,“I like reading” Emma said.",
                "AFTER reporting verb: “I like reading” Emma, said."
            ],
            "answer": "INSIDE speech marks: “I like reading,” Emma said.",
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
                "470 (47 tens)"
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
                "500 + 60 + 90"
            ],
            "answer": "500 + 60 + 9",
            "explanation": "Dạng khai triển số: 569 gồm 5 Hàng Trăm (500), 6 Hàng Chục (60) và 9 Hàng Đơn vị (9) &rarr; 569 = 500 + 60 + 9."
        },
        {
            "id": 8,
            "subject": "Mathematics",
            "question": "On a number line, what is the exact HALFWAY POINT (midpoint) between 20 and 30?",
            "audio": "On a number line, what is the exact halfway point between 20 and 30?",
            "options": [
                "25",
                "22",
                "28",
                "20"
            ],
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
                "Light always curves around sharp corners and obstacles",
                "Light only travels in circular ripples across the floor",
                "Light stops completely when passing through clear glass"
            ],
            "answer": "Light always travels in a straight line and cannot bend",
            "explanation": "Đặc tính truyền sáng slide W4S: \"Light travels in straight lines; cannot bend or move around corners.\""
        },
        {
            "id": 10,
            "subject": "Science",
            "question": "At 12 p.m. (midday) when the Sun is directly overhead, what happens to tree shadows?",
            "audio": "At 12 p.m. midday when the Sun is directly overhead, what happens to tree shadows?",
            "options": [
                "Shadows are shortest, gathered right under base",
                "Shadows are longest, stretching far out to west",
                "Shadows disappear into rainbow-colored lights",
                "Shadows are identical to early morning shadows"
            ],
            "answer": "Shadows are shortest, gathered right under base",
            "explanation": "Quy luật bóng Mặt Trời slide W4S: Lúc 12 giờ trưa (midday) khi Mặt Trời lên cao nhất trên đỉnh đầu, bóng cây ngắn nhất (shortest) thu tròn dưới gốc cây."
        }
    ],
    "week5": [
        {
            "id": 1,
            "subject": "English",
            "question": "Which part of a story introduces the CHARACTERS (Who) and the SETTING (Where and When)?",
            "audio": "Which part of a story introduces the characters and setting?",
            "options": [
                "Beginning",
                "Middle",
                "Ending",
                "Title"
            ],
            "answer": "Beginning",
            "explanation": "Quy tắc 3 phần của truyện (Slide W5E1): Phần Mở đầu (Beginning) luôn giới thiệu Nhân vật (Characters) và Bối cảnh (Setting: thời gian, địa điểm)."
        },
        {
            "id": 2,
            "subject": "English",
            "question": "What is the past simple form of the irregular verb \"wake up\" in: \"Billy _______ at half past six\"?",
            "audio": "What is the past simple form of the verb wake up?",
            "options": [
                "woke up",
                "waked up",
                "waking up",
                "wake up"
            ],
            "answer": "woke up",
            "explanation": "Động từ bất quy tắc W5E1: wake up chuyển sang quá khứ là \"woke up\"."
        },
        {
            "id": 3,
            "subject": "English",
            "question": "What is the past simple form of \"hear\" in: \"He _______ a loud BANG outside\"?",
            "audio": "What is the past simple form of hear?",
            "options": [
                "heard",
                "heared",
                "hearing",
                "hears"
            ],
            "answer": "heard",
            "explanation": "Động từ quá khứ W5E1: hear chỉ thêm 'd' thành \"heard\" (phát âm là /hɜːd/)."
        },
        {
            "id": 4,
            "subject": "English",
            "question": "Which of these time words is commonly used at the END of a story when a problem is solved?",
            "audio": "Which time word is used at the end of a story?",
            "options": [
                "Finally",
                "Suddenly",
                "One morning",
                "First of all"
            ],
            "answer": "Finally",
            "explanation": "Từ nối chỉ thời gian W5E2: \"Finally\" (Cuối cùng), \"In the end\" (Kết cục) dùng ở phần End. \"Once upon a time\" dùng ở Beginning."
        },
        {
            "id": 5,
            "subject": "Mathematics",
            "question": "Using the Partitioning method for 341 + 526, what is the sum of the HUNDREDS: (300 + 500)?",
            "audio": "What is three hundred plus five hundred in partitioning?",
            "options": [
                "800",
                "700",
                "900",
                "850"
            ],
            "answer": "800",
            "explanation": "Phương pháp tách số W5M: Hàng trăm là 300 + 500 = 800. Tổng kết quả: 800 + 60 + 7 = 867."
        },
        {
            "id": 6,
            "subject": "Mathematics",
            "question": "Calculate using column addition with regrouping: 652 + 172 = ?",
            "audio": "Calculate six hundred and fifty-two plus one hundred and seventy-two.",
            "options": [
                "824",
                "724",
                "814",
                "834"
            ],
            "answer": "824",
            "explanation": "Đặt tính cộng có nhớ W5M: Đơn vị 2+2=4; Chục: 5+7=12 (viết 2 nhớ 1); Trăm: 6+1+1=8 &rarr; Đáp án là 824."
        },
        {
            "id": 7,
            "subject": "Mathematics",
            "question": "The Rice Harvest Problem: Billy harvested 438 kg of rice in the morning and 245 kg in the afternoon. Total?",
            "audio": "How many kilograms of rice did Billy harvest in total?",
            "options": [
                "683 kg",
                "673 kg",
                "693 kg",
                "583 kg"
            ],
            "answer": "683 kg",
            "explanation": "Bài toán thực tế W5M: Phép tính 438 + 245 = 683 kg."
        },
        {
            "id": 8,
            "subject": "Science",
            "question": "Which liquid in the mouth softens food and starts breaking it down while teeth are chewing?",
            "audio": "Which liquid in the mouth softens food?",
            "options": [
                "Saliva",
                "Water",
                "Blood",
                "Mucus"
            ],
            "answer": "Saliva",
            "explanation": "Hệ tiêu hóa W5S: Nước bọt (Saliva) làm mềm và hỗ trợ tiêu hóa thức ăn ngay tại khoang miệng."
        },
        {
            "id": 9,
            "subject": "Science",
            "question": "What is the function of the OESOPHAGUS (gullet) in the digestive system?",
            "audio": "What is the function of the oesophagus?",
            "options": [
                "It squeezes food down from mouth to stomach",
                "It absorbs essential nutrients into blood",
                "It grinds hard nuts into fine particles",
                "It produces strong acids to break down fat"
            ],
            "answer": "It squeezes food down from mouth to stomach",
            "explanation": "Chức năng thực quản W5S: Các cơ của thực quản (oesophagus) co bóp đẩy thức ăn trôi từ miệng xuống dạ dày."
        },
        {
            "id": 10,
            "subject": "Science",
            "question": "Which organ of the digestive system ABSORBS nutrients into the blood to give our body energy?",
            "audio": "Which organ absorbs nutrients into the blood?",
            "options": [
                "Small intestine",
                "Large intestine",
                "Muscular stomach",
                "Oesophagus tube"
            ],
            "answer": "Small intestine",
            "explanation": "Chức năng cơ quan W5S: Ruột non (Small intestine) hấp thụ các chất dinh dưỡng thiết yếu vào máu để nuôi cơ thể."
        }
    ],
    "week6": [
        {
            "id": 1,
            "subject": "English",
            "question": "In the story \"George's Marvellous Medicine\", what does the word MARVELLOUS mean?",
            "audio": "What does the word marvellous mean?",
            "options": [
                "Really really good and wonderful",
                "Extremely dangerous and scary",
                "Very grumpy and bad-tempered",
                "Completely boring and ordinary"
            ],
            "answer": "Really really good and wonderful",
            "explanation": "Từ vựng W6E1: \"marvellous\" đồng nghĩa với wonderful, fantastic, really really good (kỳ diệu, tuyệt vời)."
        },
        {
            "id": 2,
            "subject": "English",
            "question": "Choose the correct past continuous form for singular George: \"George _______ (mix) the medicine in a giant saucepan.\"",
            "audio": "Choose the correct past continuous form for George.",
            "options": [
                "was mixing",
                "were mixing",
                "is mixing",
                "are mixing"
            ],
            "answer": "was mixing",
            "explanation": "Quy tắc thì Quá khứ tiếp diễn W6E2: Chủ ngữ số ít (George = he) đi với \"was\" + V-ing &rarr; \"was mixing\"."
        },
        {
            "id": 3,
            "subject": "English",
            "question": "Choose the correct past continuous form for plural subjects: \"Grandma's legs _______ (grow) through the living room ceiling!\"",
            "audio": "Choose the correct past continuous form for Grandma's legs.",
            "options": [
                "were growing",
                "was growing",
                "is growing",
                "are growing"
            ],
            "answer": "were growing",
            "explanation": "Ngữ pháp W6E2: Chủ ngữ \"Grandma's legs\" là danh từ số nhiều (2 chân) &rarr; dùng \"were\" + V-ing &rarr; \"were growing\"."
        },
        {
            "id": 4,
            "subject": "English",
            "question": "Which word from Language Book p.16 has the short 'oo' sound: \"He put the pot on the stove to _______ the mixture\"?",
            "audio": "Which word has the short double-o sound?",
            "options": [
                "cook",
                "moon",
                "spoon",
                "boot"
            ],
            "answer": "cook",
            "explanation": "Ngữ âm 'oo' W6E2: \"cook\", \"book\", \"foot\", \"wood\" phát âm âm ngắn. \"moon\", \"spoon\" phát âm âm dài."
        },
        {
            "id": 5,
            "subject": "Mathematics",
            "question": "A 2D shape has only two dimensions. What are these two dimensions?",
            "audio": "What two dimensions do all 2D shapes have?",
            "options": [
                "Height and width",
                "Length and depth",
                "Depth and volume",
                "Weight and area"
            ],
            "answer": "Height and width",
            "explanation": "Định nghĩa hình 2D trong slide W6M: Hình 2 chiều chỉ có chiều cao (height) và chiều rộng (width)."
        },
        {
            "id": 6,
            "subject": "Mathematics",
            "question": "How many straight sides and angles does a HEXAGON have?",
            "audio": "How many sides and angles does a hexagon have?",
            "options": [
                "6 sides and 6 angles",
                "5 sides and 5 angles",
                "8 sides and 8 angles",
                "4 sides and 4 angles"
            ],
            "answer": "6 sides and 6 angles",
            "explanation": "Thuộc tính hình W6M: Hexagon (lục giác) có đúng 6 cạnh và 6 góc. Pentagon có 5 cạnh, Octagon có 8 cạnh."
        },
        {
            "id": 7,
            "subject": "Mathematics",
            "question": "Is a CIRCLE a polygon? Why or why not?",
            "audio": "Is a circle a polygon?",
            "options": [
                "No, because a polygon must have 3 or more straight sides",
                "Yes, because a circle has four equal sides and right angles",
                "Yes, because any closed two-dimensional shape is a polygon",
                "No, because a polygon cannot have any vertices or corners"
            ],
            "answer": "No, because a polygon must have 3 or more straight sides",
            "explanation": "Khái niệm đa giác W6M: Đa giác (Polygon) bắt buộc phải tạo bởi từ 3 cạnh thẳng trở lên. Hình tròn là đường cong nên KHÔNG phải là polygon."
        },
        {
            "id": 8,
            "subject": "Science",
            "question": "A tiger eats ONLY meat and has 4 long pointed canine teeth. What diet classification is the tiger?",
            "audio": "What diet classification is the tiger?",
            "options": [
                "Carnivore",
                "Herbivore",
                "Omnivore",
                "Predator"
            ],
            "answer": "Carnivore",
            "explanation": "Phân loại chế độ ăn W6S: Động vật chỉ ăn thịt là Carnivore (hổ, sư tử, cá mập)."
        },
        {
            "id": 9,
            "subject": "Science",
            "question": "An animal skull has NO sharp canines, only broad FLAT MOLARS for chewing grass. What type of animal was it?",
            "audio": "What type of animal was it if the skull has only flat molars?",
            "options": [
                "Herbivore",
                "Carnivore",
                "Omnivore",
                "Predator"
            ],
            "answer": "Herbivore",
            "explanation": "Giải phẫu hộp sọ W6S: Hộp sọ chỉ có răng hàm phẳng (flat molars) dùng để nhai và nghiền nát cỏ &rarr; là Herbivore (bò, hươu, cừu)."
        },
        {
            "id": 10,
            "subject": "Science",
            "question": "Humans and Bears eat BOTH meat and plant foods. What are they called?",
            "audio": "What are animals called that eat both meat and plants?",
            "options": [
                "Omnivores",
                "Carnivores",
                "Herbivores",
                "Predators"
            ],
            "answer": "Omnivores",
            "explanation": "Chế độ ăn W6S: Loài ăn cả thịt và thực vật được gọi là Omnivores (con người, gấu, cáo, chó)."
        }
    ],
    "week7": [
        {
            "id": 1,
            "subject": "Mathematics",
            "question": "When we see a PLUS (+) symbol, what calculation do we need to do?",
            "audio": "When we see a plus symbol, what calculation do we need to do?",
            "options": [
                "Add",
                "Subtract",
                "Multiply",
                "Divide"
            ],
            "answer": "Add",
            "explanation": "Quy tắc cơ bản W7M: Dấu + (plus) yêu cầu ta thực hiện phép tính cộng (add). Dấu - (minus) yêu cầu ta thực hiện phép tính trừ (subtract)."
        },
        {
            "id": 2,
            "subject": "Mathematics",
            "question": "Pattern in Addition: When we add 2 to any number ending in 2 (2+2, 12+2, 42+2, 62+2), what digit is ALWAYS in the ones place?",
            "audio": "What digit is always in the ones place when we add two to a number ending in two?",
            "options": [
                "4",
                "2",
                "6",
                "8"
            ],
            "answer": "4",
            "explanation": "Quy luật số W7M (Slide p.6-7): Khi cộng 2 vào số có tận cùng là 2, hàng đơn vị luôn là 4 (2+2=4, 12+2=14, 42+2=44, 62+2=64)."
        },
        {
            "id": 3,
            "subject": "Mathematics",
            "question": "Pattern in Addition: When we add 3 to any number ending in 3 (3+3, 13+3, 23+3, 73+3), what digit is ALWAYS in the ones place?",
            "audio": "What digit is always in the ones place when we add three to a number ending in three?",
            "options": [
                "6",
                "3",
                "9",
                "5"
            ],
            "answer": "6",
            "explanation": "Quy luật số W7M (Slide p.8-9): Khi cộng 3 vào số có đuôi 3, chữ số hàng đơn vị luôn luôn là 6 (3+3=6, 13+3=16, 73+3=76)."
        },
        {
            "id": 4,
            "subject": "Mathematics",
            "question": "Pattern in Subtraction: When we subtract 5 from any number ending in 2 (12-5, 22-5, 32-5, 82-5), what digit is ALWAYS in the ones place?",
            "audio": "What digit is always in the ones place when we subtract five from a number ending in two?",
            "options": [
                "7",
                "5",
                "3",
                "2"
            ],
            "answer": "7",
            "explanation": "Quy luật số W7M (Slide p.12-13): Khi trừ 5 từ số có tận cùng là 2, hàng đơn vị luôn luôn là 7 (12-5=7, 22-5=17, 32-5=27, 82-5=77)."
        },
        {
            "id": 5,
            "subject": "Mathematics",
            "question": "The Celery Seed Problem: Lily had 73 seeds. Her teacher gave her 3 more seeds (+3). Then a bird ate 2 seeds (-2). How many seeds are left?",
            "audio": "How many seeds does Lily have left?",
            "options": [
                "74 seeds",
                "76 seeds",
                "72 seeds",
                "78 seeds"
            ],
            "answer": "74 seeds",
            "explanation": "Toán thực tế W7M: Sau khi nhận thêm 3 hạt: 73 + 3 = 76 (đuôi 3+3=6). Sau khi chim ăn 2 hạt: 76 - 2 = 74 hạt (đuôi 6-2=4)."
        },
        {
            "id": 6,
            "subject": "Science",
            "question": "Which plant part ABSORBS water and nutrients from the soil and anchors the plant firmly?",
            "audio": "Which plant part absorbs water from the soil?",
            "options": [
                "Roots",
                "Stem",
                "Leaves",
                "Flower"
            ],
            "answer": "Roots",
            "explanation": "Chức năng bộ phận cây W7S (Slide p.21): Rễ cây (Roots) hút nước và khoáng chất từ đất, đồng thời giữ chặt cây không bị ngã đổ."
        },
        {
            "id": 7,
            "subject": "Science",
            "question": "Which plant part SUPPORTS the plant upright and TRANSPORTS (moves) water up to the leaves and flowers?",
            "audio": "Which plant part supports the plant and transports water?",
            "options": [
                "Stem",
                "Roots",
                "Leaves",
                "Flower"
            ],
            "answer": "Stem",
            "explanation": "Chức năng thân cây W7S (Slide p.18): Thân cây (Stem) nâng đỡ cây và vận chuyển nước từ rễ lên các tán lá."
        },
        {
            "id": 8,
            "subject": "Science",
            "question": "What is the primary scientific function of the LEAVES on a plant?",
            "audio": "What is the function of the leaves?",
            "options": [
                "They use sunlight to make food and energy",
                "They absorb water and minerals from soil",
                "They produce colorful seeds for flowers",
                "They anchor the plant firmly in ground"
            ],
            "answer": "They use sunlight to make food and energy",
            "explanation": "Chức năng của lá W7S (Slide p.15): Lá cây dùng ánh sáng mặt trời để tạo năng lượng / thức ăn nuôi sống cây."
        },
        {
            "id": 9,
            "subject": "Science",
            "question": "What is the definition of a FAIR TEST in scientific experiments?",
            "audio": "What is a fair test in scientific experiments?",
            "options": [
                "An experiment where we change only one single thing",
                "An experiment where we change all variables at once",
                "An experiment where no equipment or tools are used",
                "An experiment where everyone makes the same guesses"
            ],
            "answer": "An experiment where we change only one single thing",
            "explanation": "Quy tắc thí nghiệm công bằng W7S (Slide p.30): \"A fair test means we change only ONE thing in the experiment\"."
        },
        {
            "id": 10,
            "subject": "Science",
            "question": "In the Virtual Celery Experiment, why did the celery leaves turn red when placed in red water?",
            "audio": "Why did the celery leaves turn red in the experiment?",
            "options": [
                "Because tubes in the stem carried red water up to the leaves",
                "Because the leaves produced red pigment when in bright sunlight",
                "Because red food dye soaked directly through leaf skin outside",
                "Because the roots converted water into red chemicals inside"
            ],
            "answer": "Because tubes in the stem carried red water up to the leaves",
            "explanation": "Thí nghiệm cọng cần tây W7S: Nước màu đỏ được các ống dẫn trong thân cây cần tây hút và vận chuyển thẳng lên các tán lá khiến lá đổi màu."
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
