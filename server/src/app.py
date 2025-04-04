from flask import Flask, request, Response
import semantic_utils as semantic_utils
import experiments_utils as experiments_utils
from model import connect_to_db, save_json_ld, get_raw_graph_from_db, log_ttl_content, clear_graph, get_logs_list, get_log_info
from flask import Response, jsonify

import logging
import os

# Set up logging
logging_level = os.getenv("LOGGING_LEVEL", "INFO").upper()
log_file = os.getenv("SERVER_LOG_FILE", "segb_server.log")
# Ensure the logs directory exists
os.makedirs('/logs', exist_ok=True)
file_handler = logging.FileHandler(
    filename=f'/logs/{log_file}',
    mode='a',
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s -> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger = logging.getLogger("segb_server")
logger.setLevel(getattr(logging, logging_level, logging.INFO))
logger.addHandler(file_handler)

logger.info("Starting SEGB server...")
logger.info("Logging level set to %s", logging_level)
# Initialize Flask app
app = Flask(__name__)

logger.info("Connecting to the database...")
connect_to_db()
logger.info("Database connection established.")

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
        log_ttl_content(recieved_data,origin_ip)
        
    return Response(status=status)

@app.route('/log', methods=['GET'])
def get_log():
    if request.is_json:
        logger.debug(f"Request body: {request.get_json()}")
        args = request.get_json()
    else:
        logger.debug(f"Request arguments: {request.args}")
        args = request.args.to_dict()
    log_id = args.get('log_id')
    logger.info(f"Received log_id: {log_id}")
    if not log_id:
        message = jsonify("Missing log_id parameter")
        status=400
    else:
        status = 200
        message = None
        
        try:
            log_data = get_log_info(log_id)
            if not log_data:
                message = jsonify("Log Info not found")
                status=404
            else:
                message = jsonify(log_data)
                status=200
        except Exception as e:
            logger.error(f"Error retrieving log: {e}")
            message = jsonify("Error retrieving log")
            status = 500
            log_data = None
        
    
    return message, status

@app.route('/query', methods=['GET'])
def get_query():
    return Response("Not implemented yet", status=501)


    # if request.is_json:
    #     logger.debug(f"Request body: {request.get_json()}")
    #     args = request.get_json()
    # else:
    #     logger.debug(f"Request arguments: {request.args}")
    #     args = request.args.to_dict()
    # sparql_query = args.get('query')
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
    
    
@app.route('/graph', methods=['GET'])
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

@app.route('/graph', methods=['DELETE'])
def delete_graph():
    status = 200
    origin_ip = semantic_utils.get_origin_ip(request)
    deleted = clear_graph(origin_ip)
    if not deleted:
        status = 500
    return Response(status=status)

@app.route('/experiment', methods=['GET'])
def get_experiment():
    logger.info("Received request for experiment")
    if request.is_json:
        logger.debug(f"Request body: {request.get_json()}")
        args = request.get_json()
    else:
        logger.debug(f"Request arguments: {request.args}")
        args = request.args.to_dict()
    uri = args.get('uri')
    if uri:
        logger.info(f"Received URI: {uri}")
        # If the URI is provided, we expect it to be a complete URI
        # Preferred option: form of namespace#experiment_id
        # If the URI is provided, namespace and experiment_id are ignored
        namespace, experiment_id = uri.rsplit("#", 1) 
        namespace += "#"
    else:
        # If the URI is not provided, we expect the namespace and experiment_id as separate parameters
        namespace = args.get('namespace')
        experiment_id = args.get('experiment_id')
        if namespace and not namespace.endswith("#"):
            namespace += "#"
        logger.info(f"Received namespace: {namespace}, experiment_id: {experiment_id}")
        if not namespace or not experiment_id:
            logger.info("Missing parameters: namespace or experiment_id")
            return Response("Missing parameters. Provide a complete URI or the tuple: namespace and experiment_id as separate parameters.", status=422)
    try:
        json_ld_data = get_raw_graph_from_db() # Test if this is the correct way to get the data
        graph = semantic_utils.get_graph_from_json(json_ld_data)
        result_graph = experiments_utils.get_experiment_with_activities(graph, namespace, experiment_id)
        if len(result_graph) == 0:
            logger.info(f"Experiment not found: {namespace}#{experiment_id}")
            return Response(f"Experiment not found: {namespace}#{experiment_id}", status=404)
        return result_graph.serialize(format="turtle")
    except Exception as e:
        logger.error(f"Error retrieving experiment: {e}")
        return Response(f"Error retrieving experiment: {str(e)}", status=500)
    
    
@app.route('/experiments', methods=['GET'])
def get_experiments():
    '''
    Get the list of experiments from the graph.
    The response is a CSV file with the experiment URIs.
    The CSV file is generated using a SPARQL query.
    '''
    try:
        json_ld_data = get_raw_graph_from_db()
        graph = semantic_utils.get_graph_from_json(json_ld_data)
        logger.debug(f"Graph retrieved successfully. Returning the experiment list as CSV.")
        return experiments_utils.get_experiment_list(graph)
    except Exception as e:
        logger.debug(f"Error retrieving experiment list: {e}")
        return Response(f"Error retrieving experiment list: {str(e)}", status=500)

@app.route('/history', methods=['GET'])
def get_history():
    status = 200
    try:
        history = get_logs_list()
        if not history:
            history = []
            status = 204
        return jsonify(history), status
    except Exception as e:
        return jsonify({"Internal Server Error"}), status
