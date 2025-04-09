4. Deployment Tutorial
==================================================

4.1. Starting the SEGB
-------------------

.. warning::
This tutorial is compatible with version **0.2.0** of the SEGB. Using a different version may result in unexpected behavior. We are actively working on new versions to enhance functionality and compatibility.


Use the docker-compose file available in this repository. This action requires access to the image used in the docker compose file. The process consists of several steps:

1. Get a personal access token to enable console login in `ghcr.io <https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens>`__.

   .. caution::
      A *classic personal access token* is preferred, given that a *fine-grained access* token may cause problems.

2. In your console, export your token with:

   .. code-block:: shell

      export CR_PAT=<YOUR_TOKEN>

3. Now, login in ghcr.io with:

   .. code-block:: shell

      echo $CR_PAT | docker login ghcr.io -u <YOUR_USER_NAME> --password-stdin

4. Finally, execute docker compose in the directory where your ``docker-compose.yaml`` file is located:

   .. code-block:: shell

      docker compose up -d

5. The URL of the SEGB is ``http://127.0.0.1:5000``


4.2. Sending and Retrieving Data
-----------------------------

To update a new TTL file containing one or several triples, make a POST request to the */log* route. For instance, if you have a Turtle file named "*data.ttl*":

.. important::
   We strongly recommend **NOT to use blank nodes** in any triples you log to the SEGB. They will not break the SEGB, but may generate duplicated blank nodes in the global graph if sent multiple times due to external limitations.

You can do this using the *curl* tool in *bash*:

.. code-block:: shell

   curl -X POST \
        -H "Content-Type: text/turtle" \
        --data-binary "@data.ttl" \
        http://127.0.0.1:5000/log

Alternatively, using *Python*:

.. code-block:: python

   import requests

   url = "http://127.0.0.1:5000/log"
   headers = {"Content-Type": "text/turtle; charset=utf-8"}

   with open("./data.ttl", "rb") as file:
       ttl_data = file.read()

   response = requests.post(url, headers=headers, data=ttl_data)

Similarly, to retrieve the data, make a GET request to the */get_graph* route.

Using *curl* in *bash*:

.. code-block:: shell

   curl -X GET http://127.0.0.1:5000/get_graph -o global_graph.ttl

Or using *Python*:

.. code-block:: python

   import requests

   url = "http://127.0.0.1:5000/get_graph"

   response = requests.get(url)

   with open("output.ttl", "wb") as file:
       file.write(response.content)