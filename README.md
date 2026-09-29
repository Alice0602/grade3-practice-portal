# 🎓 Grade 3 Learning Mastery & Practice Portal

An integrated web platform designed for **Cambridge Primary Grade 3 (English, Mathematics, Science)** to solve the forgetting curve through **Leitner Spaced Repetition**, **Strict Lock Mode (Anti-Quit)**, and **Real-Time Teacher Database Tracking**.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Alice0602/grade3-practice-portal)

---

## 🌟 Key Features

1. **🧠 Vocabulary Mastery Arena (Leitner Spaced Repetition):**
   - Eliminates vocabulary forgetting by re-queuing any mistaken words until they are mastered 100%.
   - Native English pronunciation (Web Speech API) + Collocations + Visual Emojis.

2. **🔒 Strict Lock Mode (Anti-Quit):**
   - Automatically activates Fullscreen mode.
   - Prevents closing the tab or reloading (`beforeunload` lock).
   - Real-time tab switch violation detector & logger.
   - Students must complete 100% of the active queue to finish.

3. **📊 Teacher Analytics Dashboard (`/teacher`):**
   - **🚨 "Red Alert" Vocabulary Heatmap:** Automatically identifies the top words students struggle with or fail most often.
   - **Student Performance Leaderboard:** Real-time scores, accuracy %, and test counts.
   - **Violation & Duration Tracking:** Detailed log of student attempts and tab switches.
   - **📥 1-Click Export:** Download full reports to Excel / CSV.

---

## 🚀 1-Click Cloud Deployment

Click the button below to deploy this portal 24/7 online for free:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Alice0602/grade3-practice-portal)

---

## 💻 Local Running

```bash
pip install -r requirements.txt
python app.py
```
- Teacher Dashboard: `http://localhost:5000/teacher`
- Student Practice Portal: `http://localhost:5000/`
