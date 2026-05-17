import os
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from io import BytesIO
import re
from dotenv import load_dotenv
from streamlit_cookies_controller import CookieController


load_dotenv()

# CONFIG

BACKEND_URL = os.getenv("BACKEND_URL")

BASE_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

st.set_page_config(
    page_title="TutorRAG",
    page_icon="🎓",
    layout="wide",
)


# COOKIE CONTROLLER

cookies = CookieController()


# SESSION STATE INIT

def init_state():
    defaults = {
        "page": "landing",
        "authenticated": False,
        "username": "",
        "password": "",
        "role": "",
        "grade": 0,
        "chat_messages": [],
        "generated_quiz": None,
        "quiz_result": None,
        "quiz_history": None,
        "chat_history_data": None,
        "quiz_generating": False,
        "login_loading": False,
        "signup_loading": False,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

init_state()

# Restore session from cookies on refresh
if not st.session_state.authenticated:
    username = cookies.get("username")
    password = cookies.get("password")
    role     = cookies.get("role")
    grade    = cookies.get("grade")
    if username and password and role:
        st.session_state.update({
            "authenticated": True,
            "username": username,
            "password": password,
            "role": role,
            "grade": int(grade) if grade else 0,
            "page": "app",
        })


# HELPERS

def auth():
    return HTTPBasicAuth(
        st.session_state.username,
        st.session_state.password,
    )

def api(method, path, **kwargs):
    return requests.request(
        method,
        f"{BACKEND_URL}{path}",
        auth=auth(),
        timeout=60,
        **kwargs
    )

def logout():
    for key in ["username", "password", "role", "grade"]:
        cookies.remove(key)
    for k in list(st.session_state.keys()):
        del st.session_state[k]


# CONFIRMATION DIALOGS

@st.dialog("Confirm Delete")
def confirm_delete_dialog(message, on_confirm_key):
    st.warning(message)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Yes, delete", type="primary"):
            st.session_state[on_confirm_key] = True
            st.rerun()
    with c2:
        if st.button("Cancel"):
            st.session_state[on_confirm_key] = False
            st.rerun()


# LANDING PAGE

def landing_page():
    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.markdown("## 🎓 TutorRAG")
        st.markdown(
            """
            ### AI-Powered Learning From Your Own Documents

            - Upload textbooks & notes  
            - Ask questions using AI  
            - Generate quizzes automatically  
            - Track learning progress  

            **Built using RAG + LLMs**
            """
        )

        b1, b2 = st.columns(2)
        with b1:
            if st.button("🚀 Get Started", use_container_width=True):
                st.session_state.page = "signup"
        with b2:
            if st.button("🔐 Login", use_container_width=True):
                st.session_state.page = "login"

    with col2:
        img = os.path.join(ASSETS_DIR, "landing-page.jpg")

        if os.path.exists(img):
            st.image(img, width="stretch")


# LOGIN PAGE

def login_page():
    col1, col2 = st.columns([1, 1])

    with col1:
        img = os.path.join(ASSETS_DIR, "login.jpg")

        if os.path.exists(img):
            st.image(img, width="stretch")

    with col2:
        st.markdown("## 🔐 Login")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Login",
                disabled=st.session_state.get("login_loading", False)
            )

            if submitted:
                st.session_state["login_loading"] = True
                st.session_state["_login_username"] = username
                st.session_state["_login_password"] = password
                st.rerun()

        if st.session_state.get("login_loading"):
            with st.spinner("Logging in..."):
                r = requests.get(
                    f"{BACKEND_URL}/login",
                    auth=HTTPBasicAuth(
                        st.session_state["_login_username"],
                        st.session_state["_login_password"],
                    ),
                )
            st.session_state["login_loading"] = False
            if r.status_code == 200:
                data = r.json()
                st.session_state.update({
                    "authenticated": True,
                    "username": st.session_state["_login_username"],
                    "password": st.session_state["_login_password"],
                    "role": data["role"],
                    "grade": data.get("grade", 0),
                    "page": "app",
                })
                cookies.set("username", st.session_state["username"])
                cookies.set("password", st.session_state["password"])
                cookies.set("role", data["role"])
                cookies.set("grade", str(data.get("grade", 0)))
                st.rerun()
            else:
                st.error("Invalid credentials")

        if st.button("⬅ Back", key="login_back"):
            st.session_state.page = "landing"

        if st.button("Forgot password?"):
            st.session_state.page = "reset_password"

