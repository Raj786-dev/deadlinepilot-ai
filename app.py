import streamlit as st, sqlite3, json, datetime as dt
from google import genai

client = genai.Client(api_key=open("key.txt").read().strip())
db = sqlite3.connect("pilot.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS deadlines(id INTEGER PRIMARY KEY, title TEXT, due_at TEXT, est_hours REAL)")
db.execute("CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, deadline_id INT, title TEXT, hours REAL, day TEXT, done INT DEFAULT 0)")

import time

def ask(system, text):
    for attempt in range(4):
        try:
            r = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=system + "\n\nUser input: " + text)
            break
        except Exception as e:
            msg = str(e)
            if ("429" in msg or "503" in msg) and attempt < 3:
                time.sleep(20)
            else:
                raise
    raw = r.text.strip().replace("```json", "").replace("```", "")
    return json.loads(raw)
def add_deadline(text):
    today = dt.date.today().isoformat()
    d = ask(f"Today is {today}, timezone Asia/Kolkata. Return ONLY JSON: "
            "{\"title\":str,\"due_at\":\"YYYY-MM-DD\",\"est_hours\":number}", text)
    tasks = ask(f"Break this deadline into 3-6 subtasks totalling about {d['est_hours']} hours. "
                "Return ONLY a JSON list: [{\"title\":str,\"hours\":number}]", d["title"])
    cur = db.execute("INSERT INTO deadlines(title,due_at,est_hours) VALUES(?,?,?)",
                     (d["title"], d["due_at"], d["est_hours"]))
    due = dt.date.fromisoformat(d["due_at"])
    days = max((due - dt.date.today()).days, 1)
    for i, t in enumerate(tasks):
        day = dt.date.today() + dt.timedelta(days=int(i * days / len(tasks)))
        db.execute("INSERT INTO tasks(deadline_id,title,hours,day) VALUES(?,?,?,?)",
                   (cur.lastrowid, t["title"], t["hours"], day.isoformat()))
    db.commit()

def toggle(task_id):
    db.execute("UPDATE tasks SET done = 1 - done WHERE id=?", (task_id,))
    db.commit()

st.title("🧭 DeadlinePilot AI")
text = st.text_input("Deadline likho", placeholder="OS assignment submit karna hai Friday 5pm tak")
if st.button("Add") and text:
    try:
        add_deadline(text)
        st.success("Add ho gaya!")
    except Exception as e:
        st.error(f"Error aaya, dobara try karo: {e}")

HOURS_PER_DAY = 3
for did, title, due, est in db.execute("SELECT * FROM deadlines ORDER BY due_at").fetchall():
    tasks = db.execute("SELECT id,title,hours,day,done FROM tasks WHERE deadline_id=? ORDER BY day", (did,)).fetchall()
    left = sum(t[2] for t in tasks if not t[4])
    days_left = (dt.date.fromisoformat(due) - dt.date.today()).days
    risky = left > max(days_left, 0) * HOURS_PER_DAY
    st.subheader(("🔴 " if risky else "🟢 ") + title)
    st.caption(f"Due: {due} | Bacha hua kaam: {left}h | Din bache: {days_left}")
    if risky:
        st.warning("At risk! Bacha hua kaam available time se zyada hai.")
    done_n = sum(t[4] for t in tasks)
    st.progress(done_n / len(tasks) if tasks else 0)
    for tid, ttitle, hrs, day, done in tasks:
        st.checkbox(f"{ttitle} ({hrs}h) – {day}", value=bool(done), key=f"t{tid}",
                    on_change=toggle, args=(tid,))