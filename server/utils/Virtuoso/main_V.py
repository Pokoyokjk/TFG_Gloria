from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from utils.credentials import User, validate_token
from utils.Virtuoso.model_V import insert_ttl, get_ttls, run_custom_query, delete_all_triples
from rdflib import Graph
from typing import Annotated
import logging
import os
from fastapi.responses import PlainTextResponse


logging_level = os.getenv("LOGGING_LEVEL_VIR", "INFO").upper()
log_file = os.getenv("SERVER_LOG_FILE_VIR", "mod_history_virt.log")
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
logger = logging.getLogger("mod_history_virt")
logger.setLevel(getattr(logging, logging_level, logging.INFO))
logger.addHandler(file_handler)


logger.info("Logging level set to %s", logging_level)  

logger.info("Starting Virtuoso Events Server")


app = FastAPI()

class Event(BaseModel):
    ttl_content: str


@app.post("/event")
async def post_event_ttl(
    data: Event,
    user: Annotated[User, Depends(validate_token)]
):
    try:
        log_id = insert_ttl(data.ttl_content)
        return JSONResponse(content={"message": "Event stored successfully", "log_id": log_id}, status_code=201)
    except Exception as e:
        logger.exception("Exception while inserting event")
        raise HTTPException(status_code=500, detail=f"Error inserting event: {str(e)}")


@app.get("/events", response_class=PlainTextResponse) 
async def get_events(user: Annotated[User, Depends(validate_token)]):
    try:
        ttl_data = get_ttls()
        return PlainTextResponse(content=ttl_data, media_type="text/turtle") # so that it returns in TTL format instead of serialized JSON
    except Exception as e:
        logger.exception("Failed fetching events")
        raise HTTPException(status_code=500, detail="Error fetching events")

@app.get('/query')
async def get_query(
    user: Annotated[User, Depends(validate_token)],
    query: str
):
    try:
        results = run_custom_query(query)
        return results
    except Exception as e:
        logger.exception("Failed to execute SPARQL query")
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")
    

@app.post("/ttl/delete_all")
async def delete_all_ttls(user: Annotated[User, Depends(validate_token)]):
    try:
        # Get all TTLs from Virtuoso
        ttl_text = get_ttls()
        if not ttl_text:
            return JSONResponse(content={"message": "No TTLs to delete"}, status_code=200)

        # Convert TTL to RDF graph
        g = Graph()
        g.parse(data=ttl_text, format="turtle")

        # Convert graph to TTL lines
        ttl_lines = []
        for s, p, o in g:
            line = f"{s.n3()} {p.n3()} {o.n3()} ."
            ttl_lines.append(line)

        # Delete graph
        delete_all_triples()

        return JSONResponse(content={"message": "Graph cleared."}, status_code=200)
    
    except Exception as e:
        logger.exception("Deletion failed")
        raise HTTPException(status_code=500, detail=f"Error deleting TTLs: {str(e)}")

