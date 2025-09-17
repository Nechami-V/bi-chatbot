from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "BI Chatbot API is running"}

@app.get("/ask")
def ask(question: str):
    return {
        "question": question,
        "answer": "תשובה לדוגמה - בהמשך נחבר לנתוני BI"
    }
