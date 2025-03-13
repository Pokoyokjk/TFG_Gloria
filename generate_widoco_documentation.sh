docker run -ti --rm \
    -v ./ontology:/usr/local/widoco/in:Z \
    -v ./ontology/doc:/usr/local/widoco/out:Z \
    ghcr.io/dgarijo/widoco:latest \
    -confFile in/widoco-segb-config.properties \
    -ontFile in/segb.ttl \
    -outFolder out/segb/ns/doc \
    -webVowl -rewriteAll