import hashlib
import time


class Database:
    def __init__(self):
        self.voters = {}
        self.elections = {}
        self.admins = {}
        self.vote_records = {}
        self.setup_default_data()

    def setup_default_data(self):
        # Create admin account
        admin_password_hash = hashlib.sha512("admin123".encode()).hexdigest()
        self.admins["admin"] = {
            "username": "admin",
            "password_hash": admin_password_hash,
            "name": "System Administrator",
            "created_at": time.time()
        }

        # Create default election
        self.elections["election_2024"] = {
            "id": "election_2024",
            "title": "Presidential Election 2024",
            "description": "Vote for the next president of the Student Council.",
            "candidates": [
                {
                    "id": "candidate_1",
                    "name": "Alice Johnson",
                    "party": "Progress Party",
                    "symbol": "🌟",
                    "manifesto": "Focus on technology and innovation in education."
                },
                {
                    "id": "candidate_2",
                    "name": "Bob Smith",
                    "party": "Unity Alliance",
                    "symbol": "🤝",
                    "manifesto": "Building bridges between communities for a stronger union."
                },
                {
                    "id": "candidate_3",
                    "name": "Carol Williams",
                    "party": "Green Future",
                    "symbol": "🌿",
                    "manifesto": "Sustainable development and environmental protection."
                },
                {
                    "id": "candidate_4",
                    "name": "David Brown",
                    "party": "Peoples Voice",
                    "symbol": "📢",
                    "manifesto": "Empowering citizens through transparency and accountability."
                }
            ],
            "start_time": time.time(),
            "end_time": time.time() + (30 * 24 * 60 * 60),
            "is_active": True,
            "created_at": time.time()
        }

        # Create test voters
        test_voters = [
            ("VOT001", "John Doe", "john@example.com"),
            ("VOT002", "Jane Smith", "jane@example.com"),
            ("VOT003", "Mike Wilson", "mike@example.com"),
            ("VOT004", "Sarah Davis", "sarah@example.com"),
            ("VOT005", "Tom Anderson", "tom@example.com"),
        ]

        for voter_id, name, email in test_voters:
            password_hash = hashlib.sha512(("pass" + voter_id).encode()).hexdigest()
            self.voters[voter_id] = {
                "voter_id": voter_id,
                "name": name,
                "email": email,
                "password_hash": password_hash,
                "has_voted": {},
                "registered_at": time.time(),
                "is_verified": True
            }

    def register_voter(self, voter_id, name, email, password):
        if voter_id in self.voters:
            return {"success": False, "message": "Voter ID already registered."}

        for v in self.voters.values():
            if v["email"] == email:
                return {"success": False, "message": "Email already registered."}

        password_hash = hashlib.sha512(password.encode()).hexdigest()

        self.voters[voter_id] = {
            "voter_id": voter_id,
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "has_voted": {},
            "registered_at": time.time(),
            "is_verified": True
        }

        return {"success": True, "message": "Registration successful!"}

    def authenticate_voter(self, voter_id, password):
        voter = self.voters.get(voter_id)
        if not voter:
            return None

        password_hash = hashlib.sha512(password.encode()).hexdigest()
        if voter["password_hash"] == password_hash:
            return voter
        return None

    def authenticate_admin(self, username, password):
        admin = self.admins.get(username)
        if not admin:
            return None

        password_hash = hashlib.sha512(password.encode()).hexdigest()
        if admin["password_hash"] == password_hash:
            return admin
        return None

    def has_voter_voted(self, voter_id, election_id):
        voter = self.voters.get(voter_id)
        if not voter:
            return False
        return voter["has_voted"].get(election_id, False)

    def mark_voter_voted(self, voter_id, election_id, receipt_hash):
        if voter_id in self.voters:
            self.voters[voter_id]["has_voted"][election_id] = True
            self.vote_records[voter_id] = receipt_hash

    def get_voter(self, voter_id):
        return self.voters.get(voter_id)

    def get_all_voters(self):
        return list(self.voters.values())

    def get_voter_receipt(self, voter_id):
        return self.vote_records.get(voter_id)

    def get_election(self, election_id):
        return self.elections.get(election_id)

    def get_all_elections(self):
        return list(self.elections.values())

    def get_active_elections(self):
        current_time = time.time()
        result = []
        for e in self.elections.values():
            if e["is_active"] and e["start_time"] <= current_time <= e["end_time"]:
                result.append(e)
        return result

    def toggle_election(self, election_id):
        election = self.elections.get(election_id)
        if not election:
            return {"success": False, "message": "Election not found."}

        election["is_active"] = not election["is_active"]
        if election["is_active"]:
            status = "activated"
        else:
            status = "deactivated"
        return {"success": True, "message": "Election " + status + " successfully!"}

    def get_total_voters(self):
        return len(self.voters)

    def get_voters_who_voted(self, election_id):
        count = 0
        for voter in self.voters.values():
            if voter["has_voted"].get(election_id, False):
                count = count + 1
        return count