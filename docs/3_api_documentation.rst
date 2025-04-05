3. API Description
==================

This section describes the available API endpoints provided by the Semantic Ethical Glass Box (SEGB), including their usage, expected inputs, and response formats.

Authentication and Permissions
------------------------------
The SEGB API uses **Bearer Tokens** for authentication and authorization. Each endpoint requires a specific token level:

- **Reader Token:** Grants read-only access to the graph and experiments.
- **Logger Token:** Grants permission to log new data into the graph.
- **Admin Token:** Grants full access, including administrative actions like deleting the graph or accessing logs.

Tokens must be included in the `Authorization` header as follows:

```
Authorization: Bearer "<TOKEN>"
```

If the server is secured, unauthorized access will result in the following status codes:

- `401 Unauthorized`: No token provided or invalid token.
- `403 Forbidden`: Token provided but insufficient permissions.

3.1. GET /
----------

**Description:**  
Health check endpoint to verify that the SEGB server is running.

**Request Details:**

- **URL:** `/`
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
  - ``Authorization: Bearer "<LOGGER_TOKEN or ADMIN_TOKEN>"``
- **Request Body:**  
  A valid RDF document in **Turtle (TTL)** format.

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
  - ``Authorization: Bearer "<ADMIN_TOKEN>"``
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
  - ``Authorization: Bearer "<READER_TOKEN or ADMIN_TOKEN>"``

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
  - ``Authorization: Bearer "<ADMIN_TOKEN>"``

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
Retrieve information about a specific experiment and its associated activities.

**Request Details:**

- **URL:** `/experiment`
- **Method:** `GET`
- **Required Headers:**  
  - ``Authorization: Bearer "<READER_TOKEN>"``
- **Query Parameters:**
  - ``uri``: Complete URI of the experiment (e.g., `namespace#experiment_id`).  
    **Note:** If `uri` is provided, the `namespace` and `experiment_id` parameters will be ignored.
  - OR
  - ``namespace``: The namespace of the experiment.
  - ``experiment_id``: The ID of the experiment.
  - OR
  - no parameters: Returns all experiments in JSON format.

**Response Codes:**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Status Code
     - Description
   * - ``200 OK``
     - Returns the experiment details in **Turtle (TTL)** format.
   * - ``204 No Content``
     - No experiments found.
   * - ``403 Forbidden``
     - Insufficient permissions (e.g., using a Logger Token).
   * - ``404 Not Found``
     - The specified experiment was not found.
   * - ``422 Unprocessable Entity``
     - Missing required parameters (e.g., `namespace` or `experiment_id`).

3.8. GET /history
------------------

**Description:**  
Retrieve the history of all logged actions in the SEGB.

**Request Details:**

- **URL:** `/history`
- **Method:** `GET`
- **Required Headers:**  
  - ``Authorization: Bearer "<ADMIN_TOKEN>"``

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
  - ``Authorization: Bearer "<ADMIN_TOKEN>"``

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