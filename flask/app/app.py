from flask import Flask, request, Response


import aux
from model import connect_to_db, save_json_ld

app = Flask(__name__)

connect_to_db()

@app.route('/log',methods=['POST'])
def save_log():

    status = 200
    recieved_data = request.data 
    json_ld_data = None   
    
    if not recieved_data:
        status = 400
      
    try:
        ttl_graph_data = aux.process_turtle_data(recieved_data)
        json_ld_data = aux.convert_turtle_to_json_ld(ttl_graph_data= ttl_graph_data)
    except Exception as e:
        status = 400

    if status == 200: save_json_ld(json_ld_data=json_ld_data)
  
    return Response(status=200)

  
    

@app.route('/query', methods=['GET'])
def get_query():
    # TODO: function that executes graph queries over mongodb/kgtk
    return "<h1>Hello</h1>"
    pass
    
@app.route('/get_graph', methods=['GET'])
def get_html_graph():
    # TODO: function that return a graph in HTML format
    pass
