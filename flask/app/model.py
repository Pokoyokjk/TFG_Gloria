from mongoengine import Document, DynamicField, DateTimeField, StringField, ValidationError, connect
from datetime import datetime
import aux

class Graph(Document):
    _id = StringField(primary_key=True)
    updated_at = DateTimeField()
    graph_data = DynamicField (required=True) 

    def clean(self):
        if not isinstance(self.graph_data, dict):
            raise ValidationError("'graph' field must be a document in JSON format")

    
def connect_to_db():
    connect('graph', host='mongodb', port=27017)
    
    
def save_json_ld(json_ld_data:dict):
    graph = Graph.objects(_id='0').first()
    if graph:
        json_ld_data = aux.update_prefixes(graph.graph_data, json_ld_data)
        json_ld_data = aux.update_graph(graph.graph_data, json_ld_data)
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
    
        
def get_json_ld():
    graph = Graph.objects(_id='0').first()
    return graph   