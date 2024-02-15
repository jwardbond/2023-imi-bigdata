from flask import Flask, request, jsonify
import pandas as pd
import networkx as nx
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)

# getting the data
cash = pd.read_csv("../data/processed/cash.csv")
emt = pd.read_csv("../data/processed/emt.csv")
wire = pd.read_csv("../data/processed/wire.csv")
kyc = pd.read_csv("../data/processed/kyc.csv")

kyc_display = kyc[['cust_id', 'name']].to_dict(orient='records')

emt['trxn_message'] = emt['trxn_message'].fillna('')

# making the network
G = nx.MultiDiGraph()
for index, row in emt.iterrows():
    G.add_edge(row['cust_id_sender'], row['cust_id_receiver'], amount=row['emt_value'], trxn_type='emt', trxn_id=row['trxn_id'])

for index, row in wire.iterrows():
    G.add_edge(row['cust_id_sender'], row['cust_id_receiver'], amount=row['trxn_value'], trxn_type='wire', trxn_id=row['trxn_id'])

G.add_node('BANK')
for index, row in cash.iterrows():
    if row['type'] == 'deposit':
        G.add_edge(row['cust_id'], 'BANK', amount=row['trxn_amount'], trxn_type='cash', trxn_id=row['trxn_id'])
    if row['type'] == 'withdrawal':
        G.add_edge('BANK', row['cust_id'], amount=row['trxn_amount'], trxn_type='cash', trxn_id=row['trxn_id'])

print("Loaded all data, with {} nodes and {} edges".format(G.number_of_nodes(), G.number_of_edges()))



@app.route('/init-data')
def init_data():
    return jsonify(kyc_display)


@app.route('/get-graph')
def get_graph():
    id = request.args.get('id')
    graph = make_ego_graph(G, id, 1, 1)
    return networkx_to_json(graph)


@app.route('/get-user-data')
def get_user_data():
    id = request.args.get('id')

    result = {'id': id}

    result['kyc'] = kyc.loc[kyc['cust_id'] == id].squeeze().to_dict()

    result['emt_sent'] = emt.loc[emt['cust_id_sender'] == id].to_dict(orient='records') # current person is sender
    result['emt_rec'] = emt.loc[emt['cust_id_receiver'] == id].to_dict(orient='records') # current person is recipient

    result['wire_sent'] = wire.loc[wire['cust_id_sender'] == id].to_dict(orient='records')
    result['wire_rec'] = wire.loc[wire['cust_id_receiver'] == id].to_dict(orient='records')

    result['cash_dep'] = cash.loc[(cash['type']=='deposit') & (cash['cust_id'] == id)].to_dict(orient='records')
    result['cash_wit'] = cash.loc[(cash['type']=='withdrawal') & (cash['cust_id'] == id)].to_dict(orient='records')

    return jsonify(result)


def make_ego_graph(graph, node, pre_radius, post_radius):
    # don't want out-edges from bank
    graph.remove_edges_from(list(graph.edges('BANK')))

    pre_nodes = nx.generators.ego_graph(graph.reverse(), node, radius=pre_radius, center=False).nodes()
    post_nodes = nx.generators.ego_graph(graph, node, radius=post_radius, center=False).nodes()
    subgraph = nx.induced_subgraph(graph, list(set(pre_nodes).union(set(post_nodes))) + [node])              
    
    return subgraph


# returns nodes and edges as json in the format that vis.js expects it
def networkx_to_json(graph):
    nodes = [{'id': n, 'label': n} for n in graph.nodes()]
    edges = [{'from': u, 'to': v} for u, v in graph.edges()]
    return jsonify(nodes=nodes, edges=edges)


if __name__ == '__main__':
    app.run()
