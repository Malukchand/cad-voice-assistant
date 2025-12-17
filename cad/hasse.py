# cad/hasse.py
import networkx as nx

def generate_hasse_data(assembly_tree):
    """
    Converts a hierarchical assembly tree into a Hasse Diagram (Poset).
    Returns JSON data suitable for React Flow (nodes, edges).
    """
    G = nx.DiGraph()
    
    # 1. Flatten tree and build full graph (including transitive edges implied by hierarchy)
    # Actually, the assembly tree usually GIVES us the "is-child-of" relationships directly.
    # In a perfect STEP file, Part -> Assembly -> Root is direct.
    # But sometimes there are nested assemblies or redundant links.
    
    # We will walk the tree. 
    # Nodes: id, label, type, level (calculated later)
    # Edges: child -> parent (Poset convention: x < y, so arrow from part to assembly)
    
    nodes_map = {} # id -> node_data
    edges_set = set()
    
    def traverse(node, parent_id=None):
        node_id = node['id']
        node_name = node['name']
        node_type = node['type']
        
        # Add to map if not exists (handle shared parts?)
        if node_id not in nodes_map:
            nodes_map[node_id] = {
                "id": node_id, 
                "label": node_name,
                "type": node_type
            }
        
        if parent_id:
            # Direction: Child -> Parent (is-part-of)
            # This follows the standard "Hasse diagram" convention where lower elements 
            # are "less than" upper elements.
            edges_set.add((node_id, parent_id))
            
        for child in node.get('children', []):
            traverse(child, node_id)
            
    traverse(assembly_tree)
    
    # 2. Build NetworkX Graph
    G.add_nodes_from(nodes_map.keys())
    G.add_edges_from(list(edges_set))
    
    # 3. Transitive Reduction
    # Removes shortcuts. If A->B and B->C and A->C exist, remove A->C.
    # This is the DEFINITION of a Hasse diagram edge set.
    TR = nx.transitive_reduction(G)
    
    # Note: TR is a new graph with same nodes but fewer edges.
    
    # 4. Calculate Levels (Longest path from a sink/bottom node)
    # In a DAG, we can assign levels.
    # Bottom nodes (in-degree 0 in Child->Parent graph) = Level 0?
    # Actually, in Child->Parent graph:
    # Parts have out-degree to Assembly.
    # Root has out-degree 0 (it is the top).
    # So "sources" are Parts, "sinks" are Roots.
    
    levels = {}
    # Longest path logic:
    # For each node, length of longest path to a root? OR from a leaf?
    # Hasse usually aligns by generic "rank".
    # Let's use simple topological generation or just longest path from source.
    
    for node in G.nodes():
        # Distance to "top" (Root)
        # Or distance from "bottom"
        # Let's allow Dagre on frontend to handle X coordinates, but we can hint ranks.
        pass

    # Actually, for data transfer, we just send structure. 
    # NetworkX has no simple "rank" attribute, and Dagre does it better visually.
    # WE JUST SEND THE REDUCED EDGES.
    
    # 5. Format for React Flow
    output_nodes = []
    for nid, data in nodes_map.items():
        output_nodes.append({
            "id": nid,
            "data": { "label": f"{data['label']} ({data['type']})" },
            "position": { "x": 0, "y": 0 }, # Layout will be handled by Dagre
            "type": "default" # or custom
        })
        
    output_edges = []
    for u, v in TR.edges():
        output_edges.append({
            "id": f"e{u}-{v}",
            "source": u, # Child
            "target": v, # Parent
            "type": "smoothstep",
            "animated": False,
            "style": { "stroke": "#333" }
        })
        
    return {
        "nodes": output_nodes,
        "edges": output_edges
    }
