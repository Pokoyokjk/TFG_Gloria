from mongoengine import Document, DynamicField, DateTimeField, StringField, ValidationError, connect, get_db, ReferenceField, ObjectIdField
from datetime import datetime
import semantic_utils as semantic_utils
import hashlib
from bson import ObjectId


import logging

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
    deleted_graph_hash = StringField(required=True, regex="^[a-fA-F0-9]{64}$") 
    
class Log (Document):
    _id = ObjectIdField(primary_key=True)
    # has_previous_log = ReferenceField('Log', required=False)
    uploaded_at = DateTimeField()
    origin_ip = StringField (required=True, regex="^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$")
    action_type = StringField(required=True, choices=['insertion', 'deletion'])
    action = ObjectIdField (required=True)
    
    
def connect_to_db() -> None:
    connect('graph', host='database', port=27017)
    
    
    
# ------------ INSERT FUNCTIONS ------------ #
    
def save_json_ld(json_ld_data:dict) -> None:
    
    graph = Graph.objects(_id='0').first()
    if graph:
        json_ld_data = semantic_utils.update_prefixes(graph.graph_data, json_ld_data)
        json_ld_data = semantic_utils.update_graph(graph.graph_data, json_ld_data)
        graph.update(
            set__graph_data=json_ld_data,
            set__updated_at=datetime.now()
        )
    else:
        graph = Graph (
           _id = '0',
           updated_at = datetime.now(),
           graph_data = json_ld_data
        )
    graph.save()
    



def log_ttl_content(ttl:str, ip_addr:str) -> None:
    
    """
        Atomic Transaction 
    """
    
    log_id = ObjectId()
    insertion_id = ObjectId()
    
    db = get_db()
    session = db.client.start_session()
    session.start_transaction()
    try:
        
        log = Log (
            _id = log_id,
            uploaded_at = datetime.now(),
            origin_ip = ip_addr,
            action_type = 'insertion',
            action = insertion_id
        )
        log.save()        
        
        insertion = Insertion (
        _id = insertion_id,
        log = log,
        ttl_content = ttl
     )
        insertion.save()
    
        session.commit_transaction()
        return True
    
    except Exception as ex:
        session.abort_transaction()
        return False
    finally:
        session.end_session()
        
    
    
    
# ------------ READ FUNCTIONS ------------ #


def get_raw_graph_from_db() -> DynamicField:
    graph = None
    try:
        graph = Graph.objects(_id='0').first()
    except:
        pass
    return graph.graph_data if isinstance(graph, Graph) else graph



def get_logs_list() -> list:
    logs = Log.objects()
    serialized_logs = []
    if logs:
        serialized_logs = [semantic_utils.serialize_log(log) for log in logs]
    return serialized_logs

def get_log_info(log_id: str) -> dict:

    try:
        log_id = ObjectId(log_id)
    except Exception:
        return None

    log = Log.objects(_id=log_id).first()
    if not log:
        return None

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
                "deleted_graph_hash": action.deleted_graph_hash
            }

    return {
        "log": semantic_utils.serialize_log(log),
        "action": action_data
    }


# ------------ DELETE FUNCTIONS ------------ #

def clear_graph(ip_addr:str) -> bool:
    
    """
        Atomic Transaction 
    """
    log_id = ObjectId()
    deletion_id = ObjectId()
        
    db = get_db()
    session = db.client.start_session()
    session.start_transaction()
    
    current_graph = get_raw_graph_from_db()
    if not current_graph:
        return False
        
    current_graph_hash = hashlib.sha256(str(current_graph).encode('utf-8')).hexdigest()
    
    try:
        
        log = Log (
            _id = log_id,
            uploaded_at = datetime.now(),
            origin_ip = ip_addr,
            action_type = 'deletion',
            action = deletion_id
        )
        log.save()        
        
        deletion = Deletion (
            _id = deletion_id,
            log = log,
            deleted_graph_hash = current_graph_hash
        )
        deletion.save()
        
        graph = Graph.objects(_id='0').first()
        graph.delete()
            
        session.commit_transaction()
        return True
    
    except Exception as e:
        session.abort_transaction()
        return False
    finally:
        session.end_session()
