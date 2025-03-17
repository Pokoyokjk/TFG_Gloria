2. Introduction to SEGB
===============================================

The Semantic Ethical Glass Box (SEGB) is a system designed to persisently store a global semantic registry of all in-
teractions, decisions, or activities carried out by various Artificial Intelligence (AI)-based agents within a specific
scenario or environment. The objective is allowing that these events can later be consulted to audit, analyze, and debug the
agents’ behavior. Let's break the name in order to better understand the concept: 

- *Semantic*: The SEGB stores all the events within a global knowledge graph, i.e, makes use of semantics -by using Resource Description Framework (RDF)- to describe the information happened within the scenario. Using semantics gives place to a categorized, standarized and controlled modelling of the agents & avents existing in the scenario, offering some advantages such us 1) making advanced queries to the graph thanks to the well-defined meaningful relations and properties, or 2) extend from other standardized third-party ontologies for modelling our enviroment.

- *Ethical*: The SEGB aims to provide insights in terms of AI interpretability & explainability, whose underlying complexity limits humans from understanding why an action was executed or how a decision was reasoned. But why are interpretability & explainability so important? This help us understand why an unexpected, harmful action or decision was carried out, with the objective of ensuring the fairness and *ethics* of AI-based agents. This is crucial for achiving a good reliability, which is specially remarkable in high accountability scenarios where the AI-based decisions can significatively affect people. 

- *Glass*: In order to ensure this reliability and interpretability, the SEGB enhances the concepts of transparency and traceability of registered events. Looking inside this glass box do allow auditor follow step by step what a AI-agent reasoned and excecuted in every moment. 

- *Box*: It represents a storage container where all the events produced by AI-based agents are joined and persistently saved, conforming the global registry. 


The SEGB arises as part of the AMOR project, as it uses AI-based robots and imersive environments to interact with different groups of people, requiring these agents' ethical behaviour in order to meet the objectives. This implies being able to explain and interpret why a decision/action was produced and ensuring the ethics and transparency of these agents' behaviour.

Nevertheless, the SEGB is appliable to any scenario. as long as the AI-based agents has an Internet connection and the capability of 
generating TTL-formated logs.