from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import networkx as nx
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)

# getting the data
nodes = pd.read_parquet("../data/processed/nodes_dedup.parquet")
cash = pd.read_parquet("../data/processed/cash.parquet")
emt = pd.read_parquet("../data/processed/emt.parquet")
wire = pd.read_parquet("../data/processed/wire.parquet")
kyc = pd.read_parquet("../data/processed/kyc.parquet")

main_table = nodes[['cust_id', 'name', 'score']].to_dict(orient='records')

emt['trxn_message'] = emt['trxn_message'].fillna('')
cash = cash.replace(np.nan, None)
emt = emt.replace(np.nan, None)
wire = wire.replace(np.nan, None)
kyc = kyc.replace(np.nan, None)

# making the network
G = nx.MultiDiGraph()
for index, row in nodes.iterrows():
    G.add_node(row['cust_id'], score = row['score'], display_info = row['name'] if row['name'] else ('External from ' + row['country'] if row['country'] else 'External'))

for index, row in emt.iterrows():
    G.add_edge(row['cust_id_sender'], row['cust_id_receiver'], amount=row['emt_value'], trxn_type='emt', trxn_id=row['trxn_id'], display_info = 'EMT, ${}'.format(row['emt_value']))

for index, row in wire.iterrows():
    G.add_edge(row['cust_id_sender'], row['cust_id_receiver'], amount=row['trxn_value'], trxn_type='wire', trxn_id=row['trxn_id'], display_info = 'Wire, ${}'.format(row['trxn_value']))

G.add_node('BANK', display_info = 'BANK')
for index, row in cash.iterrows():
    if row['type'] == 'deposit':
        G.add_edge(row['cust_id'], 'BANK', amount=row['trxn_amount'], trxn_type='cash', trxn_id=row['trxn_id'], display_info = 'Cash deposit, ${}'.format(row['trxn_amount']))
    if row['type'] == 'withdrawal':
        G.add_edge('BANK', row['cust_id'], amount=row['trxn_amount'], trxn_type='cash', trxn_id=row['trxn_id'], display_info = 'Cash withdrawal, ${}'.format(row['trxn_amount']))


G_rev = G.reverse()

print("Loaded all data, with {} nodes and {} edges".format(G.number_of_nodes(), G.number_of_edges()))

@app.route('/init-data')
def init_data():
    return jsonify(main_table)


@app.route('/get-graph')
def get_graph():
    id = request.args.get('id')
    graph = make_ego_graph(G, G_rev, id, 1, 2)
    return networkx_to_json(graph)


@app.route('/get-user-data')
def get_user_data():
    id = request.args.get('id')

    result = {'id': id}

    result['kyc'] = kyc.loc[kyc['cust_id'] == id].squeeze().to_dict()
    result['kyc']['country'] = nodes.loc[nodes['cust_id'] == id]['country'].iloc[0]

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
    # don't want out-edges from bank
    graph.remove_edges_from(list(graph.edges('BANK')))

    pre_nodes = nx.generators.ego_graph(graph_rev, node, radius=pre_radius, center=False).nodes()
    post_nodes = nx.generators.ego_graph(graph, node, radius=post_radius, center=False).nodes()
    subgraph = nx.Graph(nx.induced_subgraph(graph, list(set(pre_nodes).union(set(post_nodes))) + [node]))

    # sometimes 'bank' is an isolated node so just remove it for cleanliness
    subgraph.remove_nodes_from(list(nx.isolates(subgraph)))         
    
    return subgraph


# returns nodes and edges as json in the format that vis.js expects it
def networkx_to_json(graph):
    nodes = [{'id': n, 'label': n, 'value': graph.nodes[n]['score'], 'title': graph.nodes[n]['display_info']} for n in graph.nodes()]
    edges = [{'from': u, 'to': v, 'title': graph.edges[u,v,k]['display_info']} for u, v, k in graph.edges(keys=True)]
    return jsonify(nodes=nodes, edges=edges)


if __name__ == '__main__':
    app.run()
