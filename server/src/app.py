from flask import Flask, request, Response
import semantic_utils as semantic_utils
import experiments_utils as experiments_utils
from model import connect_to_db, save_json_ld, get_raw_graph_from_db, save_ttl_content


import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

connect_to_db()

@app.route('/', methods=['GET'])
def default_route():
    return "The SEGB is working"

@app.route('/log',methods=['POST'])
def save_log():
    status = 200
    recieved_data = request.data 
    origin_ip = semantic_utils.get_origin_ip(request)
    json_ld_data = None
    
    if not recieved_data:
        status = 400
    
    try:
        graph = semantic_utils.get_graph_from_ttl(recieved_data)
        json_ld_data = semantic_utils.convert_graph_to_json_ld(graph=graph)
    except Exception as e:
        status = 400
    
    if status == 200:
        save_json_ld(json_ld_data=json_ld_data)
        save_ttl_content(recieved_data,origin_ip)
        
    return Response(status=status)

  
@app.route('/query', methods=['GET'])
def get_query():
    return Response("Not implemented yet", status=501)

    # sparql_query = request.args.get('query')
    # if not sparql_query:
    #     return Response("Missing query parameter", status=400)
    
    # try:
    #     # Retrieve the graph data as in get_graph
    #     json_ld_data = get_raw_graph_from_db()
    #     graph = semantic_utils.get_graph_from_json(json_ld_data)
        
    #     # Execute the SPARQL query using the semantic_utils module on the retrieved graph
    #     query_result = semantic_utils.execute_sparql_query(graph, sparql_query)
    #     # TODO: not so simple to parse "any" query result, but we could return the raw result
    #     result = query_result.serialize()
    #     return Response(result, status=200)
    # except Exception as e:
    #     return Response(f"Error executing SPARQL query: {str(e)}", status=500)
    
    
@app.route('/get_graph', methods=['GET'])
def get_graph():
    status = 200
    json_ld_data = None
    turtle_data = None
    try:
        json_ld_data = get_raw_graph_from_db()
    except:
        status = 500
    if not json_ld_data:
        status = 204
    else:    
        graph = semantic_utils.get_graph_from_json(json_ld_data)
        turtle_data = semantic_utils.convert_graph_to_turtle(graph) 
    return Response(turtle_data, status=status)

@app.route('/get_experiment', methods=['GET'])
def get_experiment():
    uri = request.args.get('uri')
    if uri:
        # If the URI is provided, we expect it to be a complete URI
        # Preferred option: form of namespace#experiment_id
        # If the URI is provided, namespace and experiment_id are ignored
        namespace, experiment_id = uri.rsplit("#", 1) 
        namespace += "#"
    else:
        # If the URI is not provided, we expect the namespace and experiment_id as separate parameters
        namespace = request.args.get('namespace')
        experiment_id = request.args.get('experiment_id')
        if not namespace or not experiment_id:
            return Response("Missing parameters. Provide a complete URI or the tuple: namespace and experiment_id as separate parameters.", status=400)
    try:
        json_ld_data = get_raw_graph_from_db() # Test if this is the correct way to get the data
        graph = semantic_utils.get_graph_from_json(json_ld_data)
        result_graph = experiments_utils.get_experiment_with_activities(graph, namespace, experiment_id)
        if len(result_graph) == 0:
            return Response(f"Experiment not found: {namespace}#{experiment_id}", status=404)
        return result_graph.serialize(format="turtle")
    except Exception as e:
        return Response(f"Error retrieving experiment: {str(e)}", status=500)
    
@app.route('/get_experiment_list', methods=['GET'])
def get_experiment_list():
    experiment_list = None
    try:
        json_ld_data = get_raw_graph_from_db()
        graph = semantic_utils.get_graph_from_json(json_ld_data)
        experiment_list = experiments_utils.get_experiment_list()
    except Exception as e:
        return Response(f"Error retrieving experiment: {str(e)}", status=500)
    result = experiment_list.serialize(format="turtle")
    return result    
        

# @app.route('/clear_graph', methods=['GET'])

# @app.route('/history', methods=['GET'])

# @app.route('/get_log', methods=['GET'])