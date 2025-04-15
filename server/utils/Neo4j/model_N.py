# Code for interacting with the database (connecting, saving, and retrieving data)
# MonDB uses classes because of its Object-Document Mapper (ODM) architecture (document-based)
# Neo4j uses functions because of its Cypher query language (graph-based)

from neo4j import GraphDatabase
# import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
import time

# logger = logging.getLogger('neo4j_server')
# logger.info("Loading Neo4j module...")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://amor-segb-neo4j:7687") # not with amor??
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neoforyou")



def connect_to_db(retries=10, delay=5):
    global driver
    for attempt in range(retries):
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            driver.verify_connectivity()
            print("Neo4j connection verified :)")
            return
        except Exception as e:
            print(f"Neo4j connection attempt {attempt+1} failed: {e}")
            time.sleep(delay)
    raise ConnectionError("Could not connect to Neo4j after multiple attempts :(")


# Only for the first time, to create the database
# Create unique URI constraint for RDF import
def constraint_graphinit():
    print("Creating unique URI constraint for RDF import and initializing graph configuration...")
    with driver.session() as session:
        session.run("""
            CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE
        """)
        session.run("""
            CALL n10s.graphconfig.init();
        """)
    print("Constraint created successfully.")
        


def store_modification(action:str, origin_ip:str, user:str, ttl_content: str) -> str:
    log_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat() # utc to avoid timezone issues
    def store_log(tx):
        
        query = """
        CREATE (log:Log {
            log_id: $log_id,
            user:$user,
            action: $action,
            timestamp: $timestamp,
            origin_ip: $origin_ip
        })
        CREATE (change:Change {
            ttl_content: $ttl_content
        })
        CREATE (log)-[:MODIFIED]->(change)
        """
        tx.run(query, log_id=log_id, user=user, action=action, timestamp=timestamp, 
               origin_ip=origin_ip, ttl_content=ttl_content)
        
    with driver.session() as session:
        session.execute_write(store_log)

    return log_id

def get_recent_logs(limit: int):
    def fetch_logs(tx):
        query = """
        MATCH (log:Log)-[:MODIFIED]->(change:Change)
        RETURN log.log_id AS log_id, log.user AS user, log.action AS action, 
               log.timestamp AS timestamp, log.origin_ip AS origin_ip, 
               change.ttl_content AS ttl_content
        ORDER BY log.timestamp DESC
        LIMIT $limit
        """
        result = tx.run(query, limit=limit)
        return [record.data() for record in result]
    
    with driver.session() as session:
        return session.execute_read(fetch_logs)
    
def get_logs_by_date(start_date: str, end_date: str): ### NO ME DEVUELVE EL DE LA ÚLTIMA FECHA (TIENE QUE SER MENOR)
    def fetch_logs_d(tx):                             ### ADEMÁS EL PRIMER GET QUIERO QUE LA PERSONA PONGA EL LIMITE
        query = """
        MATCH (log:Log)-[:MODIFIED]->(change:Change)
        WHERE log.timestamp >= $start_date AND log.timestamp <= $end_date
        RETURN log.log_id AS log_id, log.user AS user, log.action AS action, 
               log.timestamp AS timestamp, log.origin_ip AS origin_ip, 
               change.ttl_content AS ttl_content
        ORDER BY log.timestamp DESC
        """
        result = tx.run(query, start_date=start_date, end_date=end_date)
        return [record.data() for record in result]
    
    end_dt = datetime.fromisoformat(end_date) + timedelta(microseconds=1)
    
    with driver.session() as session:
        return session.execute_read(fetch_logs_d, start_date=start_date, end_date=end_dt.isoformat())
    