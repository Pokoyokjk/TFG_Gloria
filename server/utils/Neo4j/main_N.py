from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Annotated
import logging

from utils.Neo4j.model_N import store_modification, connect_to_db, constraint_graphinit, get_recent_logs, get_logs_by_date
from utils.credentials import User, validate_token
import os


logging_level = os.getenv("LOGGING_LEVEL_NEO", "INFO").upper()
log_file = os.getenv("SERVER_LOG_FILE_NEO", "mod_history_neo4j.log")
# Ensure the logs directory exists
os.makedirs('/logs', exist_ok=True) 
file_handler = logging.FileHandler(
    filename=f'/logs/{log_file}',
    mode='a',
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s -> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger = logging.getLogger("mod_history_neo4j")
logger.setLevel(getattr(logging, logging_level, logging.INFO))
logger.addHandler(file_handler)

logger.info("Starting SEGB server...")
logger.info("Logging level set to %s", logging_level)
    

app = FastAPI() # server instance
logger.info("Connecting to Neo4j...")
connect_to_db()

#USE ONLY ONCE:
# constraint_graphinit() 

logger.info("Connected to Neo4j for historical graph.")

class Log(BaseModel):
    action:str
    ttl_content:str
    user: str

@app.post("/modification")
async def register_modificacion(
    request: Request,
    input_data: Log,
    user: Annotated[User, Depends(validate_token)], # type: ignore
):
    if input_data.action not in ["insertion", "deletion"]:
        raise HTTPException(status_code=400, detail="Invalid action type. Must be 'insertion' or 'deletion'.")
    try:
        origin_ip = request.client.host
        actor = input_data.user or user.username or "anonymous"
        log_id = store_modification(input_data.action, origin_ip, actor, input_data.ttl_content)

        return JSONResponse(
            content={"message": "Modification registered successfully", "log_id": log_id},
            status_code=201)
    
    except Exception as e:
        logger.error(f"Error registering modification: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    
@app.get("/modifications")
async def get_modifications(limit: int):
    try:
        logs = get_recent_logs(limit)
        return logs
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving logs")

# To filter by date, we can use the following endpoint:
@app.get("/modifications_date")
async def get_modifications_by_date(start_date:str, end_date:str):
    try:
        logs = get_logs_by_date(start_date, end_date)
        return logs
    except Exception as e:
        logger.error(f"Error fetching logs by date: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving logs by date")









