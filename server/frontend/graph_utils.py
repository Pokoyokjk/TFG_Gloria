from pyvis.network import Network
import tempfile
import re


def generate_ttl_graph_pyvis(g):
    # only show the last part of the uri
    def shorten(uri):
        uri = str(uri)
        return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]           

    net = Network(height="600px", width="100%", directed=True)
    net.force_atlas_2based() # force layout for better visualization

    nodes = set()

    for s, p, o in g:
        short_s = shorten(s)
        short_o = shorten(o)
        short_p = shorten(p)

        # Add nodes if not already present
        if s not in nodes:
            net.add_node(str(s), label=short_s, shape="ellipse", title=str(s), font={"size": 15})
            nodes.add(s)
        if o not in nodes:
            net.add_node(str(o), label=short_o, shape="ellipse", title=str(o), font={"size": 15})
            nodes.add(o)

        # Add edges
        net.add_edge(str(s), str(o), label=short_p, arrows="to", title=str(p), font={"align": "middle"})

        # Temporary HTML 
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as tmp_file:
        # save in HTML
        net.save_graph(tmp_file.name)
        return tmp_file.name  # Return path to HTML



from pyvis.network import Network
import tempfile
import re


def generate_ttl_graph_pyvis(g):
    # only show the last part of the uri
    def shorten(uri):
        uri = str(uri)
        return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]           

    net = Network(height="600px", width="100%", directed=True)
    net.force_atlas_2based() # force layout for better visualization

    nodes = set()

    for s, p, o in g:
        short_s = shorten(s)
        short_o = shorten(o)
        short_p = shorten(p)

        # Add nodes if not already present
        if s not in nodes:
            net.add_node(str(s), label=short_s, shape="ellipse", title=str(s), font={"size": 15})
            nodes.add(s)
        if o not in nodes:
            net.add_node(str(o), label=short_o, shape="ellipse", title=str(o), font={"size": 15})
            nodes.add(o)

        # Add edges
        net.add_edge(str(s), str(o), label=short_p, arrows="to", title=str(p), font={"align": "middle"})

        # Temporary HTML 
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as tmp_file:
        # save in HTML
        net.save_graph(tmp_file.name)
        return tmp_file.name  # Return path to HTML



def generate_modification_graph_pyvis(logs, height="600px", width="100%", directed=True):
    net = Network(height=height, width=width, directed=directed)
    net.force_atlas_2based() # force layout for better visualization
    added_nodes = set()

    for log in logs:
        log_id = log['log_id']
        user = log.get('user', 'anonymous')
        ip = log.get('origin_ip', '')
        action = log.get('action', '')
        ttl = log.get('ttl_content', '')[:80].replace('\n', ' ') + "..."

        # Compose IP and user label
        if user and user != "anonymous":
            user_label = f"{user}\n({ip})"
            user_id = f"user:{user}"
        else:
            user_label = f"anonymous\n({ip})"
            user_id = f"user:anonymous:{ip}"

        # Add user node
        if user_id not in added_nodes:
            net.add_node(
                user_id,
                label=user_label,
                shape="ellipse",
                title=user_label,
                color="lightblue",
                font={"size": 15}
            )
            added_nodes.add(user_id)

        # Insertion/deletion node 
        change_id = f"change:{log_id}"
        change_color = "lightgreen" if action == "insertion" else "orange"
        net.add_node(
            change_id,
            label=log_id,
            shape="ellipse",
            title=ttl,
            color=change_color,
            font={"size": 12},
            size=30
        )
        added_nodes.add(change_id)

        # Edge between user and change
        net.add_edge(
            user_id,
            change_id,
            label=action.capitalize(),
            color="blue",
            font={"size": 12, "align": "middle"}
        )

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as tmp_file:
        net.save_graph(tmp_file.name)
        return tmp_file.name  # Return path to HTML