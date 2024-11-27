import requests

def log_ttl(server: str, input_file_path: str):
    '''
    Example function to log a TTL file to the SEBB.
    '''

    with open(input_file_path, mode="r", encoding='utf-8') as file:
        data = file.read()
        print("Fichero leído con éxito de:", input_file_path)
    
    headers = {
        "Content-Type": "text/turtle" 
    }
    
    response = requests.post(server+"/log", headers=headers, data=data)
    
    if response.status_code == 200:
        print("POST realizado con éxito")
    else:
        print(f"Error en POST: {response.status_code} - {response.text}")


def get_graph(server: str, output_file_path: str):
    '''
    Example function to download the complete graph stored in the SEBB
    '''
    print("Requesting graph...")
    
    response = requests.get(server+"/get_graph")
    
    if response.status_code == 200:
        # print(response.text)
        with open(output_file_path, mode="w", encoding='utf-8') as file:
            file.write(response.text)
        print("Fichero descargado con éxito en:", output_file_path)
    else:
        print(f"Error en GET: {response.status_code} - {response.text}")


if __name__ == '__main__':
    # SEBB URI
    server = "http://127.0.0.1:5000"
    # Log full ontologies to SEBB
    models = [
        "example-data/amor.ttl",
        "example-data/mft.ttl",
        "example-data/bhv.ttl",
        "example-data/amor-mft.ttl",
        "example-data/amor-bhv.ttl"
    ]
    for model in models:
        log_ttl(server, model)
    
    # Log a new ontology plenty of individuals
    input_ttl_file = "example-data/amor-examples.ttl"
    log_ttl(server, input_ttl_file)
    
    
    # TODO fix the duplication of blank nodes (try with rdflib.ConjuctiveGraph)
    '''
    v0.1 works if the duplicated triples are related with BlankNodes.
    If there are some blank nodes duplicated, there will appear duplicated 
    in the downloaded graph.
    
    '''
    # Log a few triples (no ontology), some of them are duplicated.
    input_ttl_file = "example-data/new-triples.ttl"
    log_ttl(server, input_ttl_file)
    
    # Download the complete graph stored in the SEBB
    output_ttl_file = "graph.ttl"
    get_graph(server, output_ttl_file)