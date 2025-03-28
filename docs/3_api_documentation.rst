3. API Description
==================

This section describes the available API endpoints provided by the Semantic Ethical Glass Box (SEGB), including their usage, expected inputs, and response formats.

3.1. POST /log
-----------

**Description:**  
This endpoint receives data in **Turtle (TTL)** format, converts it into **JSON-LD**, and stores it in the database. The TTL payload may include one or multiple RDF triples.

**Request Details:**

- **URL:** `/log`
- **Method:** `POST`
- **Required Headers:**  
  ``Content-Type: text/turtle``
- **Request Body:**  
  A valid RDF document in **Turtle (TTL)** format.

**Response Codes:**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Status Code
     - Description
   * - ``200 OK``
     - The data was successfully received and stored.
   * - ``400 Bad Request``
     - The request contained invalid or malformed data.

3.2. GET /get_graph
----------------

**Description:**  
This endpoint retrieves the stored data (originally submitted in TTL, stored in JSON-LD), processes it, and returns the result in **Turtle (TTL)** format.

**Request Details:**

- **URL:** `/get_graph`
- **Method:** `GET`

**Response Codes:**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Status Code
     - Description
   * - ``200 OK``
     - Successfully returns the stored data in **Turtle (TTL)** format.
   * - ``404 Not Found``
     - No data is currently available in the database.

3.3. GET /get_experiment
-------------------------

**Description:**

  This endpoint retrieves information about an experiment along with its associated activities from the stored data (the SEGB global graph).

**Request Details:**

- **URL:** ``/get_experiment``
- **Method:** ``GET``
- **Parameters:**
  
  - **Option 1 (complete):**
    
    - ``uri``: Complete URI of the experiment in the format ``namespace#experiment_id``.
  
  - **Option 2 (separate):**
    
    - ``namespace``: The namespace part of the URI.
    - ``experiment_id``: The identifier of the experiment.

**Response Codes:**


.. list-table::
  :widths: 20 80
  :header-rows: 1

  * - Status Code
    - Description
  * - ``200 OK``
    - Returns the representation of the experiment and its activities in **Turtle (TTL)** format.
  * - ``400 Bad Request``
    - Missing required parameters. Neither a complete ``uri`` nor both ``namespace`` and ``experiment_id`` were provided.
  * - ``404 Not Found``
    - The specified experiment (``namespace`` and ``experiment_id`` combination) was not found.
  * - ``500 Internal Server Error``
    - An internal error occurred while retrieving or processing the data.
