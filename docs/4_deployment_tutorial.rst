4. Deployment Tutorial
==================================================

4.1. Starting the SEGB locally
-------------------

#. Use the docker-compose file available in the `SEGB repository <https://github.com/gsi-upm/segb>`_, which can be found at the following link: `docker-compose.yaml <https://github.com/gsi-upm/segb/blob/main/docker-compose.yaml>`_.

#. You can configure the SEGB to use a secret key for token-based authentication by setting the `SECRET_KEY` environment variable.

   This variable can be defined in a `.env` file located in the same directory as the `docker-compose.yaml` file. For example:

   .. code-block:: ini

      # .env file
      SECRET_KEY=your_secret_key_here

   If a `SECRET_KEY` is defined, tokens must be generated using the `SEGB Token Generator Script <https://github.com/gsi-upm/segb/blob/main/server/token_generator_script.py>`_. These tokens are unique to each user and must be included in the `Authorization` header as a Bearer token when making requests to the SEGB.

   If the `SECRET_KEY` is left blank (or not defined), the SEGB will operate without security. In this case, you must still include an `Authorization` header with a Bearer token in your requests, but any string used as a token will be accepted.

   For example, with a token-based setup:

   .. code-block:: shell

      curl -X POST \
         -H "Content-Type: text/turtle" \
         -H "Authorization: Bearer <your_generated_token>" \
         --data-binary "@data.ttl" \
         http://127.0.0.1:5000/log

   Or without a secret key:

   .. code-block:: shell

      curl -X POST \
         -H "Content-Type: text/turtle" \
         -H "Authorization: Bearer any_string_here" \
         --data-binary "@data.ttl" \
         http://127.0.0.1:5000/log

   .. note::

   Tokens must be generated manually by a SEGB admin (who knows the secret) using `SEGB Token Generator Script <https://github.com/gsi-upm/segb/blob/main/server/token_generator_script.py>`_ and are unique to each user. The tokens are valid for a limited time and should be kept secure. The server will not accept expired or invalid tokens. Additionally, tokens should be refreshed periodically to maintain security.

#. Finally, execute docker compose in the directory where your ``docker-compose.yaml`` file is located:

   .. code-block:: shell

      docker compose up -d

#. The URL of the SEGB is ready at: ``http://127.0.0.1:5000``

4.2. Sending and Retrieving Data from SEGB GUI
-----------------------------

As an alternative to using the command line or any language, you can also use the SEGB GUI to send and retrieve data. The GUI provides a user-friendly interface for interacting with the SEGB.

A Swagger UI is available, which allows you to explore the API endpoints and their functionalities.
To access the Swagger UI, open your web browser and navigate to: `http://127.0.0.1:5000/docs <http://127.0.0.1:5000/docs>`_ (or root redirects to this page).
You can use the Swagger UI to send and retrieve data from the SEGB. The interface provides a clear and intuitive way to interact with the API endpoints.


4.3. Sending and Retrieving Data from code
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

Similarly, to retrieve the data, make a GET request to the */graph* route.

Using *curl* in *bash*:

.. code-block:: shell

   curl -X GET http://127.0.0.1:5000/graph -o global_graph.ttl

Or using *Python*:

.. code-block:: python

   import requests

   url = "http://127.0.0.1:5000/graph"

   response = requests.get(url)

   with open("output.ttl", "wb") as file:
       file.write(response.content)

4.4. Personalized logging
-----------------------------

The SEGB allows for personalized logging configurations using a `log_conf.yaml<https://github.com/gsi-upm/segb/blob/main/log_conf.yaml>`_ file.
This file should follow the structure defined by PyYAML.
You can find an example of the `log_conf.yaml<https://github.com/gsi-upm/segb/blob/main/log_conf.yaml>`_ file in the root of the GitHub repository (`log_conf.yaml<https://github.com/gsi-upm/segb/blob/main/log_conf.yaml>`_) and in the `test folder<https://github.com/gsi-upm/segb/blob/main/test/test_log_conf.yaml>`_.
For more details, visit the repository: `<https://github.com/gsi-upm/segb>`_.
