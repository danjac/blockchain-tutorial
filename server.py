import uuid

from flask import Flask, jsonify
from webargs import fields
from webargs.flaskparser import use_args

from . import blockchain
from .schema import block_schema

app = Flask(__name__)

node_identifier = str(uuid.uuid4()).replace('-', '')

blockchain = blockchain.Blockchain()

transaction_args = {
    'sender': fields.Str(required=True),
    'recipient': fields.Str(required=True),
    'amount': fields.Int(required=True),
}

register_node_args = {
    'nodes': fields.List(fields.Str(), required=True)
}


@app.route("/mine/", methods=["GET"])
def mine():
    block = blockchain.mine(node_identifier)

    response = {
        'message': "New Block Forged",
        'block': block_schema.dump(block),
    }

    return jsonify(response)


@app.route("/transactions/new/", methods=["POST"])
@use_args(transaction_args)
def new_transaction(args):
    index = blockchain.new_transaction(
        args['sender'],
        args['recipient'],
        args['amount'],
    )

    response = {
        'message': f'Transaction will be added to Block {index}'
    }

    return jsonify(response), 201


@app.route("/chain/", methods=["GET"])
def chain():
    data = block_schema.dump(blockchain.chain, many=True)

    response = {
        'chain': data,
        'length': blockchain.length,
    }
    return jsonify(response)


@app.route("/nodes/", methods=["GET"])
def show_nodes():
    response = {
        "nodes": list(blockchain.nodes)
    }
    return jsonify(response)


@app.route("/nodes/register/", methods=["POST"])
@use_args(register_node_args)
def register_nodes(args):
    for node in args['nodes']:
        blockchain.register_node(node)
    response = {
        'message': 'New nodes added',
        'nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route("/nodes/resolve/", methods=["GET"])
def resolve():
    replaced = blockchain.resolve_conflicts()
    data = block_schema.dump(blockchain.chain, many=True)
    if replaced:
        response = {
            'message': 'Our blockchain was replaced',
            'new_chain': data,
        }
    else:
        response = {
            'message': 'Our blockchain has authoritah',
            'chain': data,
        }
    return jsonify(response)