from flask import Flask, request, jsonify, render_template
from flask_cors import CORS, cross_origin
import networkx as nx
import pandas as pd
import numpy as np
import json

app = Flask(__name__, template_folder='./templates')
cors = CORS(app)

# getting the data
nodes = pd.read_parquet("../data/processed/nodes.parquet")
cash = pd.read_parquet("../data/processed/cash.parquet")
emt = pd.read_parquet("../data/processed/emt.parquet")
wire = pd.read_parquet("../data/processed/wire.parquet")
kyc = pd.read_parquet("../data/processed/kyc.parquet")

emt['trxn_message'] = emt['trxn_message'].fillna('')
cash = cash.replace(np.nan, None)
emt = emt.replace(np.nan, None)
wire = wire.replace(np.nan, None)
kyc = kyc.replace(np.nan, None)

# named_trafficker flags
nodes['is_exact_named_trafficker'] = (nodes['named_trafficker'] == 1) & (~nodes['named_trafficker'].isna())
nodes['is_rough_named_trafficker'] = ((nodes['named_trafficker'] < 1) & (nodes['named_trafficker'] > 0)) & (~nodes['named_trafficker'].isna())
# for named trafficker sources etc
with open("../task_3/names_metadata.json") as file:
    names_metadata = json.load(file)

nodes['named_trafficker_description'] = 'No'
nodes.loc[nodes['is_exact_named_trafficker'], 'named_trafficker_description'] = 'Yes'
nodes.loc[nodes['is_rough_named_trafficker'], 'named_trafficker_description'] = 'Maybe'


main_table = nodes[['cust_id', 'name', 'score', 'named_trafficker_description']].to_dict(orient='records')


# making the network
G = nx.MultiDiGraph()
for index, row in nodes.iterrows():
    G.add_node(row['cust_id'], display_info = "{}\n{}".format(row['name'] if row['name'] else ('External from ' + row['country'] if row['country'] else 'External'), row['cust_id']))

for index, row in emt.iterrows():
    G.add_edge(row['cust_id_sender'], row['cust_id_receiver'], display_info = 'EMT, ${}'.format(row['emt_value']), amount = row['emt_value'])

for index, row in wire.iterrows():
    G.add_edge(row['cust_id_sender'], row['cust_id_receiver'], display_info = 'Wire, ${}'.format(row['trxn_value']), amount = row['trxn_value'])

# G.add_node('BANK', display_info = 'BANK')
# for index, row in cash.iterrows():
#     if row['type'] == 'deposit':
#         G.add_edge(row['cust_id'], 'BANK', display_info = 'Cash deposit, ${}'.format(row['trxn_amount']))
#     if row['type'] == 'withdrawal':
#         G.add_edge('BANK', row['cust_id'], display_info = 'Cash withdrawal, ${}'.format(row['trxn_amount']))

G_nobank = G.copy()
# G_nobank.remove_edges_from(list(G.edges('BANK')))
G_nobank_rev = G_nobank.reverse()


print("Loaded all data, with {} nodes and {} edges".format(G.number_of_nodes(), G.number_of_edges()))

@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/user.html')
def user():
    return render_template('user.html')

@app.route('/init-data')
def init_data():
    return jsonify(main_table)


@app.route('/get-graph')
def get_graph():
    id = request.args.get('id')
    graph = make_ego_graph(G_nobank, G_nobank_rev, id, 2, 2)
    return networkx_to_json(graph)


