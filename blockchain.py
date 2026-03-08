import hashlib
import json
import time


class Block:
    def __init__(self, index, transactions, previous_hash, timestamp=None, nonce=0):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha512(block_data).hexdigest()

    def mine_block(self, difficulty):
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        return self.hash

    def to_dict(self):
        return {
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash
        }


class Blockchain:
    def __init__(self, difficulty=3):
        self.chain = []
        self.pending_transactions = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(
            index=0,
            transactions=[{"type": "genesis", "message": "Genesis Block - E-Voting System Started"}],
            previous_hash="0" * 128,
            timestamp=time.time()
        )
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)

    def get_latest_block(self):
        return self.chain[-1]

    def generate_voter_hash(self, voter_id):
        salt = "e_voting_system_2024_secure_salt"
        data = (voter_id + salt + str(time.time())).encode()
        return hashlib.sha512(data).hexdigest()

    def generate_vote_receipt(self, voter_id, candidate, timestamp):
        receipt_data = (voter_id + ":" + candidate + ":" + str(timestamp) + ":receipt_salt_2024").encode()
        return hashlib.sha512(receipt_data).hexdigest()

    def add_vote(self, voter_id, voter_hash, candidate, election_id):
        timestamp = time.time()
        receipt_hash = self.generate_vote_receipt(voter_id, candidate, timestamp)

        transaction = {
            "type": "vote",
            "voter_hash": voter_hash,
            "candidate": candidate,
            "election_id": election_id,
            "timestamp": timestamp,
            "receipt_hash": receipt_hash,
            "vote_hash": hashlib.sha512(
                (voter_hash + candidate + str(timestamp)).encode()
            ).hexdigest()
        }

        self.pending_transactions.append(transaction)
        self.mine_pending_transactions()

        return {
            "receipt_hash": receipt_hash,
            "vote_hash": transaction["vote_hash"],
            "block_index": len(self.chain) - 1,
            "timestamp": timestamp
        }

    def mine_pending_transactions(self):
        if not self.pending_transactions:
            return None

        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.get_latest_block().hash
        )

        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    def is_chain_valid(self):
        validation_report = {
            "is_valid": True,
            "total_blocks": len(self.chain),
            "errors": [],
            "blocks_checked": 0
        }

        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            validation_report["blocks_checked"] += 1

            recalculated_hash = current_block.calculate_hash()
            if current_block.hash != recalculated_hash:
                validation_report["is_valid"] = False
                validation_report["errors"].append(
                    "Block " + str(i) + ": Hash mismatch detected"
                )

            if current_block.previous_hash != previous_block.hash:
                validation_report["is_valid"] = False
                validation_report["errors"].append(
                    "Block " + str(i) + ": Chain linkage broken"
                )

            if current_block.hash[:self.difficulty] != "0" * self.difficulty:
                validation_report["is_valid"] = False
                validation_report["errors"].append(
                    "Block " + str(i) + ": Proof of work invalid"
                )

        return validation_report

    def get_all_votes(self, election_id=None):
        votes = []
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.get("type") == "vote":
                    if election_id is None or transaction.get("election_id") == election_id:
                        votes.append(transaction)
        return votes

    def get_vote_count(self, election_id=None):
        votes = self.get_all_votes(election_id)
        count = {}
        for vote in votes:
            candidate = vote["candidate"]
            if candidate in count:
                count[candidate] = count[candidate] + 1
            else:
                count[candidate] = 1
        return count

    def verify_vote(self, receipt_hash):
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.get("receipt_hash") == receipt_hash:
                    return {
                        "found": True,
                        "candidate": transaction["candidate"],
                        "timestamp": transaction["timestamp"],
                        "block_index": block.index,
                        "block_hash": block.hash,
                        "vote_hash": transaction["vote_hash"]
                    }
        return {"found": False}

    def get_chain_data(self):
        return [block.to_dict() for block in self.chain]

    def get_statistics(self):
        total_votes = len(self.get_all_votes())
        return {
            "total_blocks": len(self.chain),
            "total_votes": total_votes,
            "difficulty": self.difficulty,
            "hash_algorithm": "SHA-512",
            "chain_valid": self.is_chain_valid()["is_valid"],
            "latest_block_hash": self.get_latest_block().hash[:64] + "...",
            "pending_transactions": len(self.pending_transactions)
        }