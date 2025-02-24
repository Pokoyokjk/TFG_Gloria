"""
Module for interacting with the Semantic Ethical Black Box (SEGB).

This module provides functions to:
    - Log Turtle (TTL) data to the SEGB via a POST request.
    - Download the complete graph stored in the SEGB via a GET request.

The SEGB exposes two endpoints:
    - /log: To store data in Turtle format (which is internally converted to JSON-LD).
    - /get_graph: To retrieve the complete graph in Turtle format.
"""

import requests

def log_ttl(server: str, input_file_path: str):
    
    """Log a TTL file to the SEGB.

    Reads a Turtle (TTL) file from the specified path and sends its content
    to the SEGB's `/log` endpoint via a POST request.

    Args:
        server (str): The base URL of the SEGB server (e.g., "http://127.0.0.1:5000").
        input_file_path (str): The path to the TTL file to be logged.
    
    Example:
        >>> log_ttl("http://127.0.0.1:5000", "/path/to/file/data.ttl")
    """
    
    with open(input_file_path, mode="r", encoding="utf-8") as file:
        data = file.read()
        print("File successfully read from:", input_file_path)
    
    headers = {
        "Content-Type": "text/turtle"
    }
    
    response = requests.post(f"{server}/log", headers=headers, data=data)
    
    if response.status_code == 200:
        print("POST request completed successfully")
    else:
        print(f"Error in POST: {response.status_code} - {response.text}")


def get_graph(server: str, output_file_path: str):
    """Download the complete graph stored in the SEGB.

    Sends a GET request to the SEGB's `/get_graph` endpoint to retrieve the
    complete graph in Turtle format and saves it to the specified output file.

    Args:
        server (str): The base URL of the SEGB server (e.g., "http://127.0.0.1:5000").
        output_file_path (str): The path where the downloaded graph will be saved.
    
    Example:
        >>> get_graph("http://127.0.0.1:5000", "/path/to/output/graph.ttl")
    """
    print("Requesting graph...")
    
    response = requests.get(f"{server}/get_graph")
    
    if response.status_code == 200:
        with open(output_file_path, mode="w", encoding="utf-8") as file:
            file.write(response.text)
        print("File successfully downloaded to:", output_file_path)
    else:
        print(f"Error in GET: {response.status_code} - {response.text}")


if __name__ == "__main__":
    
    # SEGB server URL
    server = "http://127.0.0.1:5000"
    
    # Log complete ontologies to the SEGB
    models = [
        "example-data/amor.ttl",
        "example-data/mft.ttl",
        "example-data/bhv.ttl",
        "example-data/amor-mft.ttl",
        "example-data/amor-bhv.ttl"
    ]
    for model in models:
        log_ttl(server, model)
    
    # Log a new ontology with plenty of individuals
    input_ttl_file = "example-data/amor-examples.ttl"
    log_ttl(server, input_ttl_file)
    
    # TODO: Fix the duplication of blank nodes (try using rdflib.ConjunctiveGraph)
    # Note: In version 0.1, if there are duplicated triples related to blank nodes,
    # they will appear duplicated in the downloaded graph.
    
    # Log a few triples (not a full ontology) simulating some TTL-parsed logs, some of which are duplicated.
    input_ttl_file = "example-data/new-triples.ttl"
    log_ttl(server, input_ttl_file)
    
    # Download the complete graph stored in the SEGB
    output_ttl_file = "graph.ttl"
    get_graph(server, output_ttl_file)