from fastapi import FastAPI
from auth.route import router as auth_router
from docs.route import router as doc_router
from chat.route import router as chat_router


app=FastAPI()



app.include_router(auth_router)
app.include_router(doc_router)
app.include_router(chat_router)


@app.get("/")
def home():
    return {"message":"Welcome to the User Management API"}

# server/main.py
import uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
