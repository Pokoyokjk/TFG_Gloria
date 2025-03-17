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

