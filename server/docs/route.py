from fastapi import APIRouter, UploadFile,File,Form,HTTPException
from .vectorstore import load_vectorstore
import uuid

router=APIRouter()

@router.post("/upload_docs")
async def upload_docs(file: UploadFile=File(...),grade:int=Form(...),):
    """
    Upload a PDF docuent and index it into:
    - MongoDB (full text chunks)
    - Pinecone (embeddings only)

    Access is set to 'Public' by default
    """

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    doc_id=str(uuid.uuid4())
    ACCESS_ROLE="Public"

    # call vectiorstore function
    try:
        await load_vectorstore(uploaded_files=[file],role=ACCESS_ROLE,doc_id=doc_id,grade=grade)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process and index the document: {str(e)}"
        )
    
    return {
        "message":f"{file.filename} uploaded and indexed successfully",
        "doc_id":doc_id,
        "grade":grade,
        "access":ACCESS_ROLE
    }