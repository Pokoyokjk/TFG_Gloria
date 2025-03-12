# Semantic Ethical Glass Box (SEGB)

## 1. The AMOR Project 

The AMOR Project aims to develop critical thinking and the ability to manage one's emotions when engaging with media and social networks, in order to combat phenomena such as disinformation, hate speech, and clickbait.

The general objectives of the project are defined around its strategic lines, as follows:

- Research semantic text analysis techniques that facilitate cooperative processing in the cloud and at the edge.

- Investigate the analysis and application of moral and ethical values, including their auditing.

- Explore new visualization techniques and immersive interaction that make effective use of textual data analysis. This includes the development of sector-specific applications that promote social awareness on issues such as rural depopulation, the risk of radicalization among vulnerable groups, and the needs of the elderly and dependent individuals.

This project is funded by the Ministry of Economic Affairs and Digital Transformation and the European Union – NextGeneration EU, within the UNICO I+D Cloud Program.

## 2. Introduction to the Semantic Ethical Glass Box

The Semantic Ethical Glass Box (SEGB) is a system designed to persisently store a global semantic registry of all in-
teractions, decisions, or activities carried out by various Artificial Intelligence (AI)-based agents within a specific
scenario or environment. The objective is allowing that these events can later be consulted to audit, analyze, and debug the
agents’ behavior. Let's break the name in order to better understand the cpncept: 

- *Semantic*: The SEGB stores all the events within a global knowledge graph, i.e, makes use of semantics -by using Resource Description Framework (RDF)- to describe the information happened within the scenario. Using semantics gives place to a categorized, standarized and controlled modelling of the agents & avents existing in the scenario, offering some advantages such us 1) making advanced queries to the graph thanks to the well-defined meaningful
relations and properties, or 2) extend from other standardized third-party ontologies for modelling our enviroment.

- *Ethical*: The SEGB aims to provide insights in terms of AI interpretability & explainability, whose underlying com-
plexity limits humans from understanding why an action was executed or how a
decision was reasoned. But why are interpretability & explainability so important? This help us understand why an unexpected, harmful action or decision was carried out, with the objective of ensuring the fairness and *ethics* of AI-based agents. This is crucial for achiving a good reliability, which is specially remarkable in high accountability scenarios where the AI-based decisions can significatively affect people. 

- *Glass*: In order to ensure this reliability and interpretability, the SEGB enhances the concepts of transparency
and traceability of registered events. Looking inside this glass box do allow auditor follow step by step what a AI-agent reasoned and excecuted in every moment. 

- *Box*: It represents a storage bucket where all the events occurred are stored by the AI-based agents. This events are joined and persistently saved, conforming the global registry. 

The SEGB arises as part of the AMOR project, as it uses AI-based robots and imersive environments to interact with different groups of people, requiring these agents' ethical behaviour in order to meet the objectives. This implies being able to explain and interpret why a decision/action was produced and ensuring the ethics and transparency of these gents' behaviour.

Nevertheless, the SEGB is appliable to any scenario. as long as the AI-based agents has an Internet connection and the capability of 
generating TTL-formated logs.


## 3. Design of the SEGB

### 3.1. Semantic Model

### 3.2. Knowledge Graph Construction Pipeline 

## 4. Architecture Overview 

## 5. SEGB Tutorial 

In the folder [tutorial](./tutorial), an extensive use case is presented to understand the usability and capabilities of the SEGB. 


AMOR - Semantic Ethical Glass Box

## Launch the SEGB
To start the Semantic Ethical Glass Box (SEGB), you should use the **compose.yaml** file provided in this repo.

