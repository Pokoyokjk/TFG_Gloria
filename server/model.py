from mongoengine import Document, DynamicField, DateTimeField, StringField, ValidationError, connect, get_db, ReferenceField, ObjectIdField
from datetime import datetime
import utils.semantic
import hashlib
from bson import ObjectId

import logging
import os

logger = logging.getLogger("segb.server.model")

logger.info("Loading module model...")

# ------------ DOCUMENTS DEFINITION ------------ #

class Graph(Document):
    _id = StringField(primary_key=True)
    updated_at = DateTimeField()
    graph_data = DynamicField (required=True)

    def clean(self):
        if not isinstance(self.graph_data, dict):
            raise ValidationError("'graph' field must be a document in JSON format")
        
class Insertion (Document):
    _id = ObjectIdField(primary_key=True)
    log = ReferenceField('Log', required=True)
    ttl_content = StringField(required=True)
    
class Deletion (Document):
    _id = ObjectIdField(primary_key=True)
    log = ReferenceField('Log', required=True)
    ttl_deleted_graph = StringField(required=True) 
    
class Log (Document):
    _id = ObjectIdField(primary_key=True)
    # has_previous_log = ReferenceField('Log', required=False)
    uploaded_at = DateTimeField()
    origin_ip = StringField (required=True, regex="^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$")
    action_type = StringField(required=True, choices=['insertion', 'deletion'])
    action = ObjectIdField (required=True)
    user_details = StringField () # decoded token data (username, roles, etc.)


def serialize_log(log) -> dict:
    return {
        "_id": str(log._id),
        "uploaded_at": log.uploaded_at.isoformat() if log.uploaded_at else None,
        "origin_ip": log.origin_ip,
        "action_type": log.action_type,
        "action": str(log.action) if log.action else None,
        "user_details": log.user_details if log.user_details else None,
    }


def connect_to_db(db_service: str) -> None:
    logger.info("Connecting to the database...")
    logger.info(f"Database service: {db_service}")
    connect('graph', host=db_service, port=27017)
    logger.info("Database connection established.")
    
# ------------ INSERT FUNCTIONS ------------ #
    
def save_json_ld(json_ld_data:dict) -> None:
    logger.debug(f"Saving JSON-LD data to the database")
    graph = Graph.objects(_id='0').first()
    logger.debug(f"Graph found")
    if graph:
        json_ld_data = utils.semantic.update_prefixes(graph.graph_data, json_ld_data)
        json_ld_data = utils.semantic.update_graph(graph.graph_data, json_ld_data)
        logger.debug(f"Graph ready to be saved")
        graph.update(
            set__graph_data=json_ld_data,
            set__updated_at=datetime.now()
        )
        logger.debug(f"Graph updated")
    else:
        graph = Graph (
           _id = '0',
           updated_at = datetime.now(),
           graph_data = json_ld_data
        )
    graph.save()
    logger.debug(f"Graph saved")

def log_ttl_content(ttl:str, ip_addr:str, user_details: str) -> None:
    
    """
        Atomic Transaction 
    """
    logger.debug(f"Logging TTL content")
    logger.debug(f"Origin IP: {ip_addr}")
    log_id = ObjectId()
    logger.debug(f"Log ID: {log_id}")
    insertion_id = ObjectId()
    logger.debug(f"Insertion ID: {insertion_id}")
    
    db = get_db()
    session = db.client.start_session()
    session.start_transaction()
    logger.debug(f"Session started")
    try:
        
        log = Log (
            _id = log_id,
            uploaded_at = datetime.now(),
            origin_ip = ip_addr,
            action_type = 'insertion',
            action = insertion_id,
            user_details = user_details
        )
        log.save()        
        logger.debug(f"Log saved")
        insertion = Insertion (
        _id = insertion_id,
        log = log,
        ttl_content = ttl
     )
        insertion.save()
        logger.debug(f"Insertion saved")
    
        session.commit_transaction()
        return True
    
    except Exception as ex:
        logger.error(f"Error logging TTL content: {ex}")
        session.abort_transaction()
        return False
    finally:
        session.end_session()
        logger.debug(f"Session ended")
        
    
    
    
# ------------ READ FUNCTIONS ------------ #


def get_raw_graph_from_db() -> DynamicField:
    logger.debug(f"Getting graph from DB")
    graph = None
    try:
        graph = Graph.objects(_id='0').first()
    except:
        logger.error(f"Error getting graph from DB")
        pass
    result = graph.graph_data if isinstance(graph, Graph) else graph
    if not result:
        logger.debug(f"Graph not found in DB")
    else:
        logger.debug(f"Graph found in DB")
    return result



def get_logs_list() -> list:
    logger.debug(f"Getting logs from DB")
    logs = Log.objects()
    serialized_logs = []
    if logs:
        logger.debug(f"Logs found: {len(logs)}")
        serialized_logs = [serialize_log(log) for log in logs]
    return serialized_logs

def get_log_info(log_id: str) -> dict:
    logger.debug(f"Getting log info for ID: {log_id}")
    try:
        log_id = ObjectId(log_id)
    except Exception:
        return None

    log = Log.objects(_id=log_id).first()
    if not log:
        logger.debug(f"Log not found")
        return None
    logger.debug(f"Log found: {log}")
    action_data = None
    if log.action_type == 'insertion':
        action = Insertion.objects(_id=log.action).first()
        if action:
            action_data = {
                "ttl_content": action.ttl_content
            }
    elif log.action_type == 'deletion':
        action = Deletion.objects(_id=log.action).first()
        if action:
            action_data = {
                "ttl_deleted_graph": action.ttl_deleted_graph
            }
    return {
        "log": serialize_log(log),
        "action": action_data
    }


# ------------ DELETE FUNCTIONS ------------ #

def clear_graph(ip_addr:str, user_details: str) -> bool:
    
    """
        Atomic Transaction 
    """
    logger.debug(f"Clearing graph")
    log_id = ObjectId()
    deletion_id = ObjectId()
        
    db = get_db()
    session = db.client.start_session()
    session.start_transaction()
    
    current_graph = get_raw_graph_from_db()
    if not current_graph:
        logger.debug(f"No current graph found to clear")
        return False
    graph = utils.semantic.get_graph_from_json(current_graph)
    turtle_data = utils.semantic.convert_graph_to_turtle(graph)
    
    try:
        
        log = Log (
            _id = log_id,
            uploaded_at = datetime.now(),
            origin_ip = ip_addr,
            action_type = 'deletion',
            action = deletion_id,
            user_details = user_details
        )
        log.save()        
        
        deletion = Deletion (
            _id = deletion_id,
            log = log,
            ttl_deleted_graph = turtle_data
        )
        deletion.save()
        
        graph = Graph.objects(_id='0').first()
        graph.delete()
            
        session.commit_transaction()
        logger.debug(f"Graph deleted")
        logger.debug(f"Deletion ID: {deletion_id}")
        logger.debug(f"Log ID: {log_id}")
        logger.debug(f"Deleted graph -> {len(graph)} triples deleted")
        logger.debug(f"Deletion saved")
        logger.info("Graph cleared successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error clearing graph: {e}")
        session.abort_transaction()
        return False
    finally:
        session.end_session()
