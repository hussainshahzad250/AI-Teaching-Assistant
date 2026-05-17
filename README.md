# TutorRAG 🎓

An AI-powered tutoring app that lets teachers upload documents and students ask questions, generate quizzes, and track progress — all powered by RAG + LLMs.

---

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip
- MongoDB instance (local or Atlas)
- Groq API key — [console.groq.com](https://console.groq.com)
- Google AI API key — [aistudio.google.com](https://aistudio.google.com)
- Pinecone account — [app.pinecone.io](https://app.pinecone.io)

---

## Environment Variables

Create a `.env` file in the `server/` directory:

```env
MONGO_URI=your_mongodb_connection_string
DB_NAME=your_database_name

GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_genai_api_key

PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_pinecone_index_name
PINECONE_ENV=us-east-1
```

> The Pinecone index will be created automatically on first document upload if it doesn't exist (dimension: 3072, metric: cosine).

Create a `.env` file in the `client/` directory:

```env
BACKEND_URL=http://localhost:8000
```

---

## Setup & Run

### 1. Install server dependencies

```bash
cd server
uv pip install -r requirements.txt
```

Or with pip:

```bash
pip install -r server/requirements.txt
```

### 2. Start the backend server

```bash
cd server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 3. Install client dependencies

```bash
cd client
uv pip install -r requirements.txt
```

Or with pip:

```bash
pip install -r client/requirements.txt
```

### 4. Start the frontend

```bash
cd client
streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`.

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/signup/student` | Register a student | No |
| POST | `/signup/teacher` | Register a teacher | No |
| GET | `/login` | Login and get role info | Basic |
| POST | `/upload_docs` | Upload and index a PDF | Basic |
| POST | `/chat` | Ask a question (RAG) | Basic |
| POST | `/quiz` | Generate a quiz | Basic |
| POST | `/quiz/check` | Submit quiz answers | Basic |
| GET | `/quiz/history` | Get quiz history | Basic |

---

## Project Structure

```
tutor-rag/
├── server/                  # FastAPI backend
│   ├── auth/                # Signup, login, password hashing
│   ├── chat/                # RAG query & quiz generation
│   ├── docs/                # PDF upload, chunking, vectorstore
│   ├── config/              # MongoDB connection
│   ├── upload_docs/         # Temporary PDF storage
│   └── main.py              # Server entry point
└── client/                  # Streamlit frontend
    ├── assets/              # UI images
    └── main.py              # Client entry point
```

---

## Tech Stack

- **Backend**: FastAPI, LangChain, Groq (LLaMA 3.3), Google Generative AI Embeddings
- **Vector DB**: Pinecone
- **Database**: MongoDB
- **Frontend**: Streamlit
- **Auth**: HTTP Basic Auth + bcrypt