def signup_page():
    col1, col2 = st.columns([1, 1])

    with col1:
        img = os.path.join(ASSETS_DIR, "signup.png")

        if os.path.exists(img):
            st.image(img, width="stretch")

    with col2:
        st.markdown("## ✍️ Create Account")
        role = st.selectbox("I am a", ["Student", "Teacher"])

        with st.form("signup_form"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            school = st.text_input("School")

            if role == "Student":
                grade = st.number_input("Grade", 1, 12)

            submitted = st.form_submit_button(
                "Create Account",
                disabled=st.session_state.get("signup_loading", False)
            )

            if submitted:
                st.session_state["signup_loading"] = True
                st.session_state["_signup_payload"] = {
                    "fullname": full_name,
                    "email": email,
                    "username": username,
                    "password": password,
                    "school": school,
                }
                st.session_state["_signup_role"] = role
                if role == "Student":
                    st.session_state["_signup_payload"]["grade"] = grade
                st.rerun()

        if st.session_state.get("signup_loading"):
            with st.spinner("Creating account..."):
                _role = st.session_state["_signup_role"]
                endpoint = "/signup/student" if _role == "Student" else "/signup/teacher"
                r = requests.post(
                    f"{BACKEND_URL}{endpoint}",
                    json=st.session_state["_signup_payload"],
                )
            st.session_state["signup_loading"] = False
            if r.status_code == 200:
                st.success("Account created successfully")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(r.text)

        if st.button("⬅ Back"):
            st.session_state.page = "landing"


# RESET PASSWORD PAGE

def reset_password_page():
    col1, col2 = st.columns([1, 1])

    with col1:
        img = os.path.join(ASSETS_DIR, "login.jpg")
        if os.path.exists(img):
            st.image(img, width="stretch")

    with col2:
        st.markdown("## 🔑 Reset Password")

        with st.form("reset_form"):
            username     = st.text_input("Username")
            email        = st.text_input("Email")
            new_password = st.text_input("New Password", type="password")
            confirm      = st.text_input("Confirm New Password", type="password")
            submitted    = st.form_submit_button("Reset Password")

            if submitted:
                if new_password != confirm:
                    st.error("Passwords do not match")
                elif not username or not email or not new_password:
                    st.error("All fields are required")
                else:
                    r = requests.post(
                        f"{BACKEND_URL}/reset-password",
                        json={
                            "username": username,
                            "email": email,
                            "new_password": new_password,
                        },
                    )
                    if r.status_code == 200:
                        st.success("Password reset successfully")
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(r.json().get("detail", "Reset failed"))

        if st.button("⬅ Back to Login"):
            st.session_state.page = "login"


# TEACHER DASHBOARD

def teacher_dashboard():
    # img = os.path.join(ASSETS_DIR, "teacher.jpg")

    # if os.path.exists(img):
    #     st.image(img, width=220)
    st.markdown("## 📚 Upload Study Material")

    pdf = st.file_uploader("Upload PDF", type="pdf")
    grade = st.number_input("Grade", 1, 12)

    if st.button("Upload Document", disabled=not pdf):
        with st.spinner("Uploading and indexing..."):
            files = {
                "file": (
                    pdf.name,
                    BytesIO(pdf.getvalue()),
                    "application/pdf",
                )
            }
            data = {"grade": str(int(grade))}
            r = api("POST", "/upload_docs", files=files, data=data)

            if r.status_code == 200:
                st.success("Document uploaded successfully")
            else:
                st.error(r.text)


# STUDENT DASHBOARD

def student_dashboard():
    # img = os.path.join(ASSETS_DIR, "students.jpg")
    # if os.path.exists(img):
    #     st.image(img, width=220)

    chat_tab, quiz_tab, history_tab, chat_history_tab = st.tabs(
        ["💬 Ask Questions", "📝 Quiz Generator", "📜 Quiz History", "🕘 Chat History"]
    )

    # ---------------- CHAT ----------------
    with chat_tab:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask a question"):
            st.session_state.chat_messages.append(
                {"role": "user", "content": prompt}
            )

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    r = api("POST", "/chat", json={"query": prompt})
                    if r.status_code == 200:
                        data = r.json()
                        answer = data["answer"]
                        if data["sources"]:
                            answer += "\n\n**Sources:** " + ", ".join(data["sources"])
                        st.markdown(answer)
                        st.session_state.chat_messages.append(
                            {"role": "assistant", "content": answer}
                        )
                    else:
                        st.error(r.text)

    # ---------------- QUIZ ----------------
    with quiz_tab:
        if st.session_state.generated_quiz is None:
            topic = st.text_input("Quiz Topic")
            num_q = st.slider("Number of Questions", 1, 10, 3)

            generating = st.session_state.get("quiz_generating", False)

            if st.button("Generate Quiz", disabled=not topic or generating):
                st.session_state["quiz_generating"] = True
                st.rerun()

            if st.session_state.get("quiz_generating"):
                with st.spinner("Generating quiz, please wait..."):
                    r = api(
                        "POST",
                        "/quiz",
                        json={"topic": topic, "num_questions": num_q},
                    )
                st.session_state["quiz_generating"] = False
                if r.status_code == 200:
                    st.session_state.generated_quiz = r.json()
                    st.session_state.generated_quiz["topic"] = topic
                    st.session_state.quiz_result = None
                    st.rerun()
                else:
                    st.error(r.text)

        else:
            quiz = st.session_state.generated_quiz
            raw = quiz["quiz"]

            blocks = re.split(r"(Question \d+:)", raw)[1:]
            questions = []

            for i in range(0, len(blocks), 2):
                lines = blocks[i + 1].strip().split("\n")
                q_text = lines[0]
                options = [l for l in lines if re.match(r"[A-Z]\)", l)]
                questions.append({"q": q_text, "opts": options})

            with st.form("quiz_form"):
                answers = []

                for i, q in enumerate(questions):
                    st.markdown(f"**Q{i+1}. {q['q']}**")
                    choice = st.radio(
                        "Choose:",
                        [o[0] for o in q["opts"]],
                        format_func=lambda x: next(
                            o for o in q["opts"] if o.startswith(x)
                        ),
                        key=f"quiz_q{i}",
                    )
                    answers.append(choice)

                submitted = st.form_submit_button("Submit Quiz")

            if submitted:
                with st.spinner("Submitting quiz..."):
                    r = api(
                        "POST",
                        "/quiz/check",
                        json={
                            "quiz_id": quiz["quiz_id"],
                            "answers": answers,
                        },
                    )
                if r.status_code == 200:
                    st.session_state.quiz_result = r.json()
                    st.session_state.generated_quiz = None
                else:
                    st.error(r.text)

        if st.session_state.quiz_result:
            res = st.session_state.quiz_result
            st.success(res["message"])

            for r in res["results"]:
                status = "✅ Correct" if r["is_correct"] else "❌ Incorrect"
                st.markdown(
                    f"**Q{r['question_number']} — {status}**  \n"
                    f"Your Answer: **{r['user_answer']}**  \n"
                    f"Correct Answer: **{r['correct_answer']}**"
                )

            if st.button("Start New Quiz"):
                st.session_state.quiz_result = None

    # ---------------- HISTORY ----------------
    with history_tab:
        col_load, col_del = st.columns([1, 1])
        with col_load:
            if st.button("Load History"):
                with st.spinner("Loading quiz history..."):
                    r = api("GET", "/quiz/history")
                if r.status_code == 200:
                    st.session_state.quiz_history = r.json()["history"]
                else:
                    st.error(r.text)
        with col_del:
            if st.button("🗑 Delete All Quiz History", type="secondary"):
                confirm_delete_dialog(
                    "Delete all quiz history? This cannot be undone.",
                    "do_delete_all_quiz"
                )

        if st.session_state.get("do_delete_all_quiz"):
            st.session_state["do_delete_all_quiz"] = False
            with st.spinner("Deleting..."):
                r = api("DELETE", "/quiz/history")
            if r.status_code == 200:
                st.session_state.quiz_history = None
                st.success(r.json()["message"])
                st.rerun()
            else:
                st.error(r.text)

        history = st.session_state.quiz_history
        if history:
            for attempt in history:
                score = attempt["score"]
                total = attempt["total"]
                percent = int((score / total) * 100)

                with st.expander(f"{attempt['topic']} — {score}/{total} ({percent}%)"):
                    if st.button("🗑 Delete", key=f"del_quiz_{attempt['id']}"):
                        confirm_delete_dialog(
                            f"Delete quiz attempt for '{attempt['topic']}'?",
                            f"do_delete_quiz_{attempt['id']}"
                        )

                    if st.session_state.get(f"do_delete_quiz_{attempt['id']}"):
                        st.session_state.pop(f"do_delete_quiz_{attempt['id']}", None)
                        with st.spinner("Deleting..."):
                            r = api("DELETE", f"/quiz/history/{attempt['id']}")
                        if r.status_code == 200:
                            st.session_state.quiz_history = [
                                a for a in st.session_state.quiz_history
                                if a["id"] != attempt["id"]
                            ]
                            st.rerun()
                        else:
                            st.error(r.text)

                    raw_quiz = attempt["quiz_content"]
                    blocks = re.split(r"(Question \d+:)", raw_quiz)[1:]
                    parsed = []
                    for i in range(0, len(blocks), 2):
                        lines = blocks[i + 1].strip().split("\n")
                        parsed.append({
                            "question": lines[0],
                            "options": [l for l in lines if re.match(r"[A-Z]\)", l)],
                        })

                    for i, res in enumerate(attempt["results"]):
                        q = parsed[i]
                        st.markdown(f"### Q{i+1}: {q['question']}")
                        for opt in q["options"]:
                            letter = opt[0]
                            if letter == res["correct_answer"]:
                                st.markdown(f"✅ **{opt}** (Correct)")
                            elif letter == res["user_answer"]:
                                st.markdown(f"❌ **{opt}** (Your Answer)")
                            else:
                                st.markdown(opt)
                        st.divider()


    # ---------------- CHAT HISTORY ----------------
    with chat_history_tab:
        col_load, col_del = st.columns([1, 1])
        with col_load:
            if st.button("Load Chat History"):
                with st.spinner("Loading chat history..."):
                    r = api("GET", "/chat/history")
                if r.status_code == 200:
                    st.session_state["chat_history_data"] = r.json()["history"]
                else:
                    st.error(r.text)
        with col_del:
            if st.button("🗑 Delete All Chat History", type="secondary"):
                confirm_delete_dialog(
                    "Delete all chat history? This cannot be undone.",
                    "do_delete_all_chat"
                )

        if st.session_state.get("do_delete_all_chat"):
            st.session_state["do_delete_all_chat"] = False
            with st.spinner("Deleting..."):
                r = api("DELETE", "/chat/history")
            if r.status_code == 200:
                st.session_state["chat_history_data"] = None
                st.success(r.json()["message"])
                st.rerun()
            else:
                st.error(r.text)

        chat_hist = st.session_state.get("chat_history_data")
        if chat_hist:
            if len(chat_hist) == 0:
                st.info("No chat history yet.")
            for entry in chat_hist:
                with st.expander(f"🕘 {entry['timestamp']} — {entry['query'][:60]}"):
                    col_q, col_btn = st.columns([5, 1])
                    with col_q:
                        st.markdown(f"**Question:** {entry['query']}")
                        st.markdown(f"**Answer:** {entry['response']}")
                        if entry.get("sources"):
                            st.markdown(f"**Sources:** {', '.join(entry['sources'])}")
                    with col_btn:
                        if st.button("🗑", key=f"del_chat_{entry['id']}"):
                            confirm_delete_dialog(
                                "Delete this chat entry?",
                                f"do_delete_chat_{entry['id']}"
                            )

                    if st.session_state.get(f"do_delete_chat_{entry['id']}"):
                        st.session_state.pop(f"do_delete_chat_{entry['id']}", None)
                        with st.spinner("Deleting..."):
                            r = api("DELETE", f"/chat/history/{entry['id']}")
                        if r.status_code == 200:
                            st.session_state["chat_history_data"] = [
                                e for e in st.session_state["chat_history_data"]
                                if e["id"] != entry["id"]
                            ]
                            st.rerun()
                        else:
                            st.error(r.text)


# ROUTER

if st.session_state.page == "landing":
    landing_page()
elif st.session_state.page == "login":
    login_page()
elif st.session_state.page == "signup":
    signup_page()
elif st.session_state.page == "reset_password":
    reset_password_page()
elif st.session_state.page == "app":
    st.sidebar.title("TutorRAG 🎓")
    st.sidebar.success(
        f"{st.session_state.username} ({st.session_state.role})"
    )
    st.sidebar.button("Logout", on_click=logout)

    if st.session_state.role == "Teacher":
        teacher_dashboard()
    else:
        student_dashboard()