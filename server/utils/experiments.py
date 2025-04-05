from rdflib import Namespace, Graph, URIRef
from rdflib.query import Result
import os
import logging

logging_level = os.getenv("LOGGING_LEVEL", "INFO").upper()
log_file = os.getenv("SERVER_LOG_FILE", "segb_server.log")
# Ensure the logs directory exists
os.makedirs('./logs', exist_ok=True)
file_handler = logging.FileHandler(
    filename=f'./logs/{log_file}',
    mode='a',
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s -> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger = logging.getLogger("segb_server.utils.experiments")
logger.setLevel(getattr(logging, logging_level, logging.INFO))
logger.addHandler(file_handler)


logger.info("Loading module utils.experiments...")

# -------- AUX FUNCTIONS FOR AMOR EXPERIMENTS QUERIES ----------- # 

def get_experiment(graph: Graph, namespace: str, experiment_id: str):
    # Define the specific experiment
    ns = Namespace(namespace)
    experiment_uri = ns[experiment_id]
    # Define the SPARQL query
    logger.info(f"Getting experiment details for {experiment_uri}")
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
    logger.info(f"Experiment details for {experiment_uri} retrieved successfully.")
    return experiment_uri, results

def get_logged_activities(graph: Graph, namespace: str, experiment_id: str) -> Result:
    # Define the specific experiment
    ns = Namespace(namespace)
    experiment_uri: URIRef = ns[experiment_id]
    # Define the SPARQL query
    logger.info(f"Getting logged activities for {experiment_uri}")
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
    logger.info(f"Logged activities for {experiment_uri} retrieved successfully.")
    # Return the results
    return results

def get_experiment_with_activities(source: Graph, namespace: str, experiment_id: str) -> Graph:
    # Get the experiment details
    try:
        logger.info(f"Getting experiment details...")
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
    
    logger.info(f"Experiment details for {experiment_uri} retrieved successfully.")
    logger.debug(f"Resulting graph has {len(result_graph)} triples.")
    return result_graph


def get_experiment_list(graph: Graph) -> dict:
    query = """
        PREFIX amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#>
        
        SELECT ?experiment_uri 
        WHERE {
            ?experiment_uri a amor-exp:Experiment .
        }
    """
    result = graph.query(query)
    return result.serialize(format="json", encoding="utf-8")