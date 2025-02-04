import cv2
import numpy as np
import json
import random
import networkx as nx
from scipy.spatial import distance
from shapely.geometry import LineString

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
    gfa = []
    gfa.append("H\tVN:Z:1.0")
    
    for i, (x, y) in enumerate(points):
        gfa.append(f"S\t{i}\t*")
        if i > 0:
            gfa.append(f"L\t{i-1}\t+\t{i}\t+\t0M")
    
    gfa.append(f"L\t{len(points)-1}\t+\t0\t+\t0M")  # Close the loop
    
    return gfa

def add_bubbles_to_gfa(gfa, points):
    num_bubbles = max(1, len(points) // 10)  # Add some random bubbles
    for _ in range(num_bubbles):
        i, j = sorted(random.sample(range(len(points)), 2))
        if j > i + 1:  # Ensure bubbles are meaningful
            bubble_node = len(points) + _  # Unique bubble node index
            gfa.append(f"S\t{bubble_node}\t*")
            gfa.append(f"L\t{i}\t+\t{bubble_node}\t+\t0M")
            gfa.append(f"L\t{bubble_node}\t+\t{j}\t+\t0M")
    
    return gfa

def generate_json_layout(points, gfa):
    nodes = {}
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i+1) % len(points)]
        x_start = x1 + (x2 - x1) // 3
        y_start = y1 + (y2 - y1) // 3
        x_end = x1 + 2 * (x2 - x1) // 3
        y_end = y1 + 2 * (y2 - y1) // 3
        nodes[i] = [x_start, y_start]
    fixed_positions = nodes#{i: points[i] for i in range(len(points))}
    
    G = nx.Graph()
    
    for line in gfa:
        if line.startswith("S"):
            node_id = int(line.split("\t")[1])
            if node_id < len(points):
                G.add_node(node_id, pos=points[node_id])
        elif line.startswith("L"):
            parts = line.split("\t")
            G.add_edge(int(parts[1]), int(parts[3]))
    
    pos = nx.spring_layout(G, pos=fixed_positions, fixed=fixed_positions.keys())
    nodes = {f"{i}+":[list(map(int, pos[i])), [i+10 for i in list(map(int, pos[i]))]] for i in G.nodes()}
    
    return json.dumps(nodes, indent=4)

def main(image_path, gfa_output, layout_output):
    points = extract_coordinates(image_path)
    gfa_content = generate_gfa(points)
    gfa_content = add_bubbles_to_gfa(gfa_content, points)
    json_content = generate_json_layout(points, gfa_content)


    with open(gfa_output, "w") as gfa_file:
        print("\n".join(gfa_content),file=gfa_file)
    
    with open(layout_output, "w") as layout_file:
        print(json_content,file=layout_file)
    
    print("Files generated:", gfa_output, layout_output)

# Example usage:
main("cow.jpg", "output.gfa", "layout.layout")

