import cv2
import numpy as np
import json
import random
import math
import networkx as nx
from scipy.spatial import distance
from shapely.geometry import LineString
import argparse
import sys

def diagonal_perpendicular_point(x1, y1, x2, y2, D=1):

    def calculate_mid_point(x1, y1, x2, y2):
        return (x1 +x2)/2, (y1 + y2) / 2

    xm, ym = calculate_mid_point(x1, y1, x2, y2)
    xo, yo = calculate_mid_point(x1, y1, xm, ym)
    xt, yt = calculate_mid_point(xm, ym, x2, y2)        
    
    # Compute the direction vector
    vx, vy = x2 - x1, y2 - y1
    
    # Compute the length of the vector
    length = math.sqrt(vx**2 + vy**2)

    if random.random() < 0.5:
        ux, uy = -vy / length, vx / length
    else:
        ux, uy = vy / length, -vx / length    
    return [[xo+D*ux, yo+D*uy],[xt+D*ux, yt+D*uy]]

def extract_coordinates(image_path, num_points=100):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    _, thresh = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return []
    
    contour = max(contours, key=cv2.contourArea)  # Take the largest contour
    points = [tuple(map(int, pt[0])) for pt in contour]
    
    # Use shapely to resample points for better spacing
    line = LineString(points)
    distances = np.linspace(0, line.length, num_points)
    sampled_points = [list(map(int, line.interpolate(d).coords[0])) for d in distances]
    
    return sampled_points

def generate_gfa(points):
    nodes, edges = [], []
    for i, (x, y) in enumerate(points):
        nodes.append(i)
        if i > 0:
            edges.append((i-1,i))
    edges.append((len(points)-1,0))
    return nodes, edges

def add_bubbles_to_gfa(nodes, edges, points, layout, num_bubbles=10):
    nodes_b, edges_b = [], []
    for _, B in enumerate(random.sample(edges,k=num_bubbles)):
        i, j = B
        bubble_node = len(points) + _  # Unique bubble node index
        nodes_b.append(bubble_node)
        edges_b.append((i, bubble_node))
        edges_b.append((bubble_node, j))

        ((_, _), (x1, y1)) = layout[f"{i}+"]  # Get the layout of the edge
        ((x2, y2), (_, _)) = layout[f"{j}+"] 
        new_coords = diagonal_perpendicular_point(x1, y1, x2, y2,10)

        layout[f"{bubble_node}+"] = new_coords#[[xp-5, yp-5], [xp+5, yp+5]]  # Add the bubble layout

    return nodes_b, edges_b, layout

def generate_fixed_layout(points):
    nodes = {}
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i+1) % len(points)]
        x_start = x1 + (x2 - x1) // 3
        y_start = y1 + (y2 - y1) // 3
        x_end = x1 + 2 * (x2 - x1) // 3
        y_end = y1 + 2 * (y2 - y1) // 3
        nodes[f"{i}+"] = [[x_start, y_start], [x_end, y_end]]
    return nodes #json.dumps(nodes, indent=4)

def mean_position(points):
    return np.mean([points[0][0], points[1][0]]), np.mean([points[0][1], points[1][1]])

def generate_force_layout(layout, nodes, edges, nodes_b, edges_b):
    fixed_positions = {i: mean_position(layout[f"{i}+"]) for i in range(len(nodes))}
    G = nx.Graph()
    
    for S in nodes + nodes_b:
            G.add_node(S)
    for L in edges + edges_b:
            G.add_edge(L[0], L[1])
    
    pos = nx.spring_layout(G, pos=fixed_positions, fixed=fixed_positions.keys(),k=1)

    force_layout = layout
    for n in G.nodes():
        if n in nodes_b:
            force_layout[f"{n}+"] = [list(map(int, pos[n])), [i+10 for i in list(map(int, pos[n]))]]

    return force_layout
def write_GFA(segments, links):
    gfa = ["H\tVN:Z:1.0"]
    for S in segments:
        gfa.append(f"S\t{S}\t*")
    for L in links:
        gfa.append(f"L\t{L[0]}\t+\t{L[1]}\t+\t0M")
    return gfa

def pandrawer(image,prefix,bubbles=10):

    points = extract_coordinates(image)
    nodes, edges = generate_gfa(points)
    
    fixed_node_layout = generate_fixed_layout(points)
    nodes_b, edges_b, layout = add_bubbles_to_gfa(nodes, edges, points, fixed_node_layout,bubbles)

    #force_layout = generate_force_layout (layout, nodes, edges, nodes_b, edges_b)

    with open( f"{prefix}.gfa", "w") as gfa_file:
        print("\n".join(write_GFA(nodes+nodes_b,edges+edges_b)),file=gfa_file)
        #print("\n".join(gfa_content),file=gfa_file)
    
    with open( f"{prefix}.layout", "w") as layout_file:
        json_content = json.dumps(layout, indent=4)
        print(json_content,file=layout_file)

def main_cli():
    parser = argparse.ArgumentParser(description="Generate a GFA and layout file from an image.")
    parser.add_argument("-i", "--image", required=True, help="Path to the input image file.")
    parser.add_argument("-p", "--prefix", required=True, help="Prefix for the output GFA and layout files.")
    parser.add_argument("-b","--bubbles", help="How many bubbles to add to the graph.",type=int,default=10)
    args = parser.parse_args(args=(sys.argv[1:] or ['--help']) )
    
    pandrawer(args.image,args.prefix,args.bubbles)

if __name__ == "__main__":
    main_cli()
