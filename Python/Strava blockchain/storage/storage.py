import os
import json
import config
from json.decoder import JSONDecodeError

class Storage:
    def __init__(self):
        self.storage_dir = os.path.join(os.path.dirname(__file__), "")
        self.chain_file_path = os.path.join(self.storage_dir, config.CHAIN_FILE_NAME)

    def save_chain(self, chain):
        with open(self.chain_file_path, 'w') as file:
            json.dump(chain, file, indent=4)
        print(f"chain saved to {self.chain_file_path}")

    def load_chain(self):
        try:
            with open(self.chain_file_path, 'r') as file:
                self.chain = json.load(file)
                print("Chain loaded from file.")
                return self.chain
        except FileNotFoundError:
            print("No existing chain found")
            return None
        except JSONDecodeError:
            print("Chain file exists but is empty or corrupted.")
            return None


