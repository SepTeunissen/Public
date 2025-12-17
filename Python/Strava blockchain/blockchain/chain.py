import datetime,hashlib,json
import api.strava_api as strava_api
import storage.storage as storage
from flask import jsonify

class Class_Blockchain:

    def __init__(self):
        self.storage = storage.Storage()

        loaded_chain = self.storage.load_chain()

        if loaded_chain:
            self.chain = loaded_chain
            print("Loaded existing chain from file.")
        else:
            print("No existing chain found, creating new one.")
            self.chain = []
            self.initialize_chain()

    def initialize_chain(self):
            all_activities = strava_api.Class_StravaClient().get_all_activities()
            previous_hash = '0'
            index = 1
            for activity in all_activities:
                block = {
                    'index': index,
                    'timestamp': str(datetime.datetime.now()),
                    'proof': 1,
                    'previous_hash': previous_hash,
                    'data': activity
                }
                self.chain.append(block)

                previous_hash = self.hash(block)
                index += 1

    def create_block(self, proof, previous_hash, data):

        block = {'index': len(self.chain) + 1,
                'timestamp': str(datetime.datetime.now()),
                'proof': proof,
                'previous_hash': previous_hash,
                'data': data}

        self.chain.append(block)

        self.storage.save_chain(self.chain)

        return block

    def print_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False

        while check_proof is False:
            hash_operation = hashlib.sha256(
                str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:5] == '00000':
                check_proof = True
            else:
                new_proof += 1

        return new_proof
    @staticmethod
    def hash(block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1

        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False

            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(
                str(proof**2 - previous_proof**2).encode()).hexdigest()

            if hash_operation[:5] != '00000':
                return False
            previous_block = block
            block_index += 1

        return True

    def mine_block(self, data=None):
        previous_block = self.print_previous_block()
        previous_proof = previous_block['proof']
        proof = self.proof_of_work(previous_proof)
        previous_hash = self.hash(previous_block)
        block = self.create_block(proof, previous_hash, data)

        response = {
                    'index': block['index'],
                    'timestamp': block['timestamp'],
                    'proof': block['proof'],
                    'previous_hash': block['previous_hash'],
                    'data': block['data']}

        return jsonify(response), 200
