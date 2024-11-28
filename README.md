# amor-sebb

AMOR - Semantic Ethical Black Box

## Launch the SEBB
To start the Semantic Ethical Black Box (SEBB), you should use the **compose.yaml** file provided in this repo.

## Tutorial
Then, you can execute the tutorial code provided in **sebb_tutorial.py** that log a set of triples (full ontologies and individuals stored in **example-data/**) into the SEBB and download all the triples stored in the SEBB to a local file.

>[!IMPORTANT]
>We strongly recommend to do **NOT use blank nodes** in any triples you want to log in the SEBB. They will not break the SEBB, but it can generate duplicated blank nodes (in the global graph) if they are sent several times to the SEBB.
