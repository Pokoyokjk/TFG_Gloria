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

class Triple (Document):
    inserted_at = DateTimeField (required=True)
    graph_data = DynamicField (required=True) 
    subject = StringField (required=True)
    predicate = StringField (required=True)
    object = StringField (required=True)
    
    meta = {
        'collection': 'triples'  
    }
    
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
        
        
def save_triples(triples_data:list):
    processed_triples = aux.process_triples(triples_data=triples_data)
    for processed_triple in processed_triples:
        triple = Triple (
            inserted_at = datetime.now(),
            graph_data = processed_triple.get("triple"),
            subject = processed_triple.get("subject"),
            predicate = processed_triple.get("predicate"),
            object = processed_triple.get("object")
        )
        triple.save()