5. Generic Usage Tutorial
=================================

1. Overview
-----------

The Semantic Ethical Glass Box (SEGB) is global *log* storage, which
keeps a semantic registry (graph) of logs generated within different
systems. Let’s see how to get the most out of it.

[!note] This tutorial assumes that the SEGB has already been properly
deployed following the deployment tutorial (see `Deployment
Tutorial <https://amor-segb.readthedocs.io/en/latest/4_deployment_tutorial.html>`__

[!warning] We will not use authentication in this tutorial to make it
easy to understand.

2. Auxiliary functions
~~~~~~~~~~~~~~~~~~~~~~

We first define some aux functions to make the tutorial easy.

Functions for interacting with the SEGB’s API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Specifically, one function for every endpoint the SEGB’s API defines
(see `Basic
Tutorial <https://amor-segb.readthedocs.io/en/stable/3_api_documentation.html>`__
for detailed info):

.. code:: ipython3

    import requests
    import json

.. code:: ipython3

    def get_health(server: str = "http://localhost:5000"):
        url = f"{server}/health"
        response = requests.get(url)
        if response.status_code == 200:
            print(response.text)
        else:
            print(f"Error fetching health: {response.status_code} - {response.text}")

.. code:: ipython3

    def post_log_ttl(ttl: str, server: str = "http://localhost:5000", token: str = "fake_token"):
        headers = {
            "Content-Type": "text/turtle",
            "Authorization": f"Bearer {token}"
        }
        url = f"{server}/log"
        response = requests.post(url, headers=headers, data=ttl)
        if response.status_code == 201:
            print("POST request completed successfully")
        elif response.status_code in (400, 403):
            print(f"Error in POST: {response.status_code} - {response.text}")
        else:
            print(f"Unexpected status code: {response.status_code} - {response.text}")


.. code:: ipython3

    def get_log_entry(log_id: str, server: str = "http://localhost:5000", token: str = "fake_token"):
        url = f"{server}/log"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {"log_id": log_id}
        response = requests.get(url, headers=headers, params=params)
    
        if response.status_code == 200:
            data = response.json()
            print("Log entry retrieved successfully:\n")
    
            print("Log metadata:")
            print(json.dumps(data["log"], indent=2))
    
            if data["log"]["action_type"] == "insertion":
                print("\nTTL Content:\n")
                print(data["action"]["ttl_content"].strip())
            elif data["log"]["action_type"] == "deletion":
                print("\nTTL hash at the moment of the deletion:\n")
                print(data["action"]["deleted_graph_hash"].strip())
        elif response.status_code in (400, 403, 404):
            print(f"Error retrieving log: {response.status_code} - {response.text}")
        else:
            print(f"Unexpected status code: {response.status_code} - {response.text}")


.. code:: ipython3

    def get_graph(server: str = "http://localhost:5000", token: str = "fake_token"):
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{server}/graph"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("Graph retrieved successfully:")
            print(response.text)
        elif response.status_code == 204:
            print("The graph is empty.")
        elif response.status_code == 403:
            print(f"Error retrieving graph: {response.status_code} - {response.text}")
        else:
            print(f"Unexpected status code: {response.status_code} - {response.text}")


.. code:: ipython3

    def delete_graph(server: str = "http://localhost:5000", token: str = "fake_token"):
        url = f"{server}/graph"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            print("Graph deleted successfully.")
        elif response.status_code == 204:
            print("The graph was already empty.")
        elif response.status_code == 403:
            print(f"Error deleting graph: {response.status_code} - {response.text}")
        else:
            print(f"Unexpected status code: {response.status_code} - {response.text}")


.. code:: ipython3

    def get_history(server: str = "http://localhost:5000", token: str = "fake_token"):
        url = f"{server}/history"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
    
        if response.status_code == 200:
            print("History retrieved successfully:")
            print(json.dumps(response.json(), indent=2))
        elif response.status_code == 204:
            print("No history found.")
        elif response.status_code == 403:
            print(f"Error retrieving history: {response.status_code} - {response.text}")
        else:
            print(f"Unexpected status code: {response.status_code} - {response.text}")


Functions for post-processing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: ipython3

    from rdflib import Graph
    
    def merge_ttls(ttl_1: str, ttl_2: str):
    
        g1 = Graph()
        g2 = Graph()
        
        g1.parse(data=ttl_1, format="turtle")
        g2.parse(data=ttl_2, format="turtle")
        
        g1 += g2
        
        merged_ttl = g1.serialize(format="json-ld", encoding="utf-8").decode("utf-8")
        
        print(f"\nThe final graph is:\n")
        print(merged_ttl)
    
        return merged_ttl

3. SEGB’s usage tutorial
~~~~~~~~~~~~~~~~~~~~~~~~

Let’s suppose we have the role of a data scientist who has to publish
two TTL into the SEGB:

.. code:: ipython3

    ttl_1 = """
    @prefix ex: <http://example.org/> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix schema: <http://schema.org/> .
    
    ex:dataScientist1 a prov:Person, foaf:Person, schema:Person ;
        foaf:firstName "Pedro"@es ;
        foaf:homepage <http://example.org/pedro> ;
        schema:affiliation ex:upm .
    """
    
    ttl_2 = """
    @prefix ex: <http://example.org/> .
    @prefix schema: <http://schema.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    
    ex:upm a schema:Organization, foaf:Organization, prov:Organization ;
        schema:url <https://www.upm.es> ;
        schema:name "Universidad Politécnica de Madrid"@es ;
        schema:name "Technical University of Madrid"@en .
    """


Check if the SEGB is working
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We first check if the SEGB is working properly by requesting **HTTP GET
/graph**.

.. code:: ipython3

    get_health()


.. parsed-literal::

    The SEGB is working


As the SEGB is working, we save the first TTL, *ttl_1*, by requesting
**HTTP POST /log**

.. code:: ipython3

    post_log_ttl(ttl_1)


.. parsed-literal::

    POST request completed successfully


Now we can check the SEGB graph and see the TTL info has been included

.. code:: ipython3

    get_graph()


.. parsed-literal::

    Graph retrieved successfully:
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix schema1: <http://schema.org/> .
    
    ex:dataScientist1 a schema1:Person,
            prov:Person,
            foaf:Person ;
        schema1:affiliation ex:upm ;
        foaf:firstName "Pedro"@es ;
        foaf:homepage ex:pedro .
    
    


We repeat the process for the second TTL and observe how the graph is
updated

.. code:: ipython3

    post_log_ttl(ttl_2)


.. parsed-literal::

    POST request completed successfully


.. code:: ipython3

    get_graph()


.. parsed-literal::

    Graph retrieved successfully:
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix schema1: <http://schema.org/> .
    
    ex:dataScientist1 a schema1:Person,
            prov:Person,
            foaf:Person ;
        schema1:affiliation ex:upm ;
        foaf:firstName "Pedro"@es ;
        foaf:homepage ex:pedro .
    
    ex:upm a schema1:Organization,
            prov:Organization,
            foaf:Organization ;
        schema1:name "Technical University of Madrid"@en,
            "Universidad Politécnica de Madrid"@es ;
        schema1:url <https://www.upm.es> .
    
    


Now, let’s suppose the information we have updated is no longer
necessary as we are going to register events from a new scenario. In
that case we can delete the graph:

.. code:: ipython3

    delete_graph()


.. parsed-literal::

    Graph deleted successfully.


And now the graph must be empty

.. code:: ipython3

    get_graph()


.. parsed-literal::

    The graph is empty.


Now, we update the new info:

.. code:: ipython3

    ttl_3 = """
    @prefix ex: <http://example.org/> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix schema: <http://schema.org/> .
    
    ex:dataScientist1 a prov:Person, foaf:Person, schema:Person ;
        foaf:firstName "Lucía"@es ;
        foaf:homepage <http://example.org/lucia> ;
        schema:affiliation ex:us .
    """
    
    ttl_4 = """
    @prefix ex: <http://example.org/> .
    @prefix schema: <http://schema.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    
    ex:us a schema:Organization, foaf:Organization, prov:Organization ;
        schema:url <https://www.us.es> ;
        schema:name "Universidad de Sevilla"@es ;
        schema:name "University of Seville"@en .
    """


.. code:: ipython3

    post_log_ttl(ttl_3)


.. parsed-literal::

    POST request completed successfully


.. code:: ipython3

    post_log_ttl(ttl_4)


.. parsed-literal::

    POST request completed successfully


And the new graph is:

.. code:: ipython3

    get_graph()


.. parsed-literal::

    Graph retrieved successfully:
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix schema1: <http://schema.org/> .
    
    ex:dataScientist1 a schema1:Person,
            prov:Person,
            foaf:Person ;
        schema1:affiliation ex:us ;
        foaf:firstName "Lucía"@es ;
        foaf:homepage ex:lucia .
    
    ex:us a schema1:Organization,
            prov:Organization,
            foaf:Organization ;
        schema1:name "University of Seville"@en,
            "Universidad de Sevilla"@es ;
        schema1:url <https://www.us.es> .
    
    


However, the SEGB’s principles indicates that all the information
occured within any specific scenario must be always accessed in order to
audit it. Thus, altough the info has been deleted from the main graph,
we can still retreive the history of every insertion/deletion of data:

.. code:: ipython3

    get_history()


.. parsed-literal::

    History retrieved successfully:
    [
      {
        "_id": "67f5148436cfc7bb52af9cdd",
        "uploaded_at": "2025-04-08T12:20:20.764000",
        "origin_ip": "172.18.0.1",
        "action_type": "insertion",
        "action": "67f5148436cfc7bb52af9cde"
      },
      {
        "_id": "67f5148436cfc7bb52af9cdf",
        "uploaded_at": "2025-04-08T12:20:20.794000",
        "origin_ip": "172.18.0.1",
        "action_type": "insertion",
        "action": "67f5148436cfc7bb52af9ce0"
      },
      {
        "_id": "67f5148436cfc7bb52af9ce1",
        "uploaded_at": "2025-04-08T12:20:20.806000",
        "origin_ip": "172.18.0.1",
        "action_type": "deletion",
        "action": "67f5148436cfc7bb52af9ce2"
      },
      {
        "_id": "67f5148436cfc7bb52af9ce3",
        "uploaded_at": "2025-04-08T12:20:20.827000",
        "origin_ip": "172.18.0.1",
        "action_type": "insertion",
        "action": "67f5148436cfc7bb52af9ce4"
      },
      {
        "_id": "67f5148436cfc7bb52af9ce5",
        "uploaded_at": "2025-04-08T12:20:20.835000",
        "origin_ip": "172.18.0.1",
        "action_type": "insertion",
        "action": "67f5148436cfc7bb52af9ce6"
      }
    ]


We can observe we have, as expected, **two insertions**, **one
deletion** and other **two insertions**

We can retrieve the information from the first and second insertion by
using its id and retrieving the TTL data that was updated at some point

.. code:: ipython3

    get_log_entry("67f5148436cfc7bb52af9cdd")


.. parsed-literal::

    Log entry retrieved successfully:
    
    Log metadata:
    {
      "_id": "67f5148436cfc7bb52af9cdd",
      "uploaded_at": "2025-04-08T12:20:20.764000",
      "origin_ip": "172.18.0.1",
      "action_type": "insertion",
      "action": "67f5148436cfc7bb52af9cde"
    }
    
    TTL Content:
    
    @prefix ex: <http://example.org/> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix schema: <http://schema.org/> .
    
    ex:dataScientist1 a prov:Person, foaf:Person, schema:Person ;
        foaf:firstName "Pedro"@es ;
        foaf:homepage <http://example.org/pedro> ;
        schema:affiliation ex:upm .


.. code:: ipython3

    get_log_entry("67f5148436cfc7bb52af9cdf")


.. parsed-literal::

    Log entry retrieved successfully:
    
    Log metadata:
    {
      "_id": "67f5148436cfc7bb52af9cdf",
      "uploaded_at": "2025-04-08T12:20:20.794000",
      "origin_ip": "172.18.0.1",
      "action_type": "insertion",
      "action": "67f5148436cfc7bb52af9ce0"
    }
    
    TTL Content:
    
    @prefix ex: <http://example.org/> .
    @prefix schema: <http://schema.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    
    ex:upm a schema:Organization, foaf:Organization, prov:Organization ;
        schema:url <https://www.upm.es> ;
        schema:name "Universidad Politécnica de Madrid"@es ;
        schema:name "Technical University of Madrid"@en .


We can now merge the TTL to rebuild the old graph

The same way, we can retrieve the info of the deletion log

.. code:: ipython3

    get_log_entry("67f5148436cfc7bb52af9ce1")


.. parsed-literal::

    Log entry retrieved successfully:
    
    Log metadata:
    {
      "_id": "67f5148436cfc7bb52af9ce1",
      "uploaded_at": "2025-04-08T12:20:20.806000",
      "origin_ip": "172.18.0.1",
      "action_type": "deletion",
      "action": "67f5148436cfc7bb52af9ce2"
    }
    
    TTL at the moment of the deletion:

    @prefix ex: <http://example.org/> .
    @prefix schema: <http://schema.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    
    ex:dataScientist1 a prov:Person, foaf:Person, schema:Person ;
        foaf:firstName "Pedro"@es ;
        foaf:homepage <http://example.org/pedro> ;
        schema:affiliation ex:upm .

    ex:upm a schema:Organization, foaf:Organization, prov:Organization ;
        schema:url <https://www.upm.es> ;
        schema:name "Universidad Politécnica de Madrid"@es ;
        schema:name "Technical University of Madrid"@en .



