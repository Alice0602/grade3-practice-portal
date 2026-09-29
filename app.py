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

        # Maths: Tally
        {"word": "tally chart", "meaning": "marks used to count data in groups of 5", "vietnamese": "Bảng gạch đếm dữ liệu theo từng nhóm 5 gạch", "mnemonic": "Cứ 4 gạch đứng và 1 gạch chéo ngang |||| tạo thành 1 bó 5 gạch giúp đếm cực nhanh.", "colloc": "Count tallies in groups of five", "colloc_vi": "Đếm các dấu gạch theo từng nhóm 5", "audio": "tally chart. Marks used to count in groups of five.", "type": "maths", "svg_type": "tally", "emoji": "📊"},
        {"word": "data", "meaning": "information collected by counting or measuring", "vietnamese": "Dữ liệu / Số liệu thu thập được", "mnemonic": "Các con số ghi chép lại sau khi điều tra sở thích của cả lớp 📈.", "colloc": "Collect data about favorite fruit", "colloc_vi": "Thu thập số liệu về loại trái cây yêu thích", "audio": "data. Information collected by counting.", "type": "maths", "svg_type": "data", "emoji": "📋"}
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
