import uuid
from datetime import datetime
import requests
import os
import logging
from requests.auth import HTTPDigestAuth
import re
from rdflib import Graph, Literal, Namespace, URIRef, BNode
from rdflib.namespace import RDF
from utils.Virtuoso.prefix_utils import extract_prefixes, save_prefixes, load_prefixes, clean_prefixes_with_numbers, save_prefixes_and_entities

logger = logging.getLogger("mod_history_virt")
os.makedirs('/logs', exist_ok=True)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(f'/logs/modelV.log', mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -> %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(file_handler)
logger.info("Starting model_V...")

VIRTUOSO_SPARQL_ENDPOINT = os.getenv("VIRTUOSO_ENDPOINT", "http://amor-segb-virtuoso:8890/sparql-auth")
VIRTUOSO_GRAPH_URI = os.getenv("VIRTUOSO_GRAPH_URI", "http://amor-segb/events")
VIRTUOSO_USER = os.getenv("VIRTUOSO_USER", "dba")
VIRTUOSO_PASSWORD = os.getenv("DBA_PASSWORD", "viryourbear")




# Verification of credentials
logger.info(f"Using Virtuoso endpoint: {VIRTUOSO_SPARQL_ENDPOINT}")
logger.info(f"Virtuoso user: {VIRTUOSO_USER}")
logger.info(f"Virtuoso password: {VIRTUOSO_PASSWORD}")



# Insert log
def insert_ttl(ttl_content: str) -> str:
    log_id = str(uuid.uuid4())

    # TTL into N-Triples (to avoid inserting as a block)
    g = Graph()

    try:
        g.parse(data=ttl_content, format="turtle")
    except Exception as e:
        logger.error(f"Failed to parse TTL content: {e}")
        raise Exception(f"Error parsing TTL content: {str(e)}")
    
    # extract prefixes
    prefixes = extract_prefixes(ttl_content)
    save_prefixes(prefixes) 
    save_prefixes_and_entities(prefixes, ttl_content) 

    for prefix, uri in load_prefixes().items():
        g.bind(prefix, Namespace(uri))

    logger.info(f"Parsed TTL content in NT format: {g.serialize(format="nt")}")

    # Insert with prefixes
    sparql = f"""
    INSERT DATA {{
      GRAPH <{VIRTUOSO_GRAPH_URI}> {{
        {g.serialize(format="nt")}
      }}
    }}
    """

    headers = {
        "Content-Type": "application/sparql-update"
    }
    try:
        response = requests.post(
            VIRTUOSO_SPARQL_ENDPOINT,
            data=sparql.encode("utf-8"),
            auth=HTTPDigestAuth(VIRTUOSO_USER, VIRTUOSO_PASSWORD),
            headers=headers
        )
        response.raise_for_status()
        logger.info(f"TTL inserted successfully with log_id: {log_id}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to insert TTL: {e}")
        logger.error(f"Virtuoso response: {response.text if 'response' in locals() else 'No response'}")
        raise Exception(f"Error inserting TTL into Virtuoso: {str(e)}")

    return log_id



def get_ttls() -> str:
    query = f"""
    CONSTRUCT {{
        ?s ?p ?o .
    }}
    FROM <{VIRTUOSO_GRAPH_URI}>
    WHERE {{
        ?s ?p ?o .
    }}
    """

    response = requests.get(
        VIRTUOSO_SPARQL_ENDPOINT,
        params={"query": query, "format": "application/rdf+xml"},
        auth=HTTPDigestAuth(VIRTUOSO_USER, VIRTUOSO_PASSWORD),
        headers={"Accept": "application/rdf+xml"}
    )

    if response.status_code != 200:
        raise Exception(f"Error fetching TTLs: {response.text}")

    g = Graph()
    # logger.info(f"Previous TTL result: {g.serialize(format="turtle")}")    
    g.parse(data=response.text, format="xml")

    # Bind prefixes to the graph
    for prefix, uri in load_prefixes().items():
        logger.debug(f"Binding prefix: {prefix} to URI: {uri}")
        g.bind(prefix, Namespace(uri))
    logger.info(f"TTL result: {g.serialize(format="turtle")}")
    # g.serialize(destination="/database/temp.ttl", format="turtle")
    # logger.info("Serialized TTL to /database/temp.ttl")
    rd = g.serialize(format="ttl")

    clean = clean_prefixes_with_numbers(rd)

    return clean   # Clean prefixes with numbers before returning
    
   




def run_custom_query(query: str) -> str:
    logger.info(f"Executing custom SPARQL query: {query}")

    forbidden_keywords = ["INSERT", "DELETE", "LOAD", "CLEAR", "DROP", "CREATE", "COPY", "MOVE", "ADD"]
    pattern = r"(?i)^\s*(" + "|".join(forbidden_keywords) + r")\b"
    if re.search(pattern, query):
        logger.warning("Blocked unsafe SPARQL query attempt.")
        raise Exception("Only read-only SPARQL queries are allowed.")

    # if query is a CONSTRUCT, return ttl
    is_construct = bool(re.match(r"(?i)^\s*CONSTRUCT\b", query.strip()))
    headers = {"Accept": "text/turtle" if is_construct else "application/sparql-results+json"} # else is SELECT 
    response = requests.get(
        VIRTUOSO_SPARQL_ENDPOINT,
        params={"query": query, "format": "text/turtle" if is_construct else "application/sparql-results+json"},
        auth=HTTPDigestAuth(VIRTUOSO_USER, VIRTUOSO_PASSWORD),
        headers=headers
    )

    if response.status_code != 200:
        logger.error(f"SPARQL query failed: {response.text}")
        raise Exception(f"Virtuoso error: {response.text}")
    
    if is_construct:
        return response.text  # already in Turtle
    
    # if SELECT, return table (JSON, because TTL is not posible)
    data = response.json()
    # bindings are dictionaries with all the groups of variables (rows)
    results= data.get("results", {}).get("bindings", [])
    # varriables are inside bindings (name, age...)
    variables = data.get("head", {}).get("vars", [])

    g = Graph()

    EX = Namespace("http://example.org/") # ttl predicates are not in the graph, so we need to create a namespace for them
    g.bind("nocolision", EX) 

    for i, row in enumerate(results):
        result_node = BNode ()
        g.add((result_node, RDF.type, EX.Result))
        for var in variables:
            if var in row:
                value = row[var]
                if value["type"] == "uri":
                    obj = URIRef(value["value"])
                elif value["type"] == "literal":
                    obj = Literal(value["value"], lang=value.get("xml:lang"), datatype=value.get("datatype"))
                elif value["type"] == "bnode":
                    obj = BNode(value["value"])
                else:
                    obj = Literal(value["value"])
                g.add((result_node, EX[var], obj))

    return g.serialize(format="turtle")

def delete_all_triples():
    sparql = f"""
    CLEAR GRAPH <{VIRTUOSO_GRAPH_URI}>
    """
    headers = {
        "Content-Type": "application/sparql-update"
    }
    try:
        response = requests.post(
            VIRTUOSO_SPARQL_ENDPOINT,
            data=sparql.encode("utf-8"),
            auth=HTTPDigestAuth(VIRTUOSO_USER, VIRTUOSO_PASSWORD),
            headers=headers
        )
        response.raise_for_status()
        logger.info("All triples deleted from graph.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to clear graph: {e}")
        raise Exception(f"Error clearing graph in Virtuoso: {str(e)}")