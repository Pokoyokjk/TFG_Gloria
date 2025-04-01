from rdflib import Namespace, Graph, URIRef
from rdflib.query import Result

# -------- AUX FUNCTIONS FOR AMOR EXPERIMENTS QUERIES ----------- # 

def get_experiment(graph: Graph, namespace: str, experiment_id: str):
    # Define the specific experiment
    ns = Namespace(namespace)
    experiment_uri = ns[experiment_id]
    # Define the SPARQL query
    query = f"""
    PREFIX amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#>

    SELECT ?predicate ?object
    WHERE {{
        <{experiment_uri}> a amor-exp:Experiment .
        <{experiment_uri}> ?predicate ?object .
    }}
    """
    # Execute the query
    results = graph.query(query)
    # Return the results
    return experiment_uri, results

def get_logged_activities(graph: Graph, namespace: str, experiment_id: str) -> Result:
    # Define the specific experiment
    ns = Namespace(namespace)
    experiment_uri: URIRef = ns[experiment_id]
    # Define the SPARQL query
    query = f"""
    PREFIX segb: <http://www.gsi.upm.es/ontologies/segb/ns#>
    PREFIX amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#>
    
    DESCRIBE ?activity
    WHERE {{
        ?activity a segb:LoggedActivity .
        ?activity amor-exp:isRelatedWithExperiment <{experiment_uri}> .
    }}
    """
    # Execute the query
    results = graph.query(query)
    # Return the results
    return results

def get_experiment_with_activities(source: Graph, namespace: str, experiment_id: str) -> Graph:
    # Get the experiment details
    try:
        experiment_uri, experiment_details = get_experiment(source, namespace, experiment_id)
    except Exception as e:
        raise Exception(f"Error getting experiment details: {str(e)}")
    # Get the logged activities related to the experiment
    try:
        logged_activities = get_logged_activities(source, namespace, experiment_id)
    except Exception as e:
        raise Exception(f"Error getting logged activities: {str(e)}")
    # Return both experiment details and logged activities in a new graph
    result_graph = Graph()
    # Bind all prefixes from the source graph to the result graph
    for prefix, namespace_uri in source.namespaces():
        result_graph.bind(prefix, namespace_uri)
    # Add the experiment details and logged activities to the result graph
    for row in experiment_details:
        result_graph.add((experiment_uri, row.predicate, row.object))

    for triple in logged_activities:
        subject, predicate, obj = triple
        result_graph.add((subject, predicate, obj))
        
    return result_graph


def get_experiment_list(graph: Graph):
    query = """
        PREFIX amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#>
        
        SELECT ?experiment_uri 
        WHERE {
            ?experiment_uri a amor-exp:Experiment .
        }
    """
    result = graph.query(query)
    return result 