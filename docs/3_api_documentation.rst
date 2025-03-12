3. API Description
===================

🔹 ``POST /log``
----------------
**Description:**  
Stores the received **Turtle (TTL)** data, converts it to **JSON-LD**, and saves it in the database. The TTL data could contain one or several triples.

✅ Request
~~~~~~~~~~
- **URL:** `/log`
- **Method:** `POST`
- **Required Headers:** 
    Content-Type: text/turtle
- **Request Body:**  
    A document in **Turtle (TTL)** format (`text/turtle`).

📤 Responses
~~~~~~~~~~~~
.. list-table::
   :widths: 15 60
   :header-rows: 1

   * - Status Code
     - Description
   * - `200 OK`
     - Data successfully stored.
   * - `400 Bad Request`
     - Error processing data or missing data.

---

🔹 ``GET /get_graph``
---------------------
**Description:**  
Retrieves the stored **JSON-LD** data, processes it, and returns it in **Turtle (TTL)** format.

✅ Request
~~~~~~~~~~
- **URL:** `/get_graph`
- **Method:** `GET`

📤 Responses
~~~~~~~~~~~~
.. list-table::
   :widths: 15 60
   :header-rows: 1

   * - Status Code
     - Description
   * - `200 OK`
     - Returns the data in **Turtle (TTL)** format.
   * - `404 Not Found`
     - No data available in the database.