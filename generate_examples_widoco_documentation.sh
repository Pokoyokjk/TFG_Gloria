docker run -ti --rm \
    -v ./ontology:/usr/local/widoco/in:Z \
    -v ./ontology/doc:/usr/local/widoco/out:Z \
    ghcr.io/dgarijo/widoco:latest \
    -confFile in/widoco-segb-examples-config.properties \
    -ontFile in/example.ttl \
    -outFolder out/segb/examples/doc \
    -webVowl -rewriteAll