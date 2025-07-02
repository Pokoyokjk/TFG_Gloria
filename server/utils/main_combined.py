from fastapi import FastAPI, HTTPException, Request, Depends, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Annotated
from utils.credentials import User, validate_token, Role
from utils.Neo4j.model_N import store_modification, connect_to_db, get_recent_logs, get_logs_by_date, store_bulk_deletion
from utils.Virtuoso.model_V import insert_ttl, get_ttls, run_custom_query, delete_all_triples
import logging
import os
from fastapi.responses import PlainTextResponse
from rdflib import Graph
from asyncio import Lock # atomic transactions 
from typing import Optional
from utils.RAG import rag_with_sparql
from utils.Eval import evaluate_rag_model, evaluate_batch

transaction_lock = Lock()



# Logging
logging_level = os.getenv("LOGGING_LEVEL_COMBINED", "INFO").upper()
log_file = os.getenv("SERVER_LOG_FILE_COMBINED", "combined.log")
os.makedirs('/logs', exist_ok=True)
file_handler = logging.FileHandler(f'/logs/{log_file}', mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -> %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

logger = logging.getLogger("combined_logger")
logger.setLevel(getattr(logging, logging_level, logging.INFO))
logger.addHandler(file_handler)
logger.info("Starting Combined Server...")


# Neo4j Connection
logger.info("Connecting to Neo4j...")
connect_to_db()
logger.info("Neo4j connected successfully.")

app = FastAPI()

class TTLContent(BaseModel):
    ttl_content: str
    user: str  # Optional, can be overridden by token

class DeleteRequest(BaseModel):
    user: Optional[str] = None

class RAGRequest(BaseModel):
    question: str

class RAGEvalRequest(BaseModel):
    question: str
    reference: str

class RAGBatchRequest(BaseModel):
    dataset: list[dict]   # cada dict con {"question": "...", "expected_answer": "..."}



@app.post("/ttl")
async def insert_ttl_combined(
    request: Request,
    data: TTLContent,
    user: Annotated[User, Depends(validate_token)]
):
    logger.info(f"Received post for log from IP: {request.client.host} from user {user.name} (username: {user.username} - roles: {user.roles})")
    if not (Role.LOGGER.value in user.roles or Role.ADMIN.value in user.roles):
        logger.info(f"User {user.name} (username: {user.username} - roles: {user.roles}) does not have permission to perform this action")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to perform this action"
        )
    
    if transaction_lock.locked():
        raise HTTPException(
            status_code=429,
            detail="Another transaction is in progress. Please try again later."
        )
    
    async with transaction_lock:    
        try:
            origin_ip = request.client.host
            actor = data.user or user.username or "anonymous"

            # Insert into Virtuoso
            log_id = insert_ttl(data.ttl_content)

            # Store in Neo4j as insertion
            store_modification("insertion", origin_ip, actor, data.ttl_content)

            return JSONResponse(
                content={"message": "TTL inserted into both Virtuoso and Neo4j", "log_id": log_id},
                status_code=201
            )
        except Exception as e:
            logger.exception("Insertion failed")
            raise HTTPException(status_code=500, detail=f"Error inserting TTL: {str(e)}")



@app.get("/events", response_class=PlainTextResponse) 
async def get_events(user: Annotated[User, Depends(validate_token)]):
    logger.info(f"Received request for log from user {user.name} (username: {user.username} - roles: {user.roles})")
    if not (Role.AUDITOR.value in user.roles or Role.ADMIN.value in user.roles):
        logger.info(f"User {user.name} (username: {user.username} - roles: {user.roles}) does not have permission to perform this action")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to perform this action"
        )
    try:
        ttl_data = get_ttls()       
        return PlainTextResponse(content=ttl_data, media_type="text/turtle") # so that it returns in TTL format instead of serialized JSON
    except Exception as e:
        logger.exception("Failed fetching events")
        raise HTTPException(status_code=500, detail="Error fetching events")


