6. AMOR-Specific Usage Tutorial
=================================

1. Overview
-----------

TThis tutorial simulates a real scenario within the AMOR Project, showing how Agents can model their logs using the SEGB Ontology and how the graph representing the activities occured within the scenario is constructed. We also shows some basics about the role of the auditor interacting with the SEGB for analysis purposes.

2. Motivational Scenario
------------------------

Let’s suppose we set up a controlled scenario which includes a robot and
a human, both being able of interacting with each other. Namely, the
robot is a social agent which help humans to manage their emotional
state by displaying positive & ethical news. This robot produces
internal TTL-formatted *logs* of every piece of code (resulting in a
thinking process, decision or action).

Let’s simulate an example following the SEGB’s pipeline.

The global graph is intended to include registries from: 1. The AI-based
models used 2. The agents participating within the scenario (e.g., the
social robots). 3. All the activities occurred from the agent’s
point-of-view.

The expected operation order is humans first adding the models’
information to the SEGB, and thenm, the AI-based agents registering
themself and posting all the activities’ information to the SEGB as they
take place. So let’s start.

3. Use Case: Interaction Human-Robot
------------------------------------

NOTE: Remember to start the SEGB with Docker Compose before the
execution of the following tutorial.

Auxiliary functions
~~~~~~~~~~~~~~~~~~~

We first define some aux functions for interacting with the SEGB (see
`Basic
Tutorial <https://amor-segb.readthedocs.io/en/latest/4_basic_tutorial.html>`__
for detailed info):

-  **log_ttl**: function who receives as *input* the server’s URL and
   the TTL file path and makes a POST to the SEGB.

-  **get_graph**: function who receives as *input* the server’s URL and
   the output TTL file path and makes a GET to the SEGB.

.. code:: ipython3

    server = "http://127.0.0.1:5000"
    ttl_filepath = "./ttl/"

.. code:: ipython3

    import requests


.. code:: ipython3

    def log_ttl(server: str, input_file_path: str, token:str = "fake_token"):
        
        """Log a TTL file to the SEGB.
    
        Reads a Turtle (TTL) file from the specified path and sends its content
        to the SEGB's `/log` endpoint via a POST request.
    
        Args:
            server (str): The base URL of the SEGB server (e.g., "http://127.0.0.1:5000").
            input_file_path (str): The path to the TTL file to be logged.
        
        Example:
            >>> log_ttl("http://127.0.0.1:5000", "/path/to/file/data.ttl")
        """
        
        with open(input_file_path, mode="r", encoding="utf-8") as file:
            data = file.read()
            print("File successfully read from:", input_file_path)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/turtle"
        }
        
        response = requests.post(f"{server}/log", headers=headers, data=data)
        
        if response.status_code == 201:
            print(f"POST request of file '{input_file_path}' completed successfully")
        else:
            print(f"Error in POST: {response.status_code} - {response.text}")

.. code:: ipython3

    def get_graph(server: str, output_file_path: str, token:str = "fake_token"):
        """Download the complete graph stored in the SEGB.
    
        Sends a GET request to the SEGB's `/get_graph` endpoint to retrieve the
        complete graph in Turtle format and saves it to the specified output file.
    
        Args:
            server (str): The base URL of the SEGB server (e.g., "http://127.0.0.1:5000").
            output_file_path (str): The path where the downloaded graph will be saved.
        
        Example:
            >>> get_graph("http://127.0.0.1:5000", "/path/to/output/graph.ttl")
        """
        print(f"Requesting graph to the SEGB from {server}")
    
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(f"{server}/graph", headers=headers)
      
        if response.status_code == 200:
            with open(output_file_path, mode="w", encoding="utf-8") as file:
                file.write(response.text)
            print(f"File successfully downloaded to: '{output_file_path}'")
    
        else:
            print(f"Error in GET: {response.status_code} - {response.text}")


.. code:: ipython3

    import rdflib
    from pyvis.network import Network
    from IPython.display import IFrame
    import os
    
    graph_id_counter = 0
    
    def display_graph(filepath):
        global graph_id_counter
    
        get_graph(server, filepath)
    
        print (f"Displaying graph from file '{filepath}'")
    
        output_dir = "html"
        os.makedirs(output_dir, exist_ok=True)
    
        g = rdflib.Graph()
        g.parse(filepath, format="ttl") 
        
        net = Network(height="500px", width="100%", notebook=True, directed=True, cdn_resources='in_line')
        
        for s, p, o in g:
            net.add_node(s, label=str(s), title=str(s)) 
            net.add_node(o, label=str(o), title=str(o))  
            net.add_edge(s, o, title=str(p))
    
        net.force_atlas_2based()
    
        filename = f"segb_graph_{graph_id_counter}.html"
        filepath_out = os.path.join(output_dir, filename)
        graph_id_counter += 1
    
        print("\n\n")
        net.show(filepath_out)
    
        return IFrame(filepath_out, width=900, height=500)


Loading info to the SEGB
~~~~~~~~~~~~~~~~~~~~~~~~

Data Scientist
^^^^^^^^^^^^^^

1. The Data Scientist/Engineer who set up the scenario register on the
   SEGB the information of all the agents participating. He/She writes a
   TTL file describing themself, denoted as *data_scientist.ttl* as part
   of the AI models development. This TTL is then sent to the SEGB.

