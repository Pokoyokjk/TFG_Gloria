from rdflib import Graph
import json


# -------- AUX FUNCTIONS FOR APP.PY ----------- # 

def process_turtle_data(data):

    graph = Graph()
    graph.parse(data=data, format="turtle")
    return graph

def convert_turtle_to_json_ld(ttl_graph_data):
    
    graph_namespace = ttl_graph_data.namespaces()
    prefixes = {prefix: str(uri) for prefix, uri in graph_namespace}
    serialized_json_ld = ttl_graph_data.serialize(format="json-ld", context=prefixes)
    json_ld_data = json.loads(serialized_json_ld)
    
    context = json_ld_data.get("@context", {})
    
    if "@graph" not in json_ld_data:
        json_ld_data.pop("@context")
        data = json_ld_data if isinstance(json_ld_data, list) else [json_ld_data]
        json_ld_data = {"@context": context, "@graph": data}
    
    return json_ld_data


# -------- AUX FUNCTIONS FOR MODEL.PY ----------- # 

def update_prefixes (graph_data:dict, json_ld_data:dict):
    new_prefixes = json_ld_data.get("@context", None)
    current_prefixes = graph_data.get("@context", {})
    if new_prefixes:
        for key, value in new_prefixes.items():
            if key not in current_prefixes:
                current_prefixes.update({key:value})
    json_ld_data["@context"].update(current_prefixes)
    return json_ld_data


def update_graph (graph_data: dict, json_ld_data:dict):
    old_graph = graph_data.get("@graph", [])
    new_graph = old_graph + [json_triple for json_triple in json_ld_data["@graph"]]
    json_ld_data["@graph"] = new_graph
    return json_ld_data


        