@app.get("/query")
async def execute_query(user: Annotated[User, Depends(validate_token)], query: str):
    logger.info(f"Received request for query from user {user.name} (username: {user.username} - roles: {user.roles})")
    if Role.ADMIN.value not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to perform this action"
        )
    try:
        return run_custom_query(query)
    except Exception as e:
        logger.exception("SPARQL query failed")
        raise HTTPException(status_code=500, detail=f"SPARQL error: {str(e)}")


@app.get("/modifications")
async def get_modifications(limit: int, request: Request, user: Annotated[User, Depends(validate_token)]):
    logger.info(f"Received request for history from IP: {request.client.host} from user {user.name} (username: {user.username} - roles: {user.roles})")
    if not (Role.AUDITOR.value in user.roles or Role.ADMIN.value in user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to perform this action"
        )
    try:
        return get_recent_logs(limit)
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving logs")


@app.get("/modifications_date")
async def get_modifications_by_date(start_date: str, end_date: str, request: Request, user: Annotated[User, Depends(validate_token)]):
    logger.info(f"Received request for history by date from IP: {request.client.host} from user {user.name} (username: {user.username} - roles: {user.roles})")
    if not (Role.AUDITOR.value in user.roles or Role.ADMIN.value in user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to perform this action"
        )
    
    try:
        return get_logs_by_date(start_date, end_date)
    except Exception as e:
        logger.error(f"Error fetching logs by date: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving logs by date")
    
@app.post("/ttl/delete_all")
async def delete_all_ttls(request: Request, data: DeleteRequest, user: Annotated[User, Depends(validate_token)]):
    logger.info(f"Received post for delete all log from user {user.name} (username: {user.username} - roles: {user.roles})")
    if Role.ADMIN.value not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to perform this action"
        )

    try:
        origin_ip = request.client.host
        actor = data.user or user.username or "anonymous"

        # Get all TTLs from Virtuoso
        ttl_text = get_ttls()
        if not ttl_text:
            return JSONResponse(content={"message": "No TTLs to delete"}, status_code=200)

        # Convert TTL to RDF graph
        g = Graph()
        g.parse(data=ttl_text, format="turtle")

        # Convert to TTL lines
        ttl_lines = []
        for s, p, o in g:
            line = f"{s.n3()} {p.n3()} {o.n3()} ."
            ttl_lines.append(line)

        # Save in Neo4j as deletion
        store_bulk_deletion(origin_ip, actor, ttl_lines)

        # Delete graph
        delete_all_triples()

        return JSONResponse(content={"message": "Graph cleared and deletions logged."}, status_code=200)

    except Exception as e:
        logger.exception("Deletion failed")
        raise HTTPException(status_code=500, detail=f"Error deleting TTLs: {str(e)}")
    

@app.post("/rag/ask")
async def ask_rag(data: RAGRequest, user: Annotated[User, Depends(validate_token)]):
    try:
        logger.info(f"RAG question received from user: {user.username}")

        # Call RAG function
        answer = rag_with_sparql(data.question)
        
        return JSONResponse(content={"answer": answer}, status_code=200)

    except Exception as e:
        logger.exception("RAG processing failed")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
    

@app.post("/rag/evaluate")
async def evaluate_rag_endpoint(data: RAGEvalRequest,
                                user: Annotated[User, Depends(validate_token)]):
    """
    Devuelve respuesta del RAG y métricas simples contra la referencia.
    """
    try:
        logger.info(f"RAG-eval question by {user.username}")
        result = evaluate_rag_model(data.question, data.reference)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.exception("RAG evaluation failed")
        raise HTTPException(status_code=500, detail=f"Error evaluating RAG: {e}")  

@app.post("/rag/evaluate_batch")
async def evaluate_rag_batch(data: RAGBatchRequest,
                             user: Annotated[User, Depends(validate_token)]):
    try:
        logger.info(f"Batch RAG-eval by {user.username} – {len(data.dataset)} samples")
        result = evaluate_batch(data.dataset)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.exception("Batch RAG evaluation failed")
        raise HTTPException(status_code=500, detail=f"Batch eval error: {e}")


    