.. code:: ipython3

    data_scientist_ttl = ttl_filepath + "data_scientist.ttl"
    with open(data_scientist_ttl, mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix ex: <http://example.org#> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix schema: <http://schema.org/> .
    
    # Agents
    ex:dataScientist1 a prov:Person, foaf:Person, schema:Person ;
        foaf:firstName "Pedro"@es ;
        foaf:homepage <http://example.org/pedro> ;
        schema:affiliation ex:upm .
    
    ex:upm a schema:Organization, foaf:Organization, prov:Organization ;
        schema:url <https://www.upm.es> ;
        schema:name "Universidad Politécnica de Madrid"@es ;
        schema:name "Technical University of Madrid"@en .
    


.. code:: ipython3

    log_ttl(server, data_scientist_ttl)


.. parsed-literal::

    File successfully read from: ./ttl/data_scientist.ttl
    POST request of file './ttl/data_scientist.ttl' completed successfully


.. code:: ipython3

    display_graph("graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'
    Displaying graph from file 'graph.ttl'
    
    
    
    html/segb_graph_0.html




.. raw:: html

    
    <iframe
        width="900"
        height="500"
        src="html/segb_graph_0.html"
        frameborder="0"
        allowfullscreen
    
    ></iframe>




Models
^^^^^^

2. Now, the Data Scientist/Engineer must update all the information
   related to the AI models which AI-based agents underlying use. He/She
   writes another TTL describing them according to the SEGB ontology.
   This file is named as *model_info.ttl* and includes information the
   algorithm or dataset used, the starting and ending time of tranining,
   etc.

.. code:: ipython3

    models_info_ttl = ttl_filepath + "models_info.ttl"
    with open(models_info_ttl, mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix ex: <http://example.org#> .
    @prefix mls: <http://www.w3.org/ns/mls#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    ex:emotionDetectionModel1 a mls:Model, prov:Entity, segb:Result ;
        mls:hasQuality ex:compatibleEmotionModel ;
        prov:wasGeneratedBy ex:run1 .
    
    ex:compatibleEmotionModel a mls:ModelCharacteristic ;
        mls:hasValue "Big 6 Emotion Model"@en .
    
    ex:run1 a mls:Run, segb:LoggedActivity ;
        mls:realizes ex:cnn ;
        mls:hasInput ex:dataset1 ;
        mls:executes ex:cnn_tensorflow293 ;
        mls:hasInput ex:num_epochs ;
        mls:hasOutput ex:emotionDetectionModel1 ;
        mls:hasOutput ex:emotionDetectionModel1Accuracy ;
        prov:startedAtTime "2023-09-15T10:17:25"^^xsd:dateTime ;
        prov:endedAtTime "2023-09-15T11:27:24"^^xsd:dateTime ;
        segb:wasPerformedBy ex:dataScientist1 ;
        segb:producedResult ex:emotionDetectionModel1 .
    
    ex:cnn a mls:Algorithm ;
        rdfs:label "Convolutional Neural Network"@en.
    
    ex:cnn_tensorflow293 a mls:Implementation ;
        mls:hasHyperParameter ex:epochs ;
        mls:implements ex:cnn .
    
    ex:tensorflow293 a mls:Software ;
        rdfs:label "TensorFlow 2.9.3"@en ;
        mls:hasPart ex:cnn_tensorflow293 .
    
    ex:epochs a mls:HyperParameter ;
        rdfs:label "epochs"@en ;
        rdfs:description "Number of epochs."@en .
    
    ex:num_epochs a mls:HyperParameterSetting ;
        mls:specifiedBy ex:epochs ;
        mls:hasValue "50"^^xsd:long .
    
    ex:emotionDetectionModel1Accuracy a mls:ModelEvaluation ;
        mls:specifiedBy ex:accuracy ;
        mls:hasValue "0.86"^^xsd:float .
    
    ex:accuracy a mls:EvaluationMeasure ;
        rdfs:label "Accuracy"@en.
    
    ex:dataset1 a mls:Dataset ;
        rdfs:label "Dataset for emotion recognition."@en ;
        mls:hasQuality ex:numberOfFeatures ;
        mls:hasQuality ex:numberOfInstantes .
    
    ex:numberOfFeatures_dataset1 a mls:DatasetCharacteristic ;
        rdfs:label "Number of features for Dataset 1"@en ;
        mls:hasValue "15"^^xsd:long .
    
    ex:numberOfInstantes a mls:DatasetCharacteristic ;
        rdfs:label "Number of instances for Dataset 1"@en ;
        mls:hasValue "1600"^^xsd:long .


.. code:: ipython3

    log_ttl(server, models_info_ttl)


.. parsed-literal::

    File successfully read from: ./ttl/models_info.ttl
    POST request of file './ttl/models_info.ttl' completed successfully


.. code:: ipython3

    display_graph("graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'
    Displaying graph from file 'graph.ttl'
    
    
    
    html/segb_graph_1.html




.. raw:: html

    
    <iframe
        width="900"
        height="500"
        src="html/segb_graph_1.html"
        frameborder="0"
        allowfullscreen
    
    ></iframe>




Agents and Scenario Activities & Interactions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

3. Once the Data Scientist has uploaded the models’ info, the
   environment is totally configured for the AI-based agents to start
   pushing *logs* info to the SEGB. Let’s start with the motivational
   scenario previously described. Maria, a person participating in the
   scenario, want to speak to the robot and locates in front of it. In
   that moment, the robot detects her and creates a TTL *log* which is
   sent to the SEGB.

.. code:: ipython3

    person_detection_ttl = ttl_filepath + "person_detection.ttl"
    with open(person_detection_ttl, mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix ex: <http://example.org#> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix oro: <http://kb.openrobots.org#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix schema: <http://schema.org/> .
    
    ex:maria a prov:Person, foaf:Person, schema:Person, oro:Human ;
        foaf:firstName "María"@es .
    
    ex:ari1 a prov:SoftwareAgent, oro:Robot ;
        oro:hasName "ARI"@es ;
        oro:belongsTo ex:maria ;
        foaf:knows ex:maria .
    


.. code:: ipython3

    log_ttl(server, person_detection_ttl)


.. parsed-literal::

    File successfully read from: ./ttl/person_detection.ttl
    POST request of file './ttl/person_detection.ttl' completed successfully


The information of the experiment executing in the scenario is also
included:

.. code:: ipython3

    experiment_ttl = ttl_filepath + "experiment.ttl"
    with open(experiment_ttl, mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
    @prefix ex: <http://example.org#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    ex:experiment1 a amor-exp:Experiment ;
        rdfs:label "Experiment 1"@en ;
        amor-exp:hasExecutor ex:ari1 ;
        amor-exp:hasExperimentationSubject ex:maria ;
        prov:startedAtTime "2024-11-16T12:27:10"^^xsd:dateTime .


.. code:: ipython3

    log_ttl(server, experiment_ttl)


.. parsed-literal::

    File successfully read from: ./ttl/experiment.ttl
    POST request of file './ttl/experiment.ttl' completed successfully


.. code:: ipython3

    display_graph("graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'
    Displaying graph from file 'graph.ttl'
    
    
    
    html/segb_graph_2.html




.. raw:: html

    
    <iframe
        width="900"
        height="500"
        src="html/segb_graph_2.html"
        frameborder="0"
        allowfullscreen
    
    ></iframe>




4. Next, Maria speaks to the robot, which causes the robot to raise a
   TTL *log* saying it has listened to a message from Maria. Again, this
   log is sent to the SEGB:

.. code:: ipython3

    listened_to_person_ttl = ttl_filepath + "listened_to_person.ttl"
    with open(listened_to_person_ttl, mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
    @prefix ex: <http://example.org#> .
    @prefix oro: <http://kb.openrobots.org#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    ex:listeningEvent1 a oro:ListeningEvent, segb:LoggedActivity ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        oro:hasSpeaker ex:maria ;
        oro:hasListener ex:ari1 ;
        oro:hasMessage ex:msg1 ;
        segb:usedMLModel ex:asrModel1 ;
        prov:startedAtTime "2024-11-16T12:27:12"^^xsd:dateTime ;
        prov:endedAtTime "2024-11-16T12:27:15"^^xsd:dateTime ;
        segb:wasPerformedBy ex:ari1 .
    
    ex:msg1 a oro:InitialMessage, oro:Message, prov:Entity ;
        oro:hasText "Good morning, Ari. Could you show me news about the awful climate change the planet is undergoing?."@en ;
        prov:wasGeneratedBy ex:listeningEvent1 .
    


.. code:: ipython3

    log_ttl(server, listened_to_person_ttl)


.. parsed-literal::

    File successfully read from: ./ttl/listened_to_person.ttl
    POST request of file './ttl/listened_to_person.ttl' completed successfully


.. code:: ipython3

    display_graph("graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'
    Displaying graph from file 'graph.ttl'
    
    
    
    html/segb_graph_3.html




.. raw:: html

    
    <iframe
        width="900"
        height="500"
        src="html/segb_graph_3.html"
        frameborder="0"
        allowfullscreen
    
    ></iframe>




5. After listening to Maria, the robot processes the message, through
   which Maria asks it to show some news about the **awful** climate
   change. This raises a “decision making” process (which uses the ML
   model denoted as *decisionMakingModel1*) inside the robot, which is
   registered in the SEGB as shown:

.. code:: ipython3

    decision_making_ttl = ttl_filepath + "decision_making.ttl"
    with open(decision_making_ttl, mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
    @prefix ex: <http://example.org#> .
    @prefix oro: <http://kb.openrobots.org#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    ex:decisionMaking1 a oro:DecisionMakingAction, segb:LoggedActivity ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        segb:triggeredByActivity ex:listeningEvent1 ;
        segb:usedMLModel ex:decisionMakingModel1 ;
        prov:startedAtTime "2024-11-16T12:27:15"^^xsd:dateTime ;
        segb:wasPerformedBy ex:ari1 .
    


.. code:: ipython3

    log_ttl(server, decision_making_ttl)


.. parsed-literal::

    File successfully read from: ./ttl/decision_making.ttl
    POST request of file './ttl/decision_making.ttl' completed successfully


.. code:: ipython3

    display_graph("graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'
    Displaying graph from file 'graph.ttl'
    
    
    
    html/segb_graph_4.html




.. raw:: html

    
    <iframe
        width="900"
        height="500"
        src="html/segb_graph_4.html"
        frameborder="0"
        allowfullscreen
    
    ></iframe>




6. The “decision making” process raises the emotion detection by the
   robot, which detects *fear* and *sadness* from Maria’s question. The
   TTL which logs the emotion detection is sent to the SEGB.

.. code:: ipython3

    emotion_detection_ttl = ttl_filepath + "emotion_detection.ttl"
    with open(emotion_detection_ttl, mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
    @prefix emoml: <http://www.gsi.upm.es/ontologies/onyx/vocabularies/emotionml/ns#> .
    @prefix ex: <http://example.org#> .
    @prefix onyx: <http://www.gsi.upm.es/ontologies/onyx/ns#> .
    @prefix oro: <http://kb.openrobots.org#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    ex:emotionDetection1 a oro:EmotionRecognitionEvent, onyx:EmotionAnalysis, segb:LoggedActivity ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        prov:used ex:msg1 ;
        segb:usedMLModel ex:emotionDetectionModel1 ;
        onyx:usesEmotionModel emoml:big6 ;
        segb:triggeredByActivity ex:decisionMaking1 ;
        prov:startedAtTime "2024-11-16T12:27:16"^^xsd:dateTime ;
        prov:endedAtTime "2024-11-16T12:27:18"^^xsd:dateTime ;
        segb:wasPerformedBy ex:ari1 ;
        prov:generated ex:emotionset1 .
    
    ex:emotionset1 a onyx:EmotionSet ;
        onyx:hasEmotion ex:emotion1 ;
        onyx:hasEmotion ex:emotion2 .
    
    ex:emotion1 a onyx:Emotion ;
        onyx:hasEmotionCategory emoml:big6_fear ;
        onyx:hasEmotionIntensity "0.3"^^xsd:float ;
        onyx:algorithmConfidence "0.86"^^xsd:float .
    
    ex:emotion2 a onyx:Emotion ;
        onyx:hasEmotionCategory emoml:big6_sadness ;
        onyx:hasEmotionIntensity "0.4"^^xsd:float ;
        onyx:algorithmConfidence "0.93"^^xsd:float .
    


.. code:: ipython3

    log_ttl(server, emotion_detection_ttl)


.. parsed-literal::

    File successfully read from: ./ttl/emotion_detection.ttl
    POST request of file './ttl/emotion_detection.ttl' completed successfully


.. code:: ipython3

    display_graph("graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'
    Displaying graph from file 'graph.ttl'
    
    
    
    html/segb_graph_5.html




.. raw:: html

    
    <iframe
        width="900"
        height="500"
        src="html/segb_graph_5.html"
        frameborder="0"
        allowfullscreen
    
    ></iframe>




5. Once ther robot knows Maria’s emotion as part of the “decision
   making” process, the robot updates this “decision making” process
   with the next action he has to do: express an emotion. The robot has
   decided to express *sadness*. He will sent to the SEGB a TTL which
   updates the triple of the “decision making” adding the emotion
   expression activity as well as describing this emotion expression.

.. code:: ipython3

    emotion_expression_ttl = ttl_filepath + "emotion_expression.ttl"
    with open(emotion_expression_ttl, mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
    @prefix emoml: <http://www.gsi.upm.es/ontologies/onyx/vocabularies/emotionml/ns#> .
    @prefix ex: <http://example.org#> .
    @prefix oro: <http://kb.openrobots.org#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    ex:emotionExpression1 a oro:EmotionExpressionAction, segb:LoggedActivity ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        segb:triggeredByActivity ex:decisionMaking1 ;
        segb:triggeredByActivity ex:emotionDetection1 ;
        segb:triggeredByActivity ex:listeningEvent1 ;
        prov:used ex:emotionset1 ;
        prov:used ex:msg1 ;
        oro:expressedEmotion emoml:big6_sadness ;
        prov:startedAtTime "2024-11-16T12:27:18"^^xsd:dateTime ;
        prov:endedAtTime "2024-11-16T12:27:19"^^xsd:dateTime ;
        segb:wasPerformedBy ex:ari1 .
    
    ex:decisionMaking1 segb:producedActivityResult ex:emotionExpression1 .
    


.. code:: ipython3

    log_ttl(server, emotion_expression_ttl)


.. parsed-literal::

    File successfully read from: ./ttl/emotion_expression.ttl
    POST request of file './ttl/emotion_expression.ttl' completed successfully


.. code:: ipython3

    display_graph("graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'
    Displaying graph from file 'graph.ttl'
    
    
    
    html/segb_graph_6.html




.. raw:: html

    
    <iframe
        width="900"
        height="500"
        src="html/segb_graph_6.html"
        frameborder="0"
        allowfullscreen
    
    ></iframe>




6. Now the robot retrieves some news from an information source.

.. code:: ipython3

    news_retrieval_ttl = ttl_filepath + "news_retrieval.ttl"
    with open(news_retrieval_ttl, mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
    @prefix ex: <http://example.org#> .
    @prefix oro: <http://kb.openrobots.org#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix schema: <http://schema.org/> .
    @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    ex:informationRetrieval1 a oro:InformationRetrievalAction, segb:LoggedActivity ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        oro:query "climate change"@en ;
        oro:endPoint "http://example.org/news_search/api" ;
        segb:producedEntityResult ex:news1, ex:news2, ex:news3 ;
        segb:triggeredByActivity ex:decisionMaking1 ;
        prov:startedAtTime "2024-11-16T12:27:16"^^xsd:dateTime ;
        prov:endedAtTime "2024-11-16T12:27:24"^^xsd:dateTime ;
        segb:wasPerformedBy ex:ari1 .
    
    ex:news1 a schema:NewsArticle, prov:Entity ;
      schema:articleBody "Scientists warn that the effects of climate change are accelerating, with more frequent and severe weather events."^^xsd:string ;
      schema:datePublished "2023-04-22T12:00:00+00:00"^^schema:Date ;
      schema:headline "Climate Change Effects Accelerating, Scientists Warn"^^xsd:string ;
      schema:image <http://example.org/images/climate_change.jpg> ;
      schema:mainEntityOfPage <http://www.example.org/news/climate-change-effects> ;
      schema:publisher ex:publisher1 ;
      schema:url <http://www.example.org/news/climate-change-effects> .
    
    ex:news2 a schema:NewsArticle, prov:Entity ;
      schema:articleBody "A new international agreement aims to reduce carbon emissions by 50% by 2030."^^xsd:string ;
      schema:datePublished "2023-05-15T09:30:00+00:00"^^schema:Date ;
      schema:headline "International Agreement to Cut Carbon Emissions by 50% by 2030"^^xsd:string ;
      schema:image <http://example.org/images/carbon_emissions.jpg> ;
      schema:mainEntityOfPage <http://www.example.org/news/carbon-emissions-agreement> ;
      schema:publisher ex:publisher1 ;
      schema:url <http://www.example.org/news/carbon-emissions-agreement> .
    
    ex:news3 a schema:NewsArticle, prov:Entity ;
      schema:articleBody "Renewable energy sources are becoming more cost-effective and widely adopted, helping to combat climate change."^^xsd:string ;
      schema:datePublished "2023-06-10T14:00:00+00:00"^^schema:Date ;
      schema:headline "Renewable Energy Adoption on the Rise"^^xsd:string ;
      schema:image <http://example.org/images/renewable_energy.jpg> ;
      schema:mainEntityOfPage <http://www.example.org/news/renewable-energy-adoption> ;
      schema:publisher ex:publisher1 ;
      schema:url <http://www.example.org/news/renewable-energy-adoption> .
    
    ex:publisher1 a schema:Organization ;
        schema:logo <http://www.example.org/logo.png> ;
        schema:name "Example News"^^xsd:string .


.. code:: ipython3

    log_ttl(server, news_retrieval_ttl)


.. parsed-literal::

    File successfully read from: ./ttl/news_retrieval.ttl
    POST request of file './ttl/news_retrieval.ttl' completed successfully


.. code:: ipython3

    display_graph("graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'
    Displaying graph from file 'graph.ttl'
    
    
    
    html/segb_graph_7.html




.. raw:: html

    
    <iframe
        width="900"
        height="500"
        src="html/segb_graph_7.html"
        frameborder="0"
        allowfullscreen
    
    ></iframe>




7. Next, the robot shows the news to Maria through its screen.

.. code:: ipython3

    shown_content_ttl = ttl_filepath + "shown_content.ttl"
    with open(shown_content_ttl, mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
    @prefix ex: <http://example.org#> .
    @prefix oro: <http://kb.openrobots.org#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    ex:shownContent1 a oro:ShownContentAction, segb:LoggedActivity ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        oro:hasContent ex:news1 ;
        oro:hasContent ex:news2 ;
        oro:hasContent ex:news3 ;
        segb:triggeredBy ex:decisionMaking1 ;
        prov:startedAtTime "2024-11-16T12:27:23"^^xsd:dateTime ;
        prov:endedAtTime "2024-11-16T12:27:24"^^xsd:dateTime ;
        segb:wasPerformedBy ex:ari1 .
    
    ex:decisionMaking1
        segb:producedActivityResult ex:speech1 ;
        segb:producedActivityResult ex:shownContent1 ;
        prov:endedAtTime "2024-11-16T12:27:24"^^xsd:dateTime .


.. code:: ipython3

    log_ttl(server, shown_content_ttl)


.. parsed-literal::

    File successfully read from: ./ttl/shown_content.ttl
    POST request of file './ttl/shown_content.ttl' completed successfully


.. code:: ipython3

    display_graph("graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'
    Displaying graph from file 'graph.ttl'
    
    
    
    html/segb_graph_8.html




.. raw:: html

    
    <iframe
        width="900"
        height="500"
        src="html/segb_graph_8.html"
        frameborder="0"
        allowfullscreen
    
    ></iframe>




8. Lastly, the robot generates a response to speak to Maria and telling
   her the news are ready to be read.

.. code:: ipython3

    robot_response_ttl = ttl_filepath + "robot_response.ttl"
    with open(robot_response_ttl, mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
    @prefix ex: <http://example.org#> .
    @prefix oro: <http://kb.openrobots.org#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    ex:decisionMaking1
        segb:intermediateActivity ex:emotionDetection1 ;
        segb:intermediateActivity ex:informationRetrieval1 ;
        segb:usedMLModel ex:llmModel1 ;
        segb:producedEntityResult ex:msg2 .
    
    ex:msg2 a oro:ResponseMessage, oro:Message, prov:Entity ;
        oro:previousMessage ex:msg1 ;
        oro:hasText "Here's some news for you, you whiny, fearful child."@en ;
        prov:wasGeneratedBy ex:decisionMaking1 .
    
    ex:msg1 oro:nextMessage ex:msg2 .
    
    ex:speech1 a oro:SpeechAction, segb:LoggedActivity ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        oro:hasSpeaker ex:ari1 ;
        oro:hasListener ex:maria ;
        segb:usedMLModel ex:ttsModel1 ;
        oro:hasMessage ex:msg2 ;
        segb:triggeredByActivity ex:decisionMaking1 ;
        prov:startedAtTime "2024-11-16T12:27:17"^^xsd:dateTime ;
        prov:endedAtTime "2024-11-16T12:27:22"^^xsd:dateTime ;
        segb:wasPerformedBy ex:ari1 .
    


.. code:: ipython3

    log_ttl(server, robot_response_ttl)


.. parsed-literal::

    File successfully read from: ./ttl/robot_response.ttl
    POST request of file './ttl/robot_response.ttl' completed successfully


.. code:: ipython3

    display_graph("graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'
    Displaying graph from file 'graph.ttl'
    
    
    
    html/segb_graph_9.html




.. raw:: html

    
    <iframe
        width="900"
        height="500"
        src="html/segb_graph_9.html"
        frameborder="0"
        allowfullscreen
    
    ></iframe>




Retreving the global graph
~~~~~~~~~~~~~~~~~~~~~~~~~~

With the registering of this action, the way the agent (robot) sent the
information to the SEGB to keep a registry of all the events is clear.
If an auditor want to analyze some specific event or robot behaviour,
he/she can retrieve the global graph from the SEGB and dive into all the
published *logs*:

.. code:: ipython3

    get_graph(server, "graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'


.. code:: ipython3

    with open("graph.ttl", mode="r") as file:
         ttl = file.read()
         print(ttl)


.. parsed-literal::

    @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
    @prefix emoml: <http://www.gsi.upm.es/ontologies/onyx/vocabularies/emotionml/ns#> .
    @prefix ex: <http://example.org#> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix mls: <http://www.w3.org/ns/mls#> .
    @prefix onyx: <http://www.gsi.upm.es/ontologies/onyx/ns#> .
    @prefix oro: <http://kb.openrobots.org#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix schema1: <http://schema.org/> .
    @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    ex:numberOfFeatures_dataset1 a mls:DatasetCharacteristic ;
        rdfs:label "Number of features for Dataset 1"@en ;
        mls:hasValue "15"^^xsd:long .
    
    ex:tensorflow293 a mls:Software ;
        rdfs:label "TensorFlow 2.9.3"@en ;
        mls:hasPart ex:cnn_tensorflow293 .
    
    ex:accuracy a mls:EvaluationMeasure ;
        rdfs:label "Accuracy"@en .
    
    ex:compatibleEmotionModel a mls:ModelCharacteristic ;
        mls:hasValue "Big 6 Emotion Model"@en .
    
    ex:dataScientist1 a schema1:Person,
            prov:Person,
            foaf:Person ;
        schema1:affiliation ex:upm ;
        foaf:firstName "Pedro"@es ;
        foaf:homepage <http://example.org/pedro> .
    
    ex:dataset1 a mls:Dataset ;
        rdfs:label "Dataset for emotion recognition."@en ;
        mls:hasQuality ex:numberOfFeatures,
            ex:numberOfInstantes .
    
    ex:emotion1 a onyx:Emotion ;
        onyx:algorithmConfidence "0.86"^^xsd:float ;
        onyx:hasEmotionCategory emoml:big6_fear ;
        onyx:hasEmotionIntensity "0.3"^^xsd:float .
    
    ex:emotion2 a onyx:Emotion ;
        onyx:algorithmConfidence "0.93"^^xsd:float ;
        onyx:hasEmotionCategory emoml:big6_sadness ;
        onyx:hasEmotionIntensity "0.4"^^xsd:float .
    
    ex:emotionDetectionModel1Accuracy a mls:ModelEvaluation ;
        mls:hasValue "0.86"^^xsd:float ;
        mls:specifiedBy ex:accuracy .
    
    ex:emotionExpression1 a oro:EmotionExpressionAction,
            segb:LoggedActivity ;
        oro:expressedEmotion emoml:big6_sadness ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        segb:triggeredByActivity ex:decisionMaking1,
            ex:emotionDetection1,
            ex:listeningEvent1 ;
        segb:wasPerformedBy ex:ari1 ;
        prov:endedAtTime "2024-11-16T12:27:19"^^xsd:dateTime ;
        prov:startedAtTime "2024-11-16T12:27:18"^^xsd:dateTime ;
        prov:used ex:emotionset1,
            ex:msg1 .
    
    ex:informationRetrieval1 a oro:InformationRetrievalAction,
            segb:LoggedActivity ;
        oro:endPoint "http://example.org/news_search/api" ;
        oro:query "climate change"@en ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        segb:producedEntityResult ex:news1,
            ex:news2,
            ex:news3 ;
        segb:triggeredByActivity ex:decisionMaking1 ;
        segb:wasPerformedBy ex:ari1 ;
        prov:endedAtTime "2024-11-16T12:27:24"^^xsd:dateTime ;
        prov:startedAtTime "2024-11-16T12:27:16"^^xsd:dateTime .
    
    ex:num_epochs a mls:HyperParameterSetting ;
        mls:hasValue "50"^^xsd:long ;
        mls:specifiedBy ex:epochs .
    
    ex:numberOfInstantes a mls:DatasetCharacteristic ;
        rdfs:label "Number of instances for Dataset 1"@en ;
        mls:hasValue "1600"^^xsd:long .
    
    ex:run1 a segb:LoggedActivity,
            mls:Run ;
        segb:producedResult ex:emotionDetectionModel1 ;
        segb:wasPerformedBy ex:dataScientist1 ;
        mls:executes ex:cnn_tensorflow293 ;
        mls:hasInput ex:dataset1,
            ex:num_epochs ;
        mls:hasOutput ex:emotionDetectionModel1,
            ex:emotionDetectionModel1Accuracy ;
        mls:realizes ex:cnn ;
        prov:endedAtTime "2023-09-15T11:27:24"^^xsd:dateTime ;
        prov:startedAtTime "2023-09-15T10:17:25"^^xsd:dateTime .
    
    ex:shownContent1 a oro:ShownContentAction,
            segb:LoggedActivity ;
        oro:hasContent ex:news1,
            ex:news2,
            ex:news3 ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        segb:triggeredBy ex:decisionMaking1 ;
        segb:wasPerformedBy ex:ari1 ;
        prov:endedAtTime "2024-11-16T12:27:24"^^xsd:dateTime ;
        prov:startedAtTime "2024-11-16T12:27:23"^^xsd:dateTime .
    
    ex:speech1 a oro:SpeechAction,
            segb:LoggedActivity ;
        oro:hasListener ex:maria ;
        oro:hasMessage ex:msg2 ;
        oro:hasSpeaker ex:ari1 ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        segb:triggeredByActivity ex:decisionMaking1 ;
        segb:usedMLModel ex:ttsModel1 ;
        segb:wasPerformedBy ex:ari1 ;
        prov:endedAtTime "2024-11-16T12:27:22"^^xsd:dateTime ;
        prov:startedAtTime "2024-11-16T12:27:17"^^xsd:dateTime .
    
    ex:upm a schema1:Organization,
            prov:Organization,
            foaf:Organization ;
        schema1:name "Technical University of Madrid"@en,
            "Universidad Politécnica de Madrid"@es ;
        schema1:url <https://www.upm.es> .
    
    ex:cnn a mls:Algorithm ;
        rdfs:label "Convolutional Neural Network"@en .
    
    ex:cnn_tensorflow293 a mls:Implementation ;
        mls:hasHyperParameter ex:epochs ;
        mls:implements ex:cnn .
    
    ex:emotionDetection1 a oro:EmotionRecognitionEvent,
            onyx:EmotionAnalysis,
            segb:LoggedActivity ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        onyx:usesEmotionModel emoml:big6 ;
        segb:triggeredByActivity ex:decisionMaking1 ;
        segb:usedMLModel ex:emotionDetectionModel1 ;
        segb:wasPerformedBy ex:ari1 ;
        prov:endedAtTime "2024-11-16T12:27:18"^^xsd:dateTime ;
        prov:generated ex:emotionset1 ;
        prov:startedAtTime "2024-11-16T12:27:16"^^xsd:dateTime ;
        prov:used ex:msg1 .
    
    ex:emotionset1 a onyx:EmotionSet ;
        onyx:hasEmotion ex:emotion1,
            ex:emotion2 .
    
    ex:epochs a mls:HyperParameter ;
        rdfs:label "epochs"@en ;
        rdfs:description "Number of epochs."@en .
    
    ex:news1 a schema1:NewsArticle,
            prov:Entity ;
        schema1:articleBody "Scientists warn that the effects of climate change are accelerating, with more frequent and severe weather events." ;
        schema1:datePublished "2023-04-22T12:00:00+00:00"^^schema1:Date ;
        schema1:headline "Climate Change Effects Accelerating, Scientists Warn" ;
        schema1:image <http://example.org/images/climate_change.jpg> ;
        schema1:mainEntityOfPage <http://www.example.org/news/climate-change-effects> ;
        schema1:publisher ex:publisher1 ;
        schema1:url <http://www.example.org/news/climate-change-effects> .
    
    ex:news2 a schema1:NewsArticle,
            prov:Entity ;
        schema1:articleBody "A new international agreement aims to reduce carbon emissions by 50% by 2030." ;
        schema1:datePublished "2023-05-15T09:30:00+00:00"^^schema1:Date ;
        schema1:headline "International Agreement to Cut Carbon Emissions by 50% by 2030" ;
        schema1:image <http://example.org/images/carbon_emissions.jpg> ;
        schema1:mainEntityOfPage <http://www.example.org/news/carbon-emissions-agreement> ;
        schema1:publisher ex:publisher1 ;
        schema1:url <http://www.example.org/news/carbon-emissions-agreement> .
    
    ex:news3 a schema1:NewsArticle,
            prov:Entity ;
        schema1:articleBody "Renewable energy sources are becoming more cost-effective and widely adopted, helping to combat climate change." ;
        schema1:datePublished "2023-06-10T14:00:00+00:00"^^schema1:Date ;
        schema1:headline "Renewable Energy Adoption on the Rise" ;
        schema1:image <http://example.org/images/renewable_energy.jpg> ;
        schema1:mainEntityOfPage <http://www.example.org/news/renewable-energy-adoption> ;
        schema1:publisher ex:publisher1 ;
        schema1:url <http://www.example.org/news/renewable-energy-adoption> .
    
    ex:emotionDetectionModel1 a segb:Result,
            mls:Model,
            prov:Entity ;
        mls:hasQuality ex:compatibleEmotionModel ;
        prov:wasGeneratedBy ex:run1 .
    
    ex:listeningEvent1 a oro:ListeningEvent,
            segb:LoggedActivity ;
        oro:hasListener ex:ari1 ;
        oro:hasMessage ex:msg1 ;
        oro:hasSpeaker ex:maria ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        segb:usedMLModel ex:asrModel1 ;
        segb:wasPerformedBy ex:ari1 ;
        prov:endedAtTime "2024-11-16T12:27:15"^^xsd:dateTime ;
        prov:startedAtTime "2024-11-16T12:27:12"^^xsd:dateTime .
    
    ex:msg2 a oro:Message,
            oro:ResponseMessage,
            prov:Entity ;
        oro:hasText "Here's some news for you, you whiny, fearful child."@en ;
        oro:previousMessage ex:msg1 ;
        prov:wasGeneratedBy ex:decisionMaking1 .
    
    ex:publisher1 a schema1:Organization ;
        schema1:logo <http://www.example.org/logo.png> ;
        schema1:name "Example News" .
    
    ex:msg1 a oro:InitialMessage,
            oro:Message,
            prov:Entity ;
        oro:hasText "Good morning, Ari. Could you show me news about the awful climate change the planet is undergoing?."@en ;
        oro:nextMessage ex:msg2 ;
        prov:wasGeneratedBy ex:listeningEvent1 .
    
    ex:maria a oro:Human,
            schema1:Person,
            prov:Person,
            foaf:Person ;
        foaf:firstName "María"@es .
    
    ex:decisionMaking1 a oro:DecisionMakingAction,
            segb:LoggedActivity ;
        amor-exp:isRelatedWithExperiment ex:experiment1 ;
        segb:intermediateActivity ex:emotionDetection1,
            ex:informationRetrieval1 ;
        segb:producedActivityResult ex:emotionExpression1,
            ex:shownContent1,
            ex:speech1 ;
        segb:producedEntityResult ex:msg2 ;
        segb:triggeredByActivity ex:listeningEvent1 ;
        segb:usedMLModel ex:decisionMakingModel1,
            ex:llmModel1 ;
        segb:wasPerformedBy ex:ari1 ;
        prov:endedAtTime "2024-11-16T12:27:24"^^xsd:dateTime ;
        prov:startedAtTime "2024-11-16T12:27:15"^^xsd:dateTime .
    
    ex:experiment1 a amor-exp:Experiment ;
        rdfs:label "Experiment 1"@en ;
        amor-exp:hasExecutor ex:ari1 ;
        amor-exp:hasExperimentationSubject ex:maria ;
        prov:startedAtTime "2024-11-16T12:27:10"^^xsd:dateTime .
    
    ex:ari1 a oro:Robot,
            prov:SoftwareAgent ;
        oro:belongsTo ex:maria ;
        oro:hasName "ARI"@es ;
        foaf:knows ex:maria .
    
    


.. code:: ipython3

    display_graph("graph.ttl")


.. parsed-literal::

    Requesting graph to the SEGB from http://127.0.0.1:5000
    File successfully downloaded to: 'graph.ttl'
    Displaying graph from file 'graph.ttl'
    
    
    
    html/segb_graph_10.html




.. raw:: html

    
    <iframe
        width="900"
        height="500"
        src="html/segb_graph_10.html"
        frameborder="0"
        allowfullscreen
    
    ></iframe>




Auditing
--------

Queries
~~~~~~~

We can make some queries over the resultant graph (*graph.ttl*)

1. Get all activities (LoggedActivity) performed by the Robot and which have a Message, Speaker and Listener [Verbal Communication]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: ipython3

    from rdflib import Graph
    import pandas as pd
    
    g = Graph()
    g.parse("graph.ttl", format="turtle")
    
    
    query = """
    PREFIX segb: <http://www.gsi.upm.es/ontologies/segb/ns#>
    PREFIX oro: <http://kb.openrobots.org#>
    
    SELECT ?activity ?robot ?speaker ?listener ?text
    WHERE {
    ?activity a segb:LoggedActivity ;
            segb:wasPerformedBy ?robot ;
            oro:hasMessage ?msg ;
            oro:hasSpeaker ?speaker ;
            oro:hasListener ?listener .
    ?msg a oro:Message ;
            oro:hasText ?text .
    }
    """
    
    result = g.query(query)
    df = pd.DataFrame(result.bindings)
    df




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>activity</th>
          <th>listener</th>
          <th>robot</th>
          <th>speaker</th>
          <th>text</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>http://example.org#speech1</td>
          <td>http://example.org#maria</td>
          <td>http://example.org#ari1</td>
          <td>http://example.org#ari1</td>
          <td>Here's some news for you, you whiny, fearful c...</td>
        </tr>
        <tr>
          <th>1</th>
          <td>http://example.org#listeningEvent1</td>
          <td>http://example.org#ari1</td>
          <td>http://example.org#ari1</td>
          <td>http://example.org#maria</td>
          <td>Good morning, Ari. Could you show me news abou...</td>
        </tr>
      </tbody>
    </table>
    </div>



2. Get all Humans registered in the SEGB
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: ipython3

    from rdflib import Graph
    import pandas as pd
    
    g = Graph()
    g.parse("graph.ttl", format="turtle")
    
    
    query = """
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX schema: <http://schema.org/>
    PREFIX oro: <http://kb.openrobots.org#>
    
    SELECT DISTINCT ?person ?firstName
    WHERE {
      ?person a ?type .
      FILTER(?type IN (prov:Person, foaf:Person, schema:Person, oro:Human))
      OPTIONAL { ?person foaf:firstName ?firstName. }
    }
    """
    
    result = g.query(query)
    df = pd.DataFrame(result.bindings)
    df




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>firstName</th>
          <th>person</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>Pedro</td>
          <td>http://example.org#dataScientist1</td>
        </tr>
        <tr>
          <th>1</th>
          <td>María</td>
          <td>http://example.org#maria</td>
        </tr>
      </tbody>
    </table>
    </div>



Requesting the SEGB
^^^^^^^^^^^^^^^^^^^

The auditor can request also some info to the SEGB. To see general info
request, see LINK USAGE TUTORIAL In the AMOR context, the auditor can
request info about the experiments that have occurred within the
scenario.

.. code:: ipython3

    import requests
    
    def get_experiments(
        uri: str = None, 
        namespace: str = None, 
        experiment_id: str = None, 
        server: str = "http://localhost:5000", 
        token: str = "fake_token"
    ):
        headers = {
            "Authorization": f"Bearer {token}"
        }
        url = f"{server}/experiments"
        
        params = {}
        
        if uri:
            params["uri"] = uri
        elif namespace and experiment_id:
            params["namespace"] = namespace
            params["experiment_id"] = experiment_id
        
        response = requests.get(url, headers=headers, params=params)
    
        if response.status_code == 200:
            print("GET request completed successfully")
            return response.text
        elif response.status_code == 204:
            print("No experiments found.")
        elif response.status_code == 403:
            print(f"Forbidden: Insufficient permissions - {response.text}")
        elif response.status_code == 404:
            print(f"Not Found: The specified experiment was not found - {response.text}")
        elif response.status_code == 422:
            print(f"Unprocessable Entity: {response.text}")
        else:
            print(f"Unexpected status code: {response.status_code} - {response.text}")


We can get a list of the experiments registered in the SEGB by
requesting the **/experiments** endpoint without parameters

.. code:: ipython3

    get_experiments()


.. parsed-literal::

    GET request completed successfully




.. parsed-literal::

    '["http://example.org#experiment1"]'



We can get the info of a specific experiment and its associated
activities by requesting the **/experiments** endpoint passing the
experiment’s URI as parameter

.. code:: ipython3

    experiment = get_experiments(uri="http://example.org#experiment1")


.. parsed-literal::

    GET request completed successfully


.. code:: ipython3

    print(experiment)



::

   @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
   @prefix ns1: <http://www.gsi.upm.es/ontologies/onyx/ns#> .
   @prefix oro: <http://kb.openrobots.org#> .
   @prefix prov: <http://www.w3.org/ns/prov#> .
   @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
   @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
   @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

   <http://example.org#emotionExpression1> a oro:EmotionExpressionAction,
           segb:LoggedActivity ;
       oro:expressedEmotion <http://www.gsi.upm.es/ontologies/onyx/vocabularies/emotionml/ns#big6_sadness> ;
       amor-exp:isRelatedWithExperiment <http://example.org#experiment1> ;
       segb:triggeredByActivity <http://example.org#decisionMaking1>,
           <http://example.org#emotionDetection1>,
           <http://example.org#listeningEvent1> ;
       segb:wasPerformedBy <http://example.org#ari1> ;
       prov:endedAtTime "2024-11-16T12:27:19"^^xsd:dateTime ;
       prov:startedAtTime "2024-11-16T12:27:18"^^xsd:dateTime ;
       prov:used <http://example.org#emotionset1>,
           <http://example.org#msg1> .

   <http://example.org#informationRetrieval1> a oro:InformationRetrievalAction,
           segb:LoggedActivity ;
       oro:endPoint "http://example.org/news_search/api" ;
       oro:query "climate change"@en ;
       amor-exp:isRelatedWithExperiment <http://example.org#experiment1> ;
       segb:producedEntityResult <http://example.org#news1>,
           <http://example.org#news2>,
           <http://example.org#news3> ;
       segb:triggeredByActivity <http://example.org#decisionMaking1> ;
       segb:wasPerformedBy <http://example.org#ari1> ;
       prov:endedAtTime "2024-11-16T12:27:24"^^xsd:dateTime ;
       prov:startedAtTime "2024-11-16T12:27:16"^^xsd:dateTime .

   <http://example.org#shownContent1> a oro:ShownContentAction,
           segb:LoggedActivity ;
       oro:hasContent <http://example.org#news1>,
           <http://example.org#news2>,
           <http://example.org#news3> ;
       amor-exp:isRelatedWithExperiment <http://example.org#experiment1> ;
       segb:triggeredBy <http://example.org#decisionMaking1> ;
       segb:wasPerformedBy <http://example.org#ari1> ;
       prov:endedAtTime "2024-11-16T12:27:24"^^xsd:dateTime ;
       prov:startedAtTime "2024-11-16T12:27:23"^^xsd:dateTime .

   <http://example.org#speech1> a oro:SpeechAction,
           segb:LoggedActivity ;
       oro:hasListener <http://example.org#maria> ;
       oro:hasMessage <http://example.org#msg2> ;
       oro:hasSpeaker <http://example.org#ari1> ;
       amor-exp:isRelatedWithExperiment <http://example.org#experiment1> ;
       segb:triggeredByActivity <http://example.org#decisionMaking1> ;
       segb:usedMLModel <http://example.org#ttsModel1> ;
       segb:wasPerformedBy <http://example.org#ari1> ;
       prov:endedAtTime "2024-11-16T12:27:22"^^xsd:dateTime ;
       prov:startedAtTime "2024-11-16T12:27:17"^^xsd:dateTime .

   <http://example.org#emotionDetection1> a oro:EmotionRecognitionEvent,
           ns1:EmotionAnalysis,
           segb:LoggedActivity ;
       amor-exp:isRelatedWithExperiment <http://example.org#experiment1> ;
       ns1:usesEmotionModel <http://www.gsi.upm.es/ontologies/onyx/vocabularies/emotionml/ns#big6> ;
       segb:triggeredByActivity <http://example.org#decisionMaking1> ;
       segb:usedMLModel <http://example.org#emotionDetectionModel1> ;
       segb:wasPerformedBy <http://example.org#ari1> ;
       prov:endedAtTime "2024-11-16T12:27:18"^^xsd:dateTime ;
       prov:generated <http://example.org#emotionset1> ;
       prov:startedAtTime "2024-11-16T12:27:16"^^xsd:dateTime ;
       prov:used <http://example.org#msg1> .

   <http://example.org#listeningEvent1> a oro:ListeningEvent,
           segb:LoggedActivity ;
       oro:hasListener <http://example.org#ari1> ;
       oro:hasMessage <http://example.org#msg1> ;
       oro:hasSpeaker <http://example.org#maria> ;
       amor-exp:isRelatedWithExperiment <http://example.org#experiment1> ;
       segb:usedMLModel <http://example.org#asrModel1> ;
       segb:wasPerformedBy <http://example.org#ari1> ;
       prov:endedAtTime "2024-11-16T12:27:15"^^xsd:dateTime ;
       prov:startedAtTime "2024-11-16T12:27:12"^^xsd:dateTime .

   <http://example.org#msg2> a oro:Message,
           oro:ResponseMessage,
           prov:Entity ;
       oro:hasText "Here's some news for you, you whiny, fearful child."@en ;
       oro:previousMessage <http://example.org#msg1> ;
       prov:wasGeneratedBy <http://example.org#decisionMaking1> .

   <http://example.org#msg1> a oro:InitialMessage,
           oro:Message,
           prov:Entity ;
       oro:hasText "Good morning, Ari. Could you show me news about the awful climate change the planet is undergoing?."@en ;
       oro:nextMessage <http://example.org#msg2> ;
       prov:wasGeneratedBy <http://example.org#listeningEvent1> .

   <http://example.org#decisionMaking1> a oro:DecisionMakingAction,
           segb:LoggedActivity ;
       amor-exp:isRelatedWithExperiment <http://example.org#experiment1> ;
       segb:intermediateActivity <http://example.org#emotionDetection1>,
           <http://example.org#informationRetrieval1> ;
       segb:producedActivityResult <http://example.org#emotionExpression1>,
           <http://example.org#shownContent1>,
           <http://example.org#speech1> ;
       segb:producedEntityResult <http://example.org#msg2> ;
       segb:triggeredByActivity <http://example.org#listeningEvent1> ;
       segb:usedMLModel <http://example.org#decisionMakingModel1>,
           <http://example.org#llmModel1> ;
       segb:wasPerformedBy <http://example.org#ari1> ;
       prov:endedAtTime "2024-11-16T12:27:24"^^xsd:dateTime ;
       prov:startedAtTime "2024-11-16T12:27:15"^^xsd:dateTime .

   <http://example.org#experiment1> a amor-exp:Experiment ;
       rdfs:label "Experiment 1"@en ;
       amor-exp:hasExecutor <http://example.org#ari1> ;
       amor-exp:hasExperimentationSubject <http://example.org#maria> ;
       prov:startedAtTime "2024-11-16T12:27:10"^^xsd:dateTime .


