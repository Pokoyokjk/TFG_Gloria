# SEGB Server Structure

This project provides the code for implementing the logic behind the SEGB, including disposing a REST API, processing TTL files and store the *logged* info in a MongoDB database.

## Project Structure

server/ 
├── *app.py* # Main Flask application with defined API routes.
├──* model.py* # Python code for interct with the MongoDB database, defining data models and data access functions. 
├── *semantic_utils.py* # RDF processing (e.g., Turtle ↔ JSON-LD conversion) and others auxiliary utilities.
├── *requirements.txt* # Python dependencies used by the server 
└── *Dockerfile* # Docker container definition for Flask-based API server.