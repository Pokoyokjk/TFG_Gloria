from langchain_community.chat_models import ChatOllama
from langchain.schema import SystemMessage, HumanMessage
import requests
from requests.auth import HTTPDigestAuth
import os
import time
import re
import json
import logging

logger = logging.getLogger("RAG")
os.makedirs('/logs', exist_ok=True)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(f'/logs/RAG.log', mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -> %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(file_handler)
logger.info("Starting RAG...")

# ollama_url = os.getenv("OLLAMA_REMOTE_URL", "http://ollama:11434")
url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

# Ensure keys are set via env vars
llm = ChatOllama(
    model="phi4:14b",  
    temperature=0.2,
    # base_url=ollama_url
    base_url="https://ollama.gsi.upm.es",
    
)

VIRTUOSO_SPARQL_ENDPOINT = os.getenv("VIRTUOSO_ENDPOINT", "http://amor-segb-virtuoso:8890/sparql-auth")
# Use the correct hostname or IP for your Virtuoso server
# VIRTUOSO_SPARQL_ENDPOINT = os.getenv("VIRTUOSO_ENDPOINT", "http://localhost:8890/sparql-auth")

VIRTUOSO_USER = os.getenv("VIRTUOSO_USER", "dba")
VIRTUOSO_PASSWORD = os.getenv("DBA_PASSWORD", "viryourbear")

def load_prefixes_and_patterns(path="/logs/for_RAG.json") -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Prefixes
        prefixes = data.get("prefixes", {})
        prefixes_str = "\n".join(f"PREFIX {k}: <{v}>" for k, v in prefixes.items())

        # Classes
        classes = data.get("classes", [])
        classes_str = "\n".join(f"- {cls}" for cls in classes)

        # Properties
        properties = data.get("properties", [])
        properties_str = "\n".join(f"- {prop}" for prop in properties)

        # Patterns
        patterns = data.get("patterns", {})
        pattern_lines = []
        for cls, props in patterns.items():
            pattern_lines.append(f"{cls}:")
            for prop in props:
                pattern_lines.append(f"  - {prop}")
        patterns_str = "\n".join(pattern_lines)

        return f"""### Prefixes
{prefixes_str}

### Classes
{classes_str}

### Properties
{properties_str}

### Patterns
{patterns_str}
"""
    except Exception as e:
        logger.error(f"⚠️ Failed to load prefixes and patterns: {e}")
        return ""
    
# Gets SPARQL query, uses SPARQLWrapper to consult, and returns a list with results
def sparql_query(query: str) -> str:
    headers = {
        "Accept": "application/sparql-results+json"
    }
    params = {
        "query": query
    }
    try: 
        response = requests.get(
            VIRTUOSO_SPARQL_ENDPOINT,
            params=params,
            headers=headers,
            auth=HTTPDigestAuth(VIRTUOSO_USER, VIRTUOSO_PASSWORD),
            timeout=30 
        )

    except requests.exceptions.Timeout:
        raise Exception("Timeout consulting SPARQL endpoint.")

    if response.status_code != 200:
        raise Exception(f"SPARQL query failed: {response.status_code} {response.text}")

    results = response.json()
    output = []

    for result in results["results"]["bindings"]:
        line = ", ".join(f"{k}: {v['value']}" for k, v in result.items())
        output.append(line)

    return "\n".join(output)

# Prompt template
def rag_with_sparql(question: str) -> str:
    # Step 1: Verify if the question is related to RDF or data querying
    prefixes_classes_properties_patterns = load_prefixes_and_patterns()

    system_prompt = f"""

    You are an expert in RDF and SPARQL. 
    If the user's question is not related to RDF or data querying, 
    respond only with: 'This is not a data-related question.'

    Otherwise, generate a valid SPARQL SELECT query for a Virtuoso endpoint. 
    ALWAYS include prefixes. Prefixes, classes, and properties and patterns are provided below: 
    
    {prefixes_classes_properties_patterns} 

    Important rules you must follow:
    - Use ONLY the properties listed under each class in the 'patterns' section.
    - Do NOT create links between classes and properties unless the relationship is defined in the patterns.
    - If the user's question requires a property that is NOT listed under a class, DO NOT invent it — instead respond: "Cannot answer with given patterns."
    - Use full URIs via prefixes as defined. Do not invent new prefixes.
    - If the query is not retrieving the entity (i.e., it's not a variable in the SELECT clause), entities MUST ALWAYS be represented as full literals (e.g., quoted strings), not as local names or bare identifiers

    CRITICAL INSTRUCTION:
    - NEVER use exact string matching with double quotes ("") to match URIs or resources
    - ALWAYS use FILTER(CONTAINS(?var, "term")) when searching for resources by name or partial URI
    - Remember that resources in the database are URIs, not simple strings
    - PRESERVE FULL IDENTIFIERS including underscores - do NOT split or truncate resource names
    - When filtering for resources like "name_XXXX", use the COMPLETE string: FILTER(CONTAINS(str(?name), "name_XXXX"))
    - Example: Use 'FILTER(CONTAINS(str(?resource), "example"))' instead of '?resource = "example"'
    - When matching against a URI or resource name, always use FILTER(CONTAINS()) on the string representation
    
    Please generate a SPARQL query without using hardcoded URIs (like <http://example.com/...>), because I don't know the exact resource identifiers.
    Instead, use a variable to find instances by their RDF type and filter them using CONTAINS to match a string on the URI or a label.   
    For all queries that search for resources by name, ALWAYS filter using CONTAINS with the COMPLETE identifier. 
    Do not use rdfs:label, use FILTER CONTAINS for ?name or ?label that may contain underscore as part of the name.

    IMPORTANT: Identifiers with underscores (like "name_0f6H") must be preserved in their entirety. Do not split or drop parts of the identifier.

    Please generate a SPARQL query that retrieves the full resource, including the prefix and the underscore in the identifier and use FILTER CONTAINS to search for the resource by name.

    Before answering, think step by step about what the subject, predicate, and variable to select are. CRITICAL: return ONLY the SPARQL query, WITHOUT any notes, markdown, comments, or explanations.

"""

    logger.info(f"Received question: {question}")

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question)
    ]

    start = time.time()

    # 1. SQL query
    logger.info(f"Passing question to llm")
    query = llm(messages).content.strip()
    query = re.sub(r"^```(?:sparql)?", "", query)
    query = re.sub(r"```$", "", query)
    query = query.strip()
    logger.info(f"Generated SPARQL query:\n{query}")
    print("⏱️ Time in generating SPARQL:", round(time.time() - start, 2), "s")

    # If not a data-arelated question
    if "This is not a data-related question." in query:
        return "This is not a data-related question."

    print("📤 Query generated by model:\n", query)

    # Paso 3: Run the SPARQL query
    try:
        result = sparql_query(query)
        logger.info(f"SPARQL query result:\n{result}")
    except Exception as e:
        # First attempt already failed with error
        max_attempts = 5
        attempt = 1  # Count the first attempt
        success = False
        last_error = str(e)
        
        while attempt < max_attempts and not success:
            logger.info(f"Attempt {attempt+1}/{max_attempts}: Regenerating SPARQL query")
            
            # Regenerate the SPARQL query with feedback about the error
            retry_messages = [
            SystemMessage(content=system_prompt + f"\n\nThe previous query failed with: {last_error}. Please try a different approach."),
            HumanMessage(content=question)
            ]
            
            query = llm(retry_messages).content.strip()
            query = re.sub(r"^```(?:sparql)?", "", query)
            query = re.sub(r"```$", "", query)
            query = query.strip()
            logger.info(f"Regenerated SPARQL query:\n{query}")
            
            # If not a data-related question
            if "This is not a data-related question." in query:
                return "This is not a data-related question."
            
            print(f"📤 Retry query {attempt+1}/{max_attempts} generated by model:\n", query)
            
            try:
                result = sparql_query(query)
                if result.strip():
                    success = True
                    logger.info(f"Retry attempt {attempt+1} successful with results")
                    break
                else:
                    logger.info(f"Retry attempt {attempt+1}: No results found")
                    last_error = "No results found for query"
            except Exception as e:
                logger.error(f"Retry attempt {attempt+1} failed: {e}")
                last_error = str(e)
            
            attempt += 1
        
        # If we didn't succeed after all attempts
        if not success:
            if "No results" in last_error:
                return f"⚠️ No results found after {max_attempts} attempts.\n\nLast SPARQL query:\n\n{query}\n"
            else:
                return f"❌ Error running SPARQL query after {max_attempts} attempts: {last_error}"

    logger.info(f"SPARQL query result:\n{result}")

    # Paso 4: Summarize the results
    summary_prompt = f"""
You are a helpful assistant.

Given the following SPARQL query results, answer the original question concisely and factually in one sentence.

If not asked specifically for an URI, only mention the local name (after the last slash or #), not full URIs. 
CRITICAL: 
- When you receive an URI, ALWAYS use the local name (after the last slash or #) to answer, do not guess new information.
- When you receive a String, DO NOT modify it, use it as is.

Avoid any additional explanation. Just provide the answer in this format:
"[Subject]'s [property] is [value]. Or for several values, use 'are' [value1, value2, ...]."

Results:
{result}

Original question: {question}
"""

    summary = llm([HumanMessage(content=summary_prompt)]).content
    return summary.strip()
   