## Tutorial
Then, you can execute the tutorial code provided in **segb_tutorial.py** that log a set of triples (full ontologies and individuals stored in **example-data/**) into the SEGB and download all the triples stored in the SEGB to a local file.

## 1. Overview 

The Semantic Ethical Glass Box (SEGB) is global *log* storage, which keeps a semantic registry (graph) of logs generated within different systems. It is comprised of two parts: 

1. A REST API Flask-based server, whose functions are 1) to add new triples to the global graph and 2) retrieve the global graph; 

2. A MongoDB-based database, where the global graph is storaged in JSON-LD format

>[!IMPORTANT]
> Since the SEGB is in a testing stage, the MongoDB database is stored in a local Docker-managed volume on the local computer where the SEGB is deployed. In the future, during the deployment stage, the database will be migrated to a centralized server to store all the records in a safe, consistent manner.

## API Description

### 🔹 `POST /log`
**Description:**  
Stores the received **Turtle (TTL)** data, converts it to **JSON-LD**, and saves it in the database. The TTL data could contain one or several triples.

#### ✅ Request
- **URL:** `/log`
- **Method:** `POST`
- **Required Headers:** 
    Content-Type: text/turtle
- **Request Body:**  
    A document in **Turtle (TTL)** format (`text/turtle`).

#### 📤 Responses
| Status Code | Description |
|-------------|-------------|
| `200 OK` | Data successfully stored. |
| `400 Bad Request` | Error processing data or missing data. |

---

### 🔹 `GET /get_graph`
**Description:**  
Retrieves the stored **JSON-LD** data, processes it, and returns it in **Turtle (TTL)** format.

#### ✅ Request
- **URL:** `/get_graph`
- **Method:** `GET`

#### 📤 Responses
| Status Code | Description |
|-------------|-------------|
| `200 OK` | Returns the data in **Turtle (TTL)** format. |
| `404 Not Found` | No data available in the database. |

## 3. Launching the Semantic Ethical Glass Box (SEGB)

Use the docker-compose file available in this repository. This action requires access to the image used in the docker compose file. This consists on several steps:

1. Get a personal access token to enable console login in ghcr.io (Follow these instructions <https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens>)

>[!CAUTION]
>A *classic personal access token* is preferred, given that *fine-grained access* token may cause problems.

3. In your console, export your token with:

```shell
export CR_PAT=<YOUR_TOKEN>
```

4. Now, login in ghcr.io with:

```shell
echo $CR_PAT | docker login ghcr.io -u <YOUR_USER_NAME> --password-stdin
```

5. Finally, execute docker compose in the directory you have your docker-compose.yaml file:

```shell
docker compose up -d
```

6. The URL of the SEGB is `http://127.0.0.1:5000`

## 4. Sending data to and retrieving data from the SEGB.

To update a new TTL file containing one or several triples, we makes a POST request to the */log* route. Given that we have a Turtle file "*data.ttl*".

>[!IMPORTANT]
>We strongly recommend to do **NOT use blank nodes** in any triples you want to log in the SEGB. They will not break the SEGB, but it can generate duplicated blank nodes (in the global graph) if they are sent several times to the SEGB due to external limitatios.

We can make it through the *curl* tool if using *bash*:

```shell
curl -X POST \
     -H "Content-Type: text/turtle" \
     --data-binary "@data.ttl" \
     http://127.0.0.1:5000/log
```

or by using *Python*:

```python
import requests

url = "http://127.0.0.1:5000/log"

headers = {"Content-Type": "text/turtle"}

with open("./data.ttl", "rb") as file:
    ttl_data = file.read()

response = requests.post(url, headers=headers, data=ttl_data)
```

Similarly, for retrieving the data we makes a GET request to the */get_graph* route.

Using *curl* over *bash*:

```shell
curl -X GET http://127.0.0.1:5000/get_graph -o global_graph.ttl
```

or *Python*:

```python

import requests

url = "http://127.0.0.1:5000/get_graph"

response = requests.get(url)

with open("output.ttl", "wb") as file:
    file.write(response.content)

```

## 5. Using the SEGB in the AMOR context

We have defined a *Python* script, [segb_tutorial.py](./segb_tutorial.py) which defines an SEGB's use case within the AMOR context. 

It first defines two functions, both of them including console *logs* and some errors verification logic, and being appropiately described by using *Docstring*:

- ***log_ttl***: function who receives as *input* the server's URL and the TTL file path and makes a POST to the SEGB.

- ***get_graph***: function who receives as *input* the server's URL and the output TTL file path and makes a GET to the SEGB.


The workflow defined within the *script* defines the use case as follows:

1. First, the server's URL and the TTL files' routes with the different ontologies used (stored in the [example_data](./example-data/) directory in this repo) are defined:

``` python
    server = "http://127.0.0.1:5000"
    
    models = [
        "example-data/amor.ttl",
        "example-data/mft.ttl",
        "example-data/bhv.ttl",
        "example-data/amor-mft.ttl",
        "example-data/amor-bhv.ttl"
    ]
```

2. The ontologies TTL files are mapped to the SEGB's global graph via the *log_ttl* function:

``` python
    for model in models:
        log_ttl(server, model)
```

3. A new ontology can be uptated whenever we need it, so we upload a new ontology (in this case, plenty of individuals):

``` python
    input_ttl_file = "example-data/amor-examples.ttl"
    log_ttl(server, input_ttl_file)
```

4. 
``` python
    input_ttl_file = "example-data/new-triples.ttl"
    log_ttl(server, input_ttl_file)
```

5. We finally retrieve the global graph in TTL format, which includes all the mapped ontologies and all the logs which previously were uploaded, using the *get_graph* function:

``` python
    output_ttl_file = "graph.ttl"
    get_graph(server, output_ttl_file)
```