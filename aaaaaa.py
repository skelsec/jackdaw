

from graph_tool import load_graph_from_csv
from graph_tool.topology import all_shortest_paths, shortest_path


graph_file = '/home/devel/Desktop/projects/jackdaw/t.txt'
g = load_graph_from_csv(graph_file, directed=False, string_vals=False, hashed=False)

for e in g.edges():
    print(e)

for p in shortest_path(g , 213080, 5012):
    print(p)


#for v in g.vertices():
#    print(v)



#