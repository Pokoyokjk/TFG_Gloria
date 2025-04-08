3. API Description
==================

This section describes the available API endpoints provided by the Semantic Ethical Glass Box (SEGB), including their usage, expected inputs, and response formats.

Authentication and Permissions
------------------------------
The SEGB API uses **Bearer Tokens** for authentication and authorization. Each endpoint requires a specific role to access it. The roles are defined as follows:

- **Reader**: Can read the graph and experiment data.
- **Logger**: Can log data to the SEGB.
- **Admin**: Has full access to all endpoints, including deleting the graph and accessing the history.

These must be included as information at token generation time. The SEGB server will validate the token and check the permissions associated with it before processing the request. A token can be defined with several roles and the server will check the permissions for each endpoint. It means that a reader/logger token can be generated.

.. note::

  Tokens must be generated manually by a SEGB admin (who knows the secret) using `token_generator_script.py` and are unique to each user. The tokens are valid for a limited time and should be kept secure. The server will not accept expired or invalid tokens. Additionally, tokens should be refreshed periodically to maintain security.

Tokens must be included in the `Authorization` header as follows:

``Authorization: Bearer <TOKEN>``

If the server is secured, unauthorized access will result in the following status codes:

- `401 Unauthorized`: Invalid token.
- `403 Forbidden`: Token provided but insufficient permissions or no token provided.

3.1. GET /health
----------

**Description:**  
Health check endpoint to verify that the SEGB server is running.

**Request Details:**

- **URL:** `/health`
- **Method:** `GET`

**Response Codes:**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Status Code
     - Description
   * - ``200 OK``
     - The server is running and returns the message: "The SEGB is working".

3.2. POST /log
--------------

**Description:**  
This endpoint receives data in **Turtle (TTL)** format, converts it into **JSON-LD**, and stores it in the database. The TTL payload may include one or multiple RDF triples.

**Request Details:**

- **URL:** `/log`
- **Method:** `POST`
- **Required Headers:**

  - ``Content-Type: text/turtle``
  - ``Authorization: Bearer <LOGGER_TOKEN or ADMIN_TOKEN>``
  
- **Request Body:**
  
  - A valid RDF document in **Turtle (TTL)** format.

**Response Codes:**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Status Code
     - Description
   * - ``201 Created``
     - The data was successfully received and stored.
   * - ``400 Bad Request``
     - The request contained invalid or malformed data.
   * - ``403 Forbidden``
     - Insufficient permissions (e.g., using a Reader Token).

3.3. GET /log
-------------

**Description:**  
Retrieve detailed information about a specific log entry.

**Request Details:**

- **URL:** `/log`
- **Method:** `GET`
- **Required Headers:**  

  - ``Authorization: Bearer <ADMIN_TOKEN>``

- **Query Parameters:**

  - ``log_id``: The ID of the log to retrieve.

**Response Codes:**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Status Code
     - Description
   * - ``200 OK``
     - Returns the log details in JSON format.
   * - ``400 Bad Request``
     - Missing or invalid `log_id` parameter.
   * - ``403 Forbidden``
     - Insufficient permissions (e.g., using a Reader or Logger Token).
   * - ``404 Not Found``
     - The specified log was not found.

3.4. GET /graph
---------------

**Description:**  
Retrieve the entire graph stored in the SEGB in **Turtle (TTL)** format.

**Request Details:**

- **URL:** `/graph`
- **Method:** `GET`
- **Required Headers:**  

  - ``Authorization: Bearer <READER_TOKEN or ADMIN_TOKEN>``

**Response Codes:**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Status Code
     - Description
   * - ``200 OK``
     - Successfully returns the graph in **Turtle (TTL)** format.
   * - ``204 No Content``
     - The graph is empty.
   * - ``403 Forbidden``
     - Insufficient permissions (e.g., using a Logger Token).

3.5. DELETE /graph
------------------

**Description:**  
Delete the entire graph stored in the SEGB.

**Request Details:**

- **URL:** `/graph`
- **Method:** `DELETE`
- **Required Headers:**  

  - ``Authorization: Bearer <ADMIN_TOKEN>``

**Response Codes:**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Status Code
     - Description
   * - ``200 OK``
     - The graph was successfully deleted.
   * - ``204 No Content``
     - The graph was already empty.
   * - ``403 Forbidden``
     - Insufficient permissions (e.g., using a Reader Token).

3.6. GET /experiments
---------------------

