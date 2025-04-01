from mongoengine import Document, DynamicField, DateTimeField, StringField, ValidationError, connect
from pymongo.errors import ServerSelectionTimeoutError
from datetime import datetime
import semantic_utils as semantic_utils

class Graph(Document):
    _id = StringField(primary_key=True)
    updated_at = DateTimeField()
    graph_data = DynamicField (required=True)

    def clean(self):
        if not isinstance(self.graph_data, dict):
            raise ValidationError("'graph' field must be a document in JSON format")
        
class TTL(Document):
    uploaded_at = DateTimeField()
    origin_ip = StringField(required=True, regex="^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$")
    ttl_content = StringField(required=True)

    
def connect_to_db() -> None:
    connect('graph', host='amor-segb-mongodb', port=27017)
    
    
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
    
        
def get_raw_graph_from_db() -> DynamicField:
    graph = None
    try:
        graph = Graph.objects(_id='0').first()
    except ServerSelectionTimeoutError:
        pass
    return graph.graph_data if isinstance(graph, Graph) else graph


def save_ttl_content(ttl:str, ip_addr:str) -> None:
    ttl = TTL (
        uploaded_at = datetime.now(),
        origin_ip = ip_addr,
        ttl_content = ttl
    )
    ttl.save()
    
    
def get_ttl_content() -> list:
    ttl_list = TTL.objects()
    dict_ttl_list = semantic_utils.convert_ttl_info_to_dict(ttl_list)
    return dict_ttl_list