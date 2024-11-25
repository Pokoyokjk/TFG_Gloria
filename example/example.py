import requests


URL = "http://127.0.0.1:5000"  
TTL_FILE = "amor-imports.ttl"

def post_file(file_path):

    with open(file_path, 'r', encoding='utf-8') as file:
        data = file.read()
    
    headers = {
        "Content-Type": "text/turtle" 
    }
    
    response = requests.post(URL, headers=headers, data=data)
    
    if response.status_code == 200:
        print("POST realizado con éxito:", response.text)
    else:
        print(f"Error en POST: {response.status_code} - {response.text}")


def get_data():
    
    print("Requesting data")
    
    response = requests.get(URL+"/get_graph")
    
    if response.status_code == 200:
        print(response.text)
    else:
        print(f"Error en GET: {response.status_code} - {response.text}")


# post_file(TTL_FILE)
get_data()