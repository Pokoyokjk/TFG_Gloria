# SEGB Server Structure

This project provides the code for implementing the logic behind the SEGB, including exposing a REST API, processing TTL files, and storing the *logged* info in a MongoDB database.

## Project Structure

```md
server/
├── *main.py* - Entry point for the Flask application with defined API routes.
├── *model.py* - Python code for interacting with the MongoDB database, defining data models and data access functions.
├── *token_generator_script.py* - Script for generating secure tokens for user authentication.
├── *utils/* - Contains utility functions and helpers used across the project.
├── ├── *credentials.py* - Module for managing credentials and authentication tokens.
├── ├── *experiments.py* - Module for managing experiments and related activities.
└── └── *semantic.py* - Module for managing semantic data, including creating, updating, and deleting semantic data.
```
