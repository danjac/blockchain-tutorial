import time
import json
import hashlib
import requests

from urllib.parse import urlparse


class Transaction:

    def __init__(self, sender, recipient, amount):
        """
        :param sender: <str> ID of sender
        :param recipient: <str> ID of recipient
        :param amount: <int> value
        """
        self.sender = sender
        self.recipient = recipient
        self.amount = amount


class Block:

    def __init__(self, index, proof, previous_hash, transactions):
        """
        :param index: <int> index in chain
        :param proof: <int> Proof-of-Work
        :param previous_hash: <str> hash of previous block in chain
        :param transactions: <list> list of previous Transactions
        """
        self.index = index
        self.proof = proof
        self.previous_hash = previous_hash
        self.transactions = transactions or []
        self.timestamp = time.time()

    def hash(self):
        """
        Creates an SHA-256 hash of the block
        :return: <str> hash of block
        """
        data = {
            "index": self.index,
            "proof": self.proof,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": [
                {
                    "sender": t.sender,
                    "recipient": t.recipient,
                    "amount": t.amount,
                } for t in self.transactions
            ]
        }

        block_string = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def check(self, last_block):
        """
        Checks if valid (hash and proof correct)

        :param last_block Block
        :return: <bool>
        """
        return Blockchain.valid_proof(
            last_block.proof,
            self.proof
        ) and self.previous_hash == last_block.hash()


class Blockchain:

    def __init__(self):
        self.chain = []
        self.current_transactions = []

        self.nodes = set()

        # generate the new block
        self.new_block(previous_hash=1, proof=100)

    def register_node(self, address):
        """
        Add a new node to list of nodes

        :param address: <str> Address of node
        """

        location = urlparse(address).netloc
        if location:
            self.nodes.add(location)

    def mine(self, node_identifier):
        """
        Mines a new block
        :return: a new Block instance
        """

        last_block = self.last_block
        proof = self.proof_of_work(last_block.proof)

        # reward for finding new proof
        self.new_transaction(
            sender="0",
            recipient=node_identifier,
            amount=1,
        )

        # forge new Block by adding it to the chain
        block = self.new_block(proof, last_block.hash())

        # call all other nodes
        for node in self.nodes:
            requests.get(f'http://{node}/nodes/resolve/')
        return block

    def resolve_conflicts(self):
        """
        Consensus Algorithm, it resolves conflicts by replacing our chain
        with the longest one in the network.

        :return: <bool> if chain replaced
        """

        max_length = len(self.chain)
        new_chain = None

        for node in self.nodes:
            response = requests.get(f'http://{node}/chain/')
            if not response.ok:
                print(f'Invalid response from node {node}')
                continue
            payload = response.json()
            length = payload['length']
            chain = payload['chain']
            if length > max_length and self.valid_chain(chain):
                max_length = length
                new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True
        return False

    def proof_of_work(self, last_proof):
        """
        Simple POW algorithm:
        - Find a number p' such that hash(pp') contains 4 leading zeroes,
            p is the previous p', p is previous proof, p' the new proof

        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @property
    def length(self):
        return len(self.chain)

    def new_block(self, proof, previous_hash=None):
        """
        Creates a new Block in the Blockchain

        :param proof: <int> Proof given in the Proof of Work algorithm
        :param previous_hash: (Optional) Hash of previous block
        :return: Block: new block
        """

        block = Block(
            index=self.length + 1,
            transactions=self.current_transactions,
            proof=proof,
            previous_hash=previous_hash or self.last_block.hash(),
        )

        # reset transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: <str> Address of Sender
        :param recipient: <str> Address of Recipient
        :param amount: <int> Amount
        :return: <int> Index of the Block that will hold this transaction
        """
        transaction = Transaction(sender, recipient, amount)
        self.current_transactions.append(transaction)
        return self.last_block.index + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: does hash(last_proof, proof) contain 4 leading
        zeroes?

        :param last_proof: <int> Previous proof
        :param proof: Current proof
        :return: <bool>
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @staticmethod
    def valid_chain(chain):
        """
        Determine if a block chain is valid

        :param chain: <list> A blockchain
        :return: <bool>
        """

        last_block = None

        for block in chain:

            if last_block:

                print(last_block)
                print(block)
                print('\n----------------------\n')
                if not block.check(last_block):
                    return False

            last_block = block

        return True