**Description:**  
Retrieve a list of all experiments registered or information about a specific experiment and its associated activities (based on parameters).

**Request Details:**

- **URL:** `/experiments`
- **Method:** `GET`
- **Required Headers:**  

  - ``Authorization: Bearer <READER_TOKEN>``

- **Query Parameters:**

  - Retrieving a list of all experiments can be done by providing no parameters.

    - **Important:** If no parameters are provided, the endpoint will return all experiment URIs registered in the SEGB in JSON format.

    - Example without parameters:

      - **Request:**

        .. code-block:: text

           GET /experiments HTTP/1.1
           Host: http://example.com/experiments
           Authorization: Bearer <READER_TOKEN>

      - **Response:**

        .. code-block:: json

           [
             "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1",
             "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp2"
           ]

  - Retrieving information about a specific experiment can be done in two ways:

    - **Note:** Any of the following alternatives can be used to specify the experiment in query parameters.

    - Option 1:

      - ``uri``: Complete URI of the experiment (e.g., `namespace#experiment_id`).  

      - **Important:** If `uri` is provided, the `namespace` and `experiment_id` parameters will be ignored.

      - **Recommendation:** When using Python's `requests` library, use the `params` argument to ensure proper encoding of the `#` character as `%23`. For example:

        .. code-block:: python

         import requests

         url = "http://example.com/experiments"
         params = {"uri": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1"}
         headers = {"Authorization": "Bearer <READER_TOKEN>"}
         response = requests.get(url, params=params, headers=headers)
         print(response.url)  # The URL will automatically encode # as %23

      - **Note for query parameter:** The `uri` parameter contains # character is not allowed in a query parameter, it must be encoded as `%23` if it is included in the URI. This is not required if the `params` argument is used, as in the previous example. For example:

        .. code-block:: text

           /experiments?uri=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns%23exp1

    - Option 2:

      - ``namespace``: The namespace of the experiment.

      - ``experiment_id``: The ID of the experiment.

      - **Recommendation:** When using Python's `requests` library, use the `params` argument to ensure proper encoding of the `#` character as `%23`. For example:

        .. code-block:: python

         import requests

         url = "http://example.com/experiments"
         params = {"namespace": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns", "experiment_id": "exp1"}
         headers = {"Authorization": "Bearer <READER_TOKEN>"}
         response = requests.get(url, params=params, headers=headers)
         print(response.url)  # The URL will automatically encode # as %23

      - The following examples are valid:

      .. code-block:: text

         /experiments?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns&experiment_id=exp1

      .. code-block:: text

         /experiments?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns%23&experiment_id=exp1

**Response Codes:**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Status Code
     - Description
   * - ``200 OK``
     - Returns the experiment details in **Turtle (TTL)** format (if `uri` is provided) or JSON format (if `namespace` and `experiment_id` are provided). If not, returns a list of all experiment URIs registered in the SEGB.
   * - ``204 No Content``
     - No experiments found.
   * - ``403 Forbidden``
     - Insufficient permissions (e.g., using a Logger Token).
   * - ``404 Not Found``
     - The specified experiment was not found.
   * - ``422 Unprocessable Entity``
     - Missing required parameters (e.g., `namespace` or `experiment_id`) or **Invalid URI format**. The URI must be a valid IRI (Internationalized Resource Identifier <prefix>#<resource>) and should not contain spaces or special characters that are not allowed in IRIs. The URI must also be properly encoded if it contains reserved characters.
     
3.8. GET /history
------------------

**Description:**  
Retrieve the history of all logged actions in the SEGB.

**Request Details:**

- **URL:** `/history`
- **Method:** `GET`
- **Required Headers:**  

  - ``Authorization: Bearer <ADMIN_TOKEN>``

**Response Codes:**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Status Code
     - Description
   * - ``200 OK``
     - Returns the history in JSON format.
   * - ``204 No Content``
     - No history found.
   * - ``403 Forbidden``
     - Insufficient permissions (e.g., using a Reader or Logger Token).

3.9. GET /query
---------------

**Description:**  
Execute a SPARQL query on the graph. **(Not implemented yet)**

**Request Details:**

- **URL:** `/query`
- **Method:** `GET`
- **Required Headers:**  

  - ``Authorization: Bearer <ADMIN_TOKEN>``

**Response Codes:**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Status Code
     - Description
   * - ``403 Forbidden``
     - Insufficient permissions (e.g., using a Reader or Logger Token).
   * - ``501 Not Implemented``
     - This endpoint is not yet implemented.