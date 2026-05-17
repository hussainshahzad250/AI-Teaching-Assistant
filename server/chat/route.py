from fastapi import APIRouter, HTTPException, Depends, Body
from auth.route import authenticate
from chat.chat_query import answer_query,quiz_generation
from pydantic import BaseModel
from typing import List, Optional
import datetime
from config.db import (
    chat_history_collection,quizzes_collection,quiz_history
)
from bson.objectid import ObjectId


router=APIRouter()

class QuizRequest(BaseModel):
    topic:str
    num_questions:Optional[int]=3

class QuizAnswerRequest(BaseModel):
    quiz_id:str
    answers:List[str]

@router.get("/chat/history")
async def get_chat_history(user=Depends(authenticate)):
    if user["role"] != "Student":
        raise HTTPException(status_code=403, detail="Only students can view chat history")

    cursor = chat_history_collection.find(
        {"user_id": user["user_id"]}
    ).sort("timestamp", -1).limit(100)

    history = []
    for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        doc.pop("user_id", None)
        doc["timestamp"] = doc["timestamp"].strftime("%Y-%m-%d %H:%M")
        history.append(doc)

    return {"history": history}


@router.delete("/chat/history")
async def delete_chat_history(user=Depends(authenticate)):
    if user["role"] != "Student":
        raise HTTPException(status_code=403, detail="Only students can delete chat history")
    result = chat_history_collection.delete_many({"user_id": user["user_id"]})
    return {"message": f"Deleted {result.deleted_count} chat records"}


@router.delete("/chat/history/{chat_id}")
async def delete_single_chat(chat_id: str, user=Depends(authenticate)):
    if user["role"] != "Student":
        raise HTTPException(status_code=403, detail="Only students can delete chat history")
    doc = chat_history_collection.find_one({"_id": ObjectId(chat_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Chat record not found")
    if doc["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    chat_history_collection.delete_one({"_id": ObjectId(chat_id)})
    return {"message": "Chat record deleted"}


@router.delete("/quiz/history")
async def delete_quiz_history(user=Depends(authenticate)):
    if user["role"] != "Student":
        raise HTTPException(status_code=403, detail="Only students can delete quiz history")
    result = quiz_history.delete_many({"user_id": user["user_id"]})
    return {"message": f"Deleted {result.deleted_count} quiz attempts"}


@router.delete("/quiz/history/{attempt_id}")
async def delete_single_quiz(attempt_id: str, user=Depends(authenticate)):
    if user["role"] != "Student":
        raise HTTPException(status_code=403, detail="Only students can delete quiz history")
    doc = quiz_history.find_one({"_id": ObjectId(attempt_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")
    if doc["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    quiz_history.delete_one({"_id": ObjectId(attempt_id)})
    return {"message": "Quiz attempt deleted"}


@router.post("/chat")
async def chat(user=Depends(authenticate),query:str=Body(...,embed=True)):
    if user["role"] != "Student":
        raise HTTPException(
            status_code=403,
            details="Only student can ask questions"
        )
    
    response=await answer_query(
        query,user["role"],user["grade"],
    )

    chat_history_collection.insert_one({
        "user_id":user["user_id"],
        "timestamp":datetime.datetime.utcnow(),
        "query":query,
        "response":response["answer"],
        "sources":response["sources"],
    })

    return response

@router.post("/quiz")
async def quiz(request:QuizRequest, user=Depends(authenticate)):
    if user["role"] != "Student":
        raise HTTPException(
            status_code=403,
            details="Only student can generate quizzes.."
        )
    
    response= await quiz_generation(
        request.topic,
        user["role"],
        user["grade"],
        request.num_questions
    )

    quiz_doc={
        "user_id":user["user_id"],
        "timestamp":datetime.datetime.utcnow(),
        "topic":request.topic,
        "quiz_data":response["quiz"],
        "sources":response["sources"]
    }

    result=quizzes_collection.insert_one(quiz_doc)

    return {
        "quiz":response["quiz"],
        "sources":response["sources"],
        "quiz_id":str(result.inserted_id)
    }


@router.post("/quiz/check")
async def check_quiz_answers(request:QuizAnswerRequest,user=Depends(authenticate)):
    quiz_doc=quizzes_collection.find_one(
        {"_id":ObjectId(request.quiz_id)}
    )

    if not quiz_doc:
        raise HTTPException(404,"Quiz not found")
    

    if quiz_doc["user_id"] != user["user_id"]:
        raise HTTPException(403,"Unauthorized")
    

    correct_answers=[]
    for line in quiz_doc["quiz_data"].split("\n"):
        if line.startswith("Correct Answer:"):
            correct_answers.append(line.split(":")[1].strip()[0])

    if len(request.answers) != len(correct_answers):
        raise HTTPException(400, "Answer count mismatch")
    
    score=0
    results=[]


    for i, ans in enumerate(request.answers):
        is_correct=ans.strip().upper() == correct_answers[i]
        if is_correct:
            score +=1

        results.append({
            "question_number":i+1,
            "user_answer":ans,
            "correct_answer":correct_answers[i],
            "is_correct":is_correct
        })

    quiz_history.insert_one({
        "user_id": user["user_id"],
        "quiz_id": request.quiz_id,
        "timestamp": datetime.datetime.utcnow(),
        "topic": quiz_doc["topic"],
        "score": score,
        "total": len(correct_answers),
        "results": results,
        "quiz_content": quiz_doc["quiz_data"],
    })

    return {
        "message":f"Quiz complete, You scored {score}/{len(correct_answers)}",
        "score":score,
        "total":len(correct_answers),
        "results":results
    }


@router.get("/quiz/history")
async def get_quiz_history(user=Depends(authenticate)):
    if user["role"] != "Student":
        raise HTTPException(
            403,
            "Only student can view quiz history"
        )
    
    cursor=quiz_history.find({"user_id":user["user_id"]}).sort("timestamp",-1)

    history=[]
    for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        doc["quiz_id"] = str(doc["quiz_id"])
        doc.pop("user_id", None)
        history.append(doc)


    return {
        "message":f"Found {len(history)} attempts",
        "history":history,
    }