@app.route('/get-user-data')
def get_user_data():
    id = request.args.get('id')

    if id == "BANK":
        return jsonify({})

    result = {'id': id}

    result['score'] = nodes.loc[nodes['cust_id'] == id]['score'].squeeze() 

    result['kyc'] = kyc.loc[kyc['cust_id'] == id].squeeze().to_dict()
    result['kyc']['cust_id'] = nodes.loc[nodes['cust_id'] == id]['cust_id'].iloc[0]
    result['kyc']['name'] = nodes.loc[nodes['cust_id'] == id]['name'].squeeze() # nodes df has names for some externals too
    result['kyc']['country'] = nodes.loc[nodes['cust_id'] == id]['country'].iloc[0]

    result['named_trafficker'] = {}
    result['named_trafficker']['exact'] = bool(nodes.loc[nodes['cust_id'] == id]['is_exact_named_trafficker'].squeeze())
    result['named_trafficker']['rough'] = bool(nodes.loc[nodes['cust_id'] == id]['is_rough_named_trafficker'].squeeze())

    if result['named_trafficker']['exact'] or result['named_trafficker']['rough']:
        this_metadata = names_metadata[result['kyc']['name'].lower()]
        result['named_trafficker']['matched_name'] = this_metadata['case_name']
        result['named_trafficker']['context'] = this_metadata['case_name_context']
        result['named_trafficker']['sources'] = this_metadata['sources']

    result['emt_sent'] = emt.loc[emt['cust_id_sender'] == id].to_dict(orient='records') # current person is sender
    result['emt_rec'] = emt.loc[emt['cust_id_receiver'] == id].to_dict(orient='records') # current person is recipient

    result['wire_sent'] = wire.loc[wire['cust_id_sender'] == id].to_dict(orient='records')
    result['wire_rec'] = wire.loc[wire['cust_id_receiver'] == id].to_dict(orient='records')

    result['cash_dep'] = cash.loc[(cash['type']=='deposit') & (cash['cust_id'] == id)].to_dict(orient='records')
    result['cash_wit'] = cash.loc[(cash['type']=='withdrawal') & (cash['cust_id'] == id)].to_dict(orient='records')

    return jsonify(result)


# takes id, df, and list of columns
# it then returns a list of columns for which the value for the id is 1
# these are the flags!
# DEPRECATED: not used because I handle this on the frontend, keeping it here in case
def get_flags(id, df, columns):
    row = df.loc[df['cust_id'] == id].iloc[0][columns]
    flags = [index for index, value in row.items() if value == 1.0]
    return flags


def get_cols_prefix(df, prefix):
    return [col for col in df.columns if col.startswith(prefix)]


def make_ego_graph(graph, graph_rev, node, pre_radius, post_radius):

    pre_nodes = nx.generators.ego_graph(graph_rev, node, radius=pre_radius, center=False).nodes()
    post_nodes = nx.generators.ego_graph(graph, node, radius=post_radius, center=False).nodes()
    subgraph = nx.induced_subgraph(graph, list(set(pre_nodes).union(set(post_nodes))) + [node]).copy() # do copy because otherwise nx will freeze graph

    # sometimes 'bank' is an isolated node so just remove it for cleanliness
    subgraph.remove_nodes_from(list(nx.isolates(subgraph))) 
    
    return subgraph


# returns nodes and edges as json in the format that vis.js expects it
def networkx_to_json(graph):

    edge_weights = list(sorted(graph.edges(data=True), key=lambda x: x[2]['amount'], reverse=True))
    if len(edge_weights)>1:
        max_weight = edge_weights[0][2]['amount']
        min_weight = edge_weights[-1][2]['amount']
    else:
        max_weight = 1
        min_weight = 0


    return_nodes = [{'id': n, 
                     'label': '', 
                     'value': nodes.loc[nodes['cust_id']==n]['score'].squeeze() if n != 'BANK' else 0.25, 
                     'title': graph.nodes[n]['display_info'] if graph.nodes[n]['display_info'] else n,
                     'color': '#008000' if n == 'BANK' else ('#FF5733' if 'EXT' in n else '#3355FF')
                     } for n in graph.nodes()]
    return_edges = [{'from': u, 
                     'to': v, 
                     'title': graph.edges[u,v,k]['display_info'],
                     'width': (graph.edges[u,v,k]['amount']-min_weight)/(max_weight-min_weight)*5+1,
                     } for u, v, k in graph.edges(keys=True)]
    
    return jsonify({'nodes':return_nodes, 'edges':return_edges})


if __name__ == '__main__':
    app.run()
