from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from blockchain import Blockchain
from database import Database
import hashlib
import time
import os

app = Flask(__name__)
app.secret_key = "super_secret_key_for_evoting_2024"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

blockchain = Blockchain(difficulty=3)
db = Database()


class User(UserMixin):
    def __init__(self, user_id, name, email, user_type="voter"):
        self.id = user_id
        self.name = name
        self.email = email
        self.user_type = user_type

    def is_admin(self):
        return self.user_type == "admin"


active_users = {}


@login_manager.user_loader
def load_user(user_id):
    return active_users.get(user_id)


@app.route("/")
def index():
    stats = blockchain.get_statistics()
    elections = db.get_active_elections()
    return render_template("index.html", stats=stats, elections=elections)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        voter_id = request.form.get("voter_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([voter_id, name, email, password]):
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        result = db.register_voter(voter_id, name, email, password)

        if result["success"]:
            voter_hash = hashlib.sha512((voter_id + ":" + email).encode()).hexdigest()
            flash("Registration successful! Your SHA-512 identity hash: " + voter_hash[:32] + "...", "success")
            return redirect(url_for("login"))
        else:
            flash(result["message"], "danger")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        password = request.form.get("password", "")
        login_type = request.form.get("login_type", "voter")

        if not user_id or not password:
            flash("Please enter both ID and password.", "danger")
            return render_template("login.html")

        if login_type == "admin":
            admin = db.authenticate_admin(user_id, password)
            if admin:
                user = User(user_id, admin["name"], "", "admin")
                active_users[user_id] = user
                login_user(user)
                flash("Welcome, Administrator " + admin["name"] + "!", "success")
                return redirect(url_for("admin_dashboard"))
            else:
                flash("Invalid admin credentials.", "danger")
        else:
            voter = db.authenticate_voter(user_id, password)
            if voter:
                user = User(user_id, voter["name"], voter["email"], "voter")
                active_users[user_id] = user
                login_user(user)
                flash("Welcome, " + voter["name"] + "!", "success")
                return redirect(url_for("vote"))
            else:
                flash("Invalid voter credentials.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    if current_user.id in active_users:
        del active_users[current_user.id]
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/vote", methods=["GET", "POST"])
@login_required
def vote():
    if current_user.user_type == "admin":
        flash("Admins cannot vote.", "warning")
        return redirect(url_for("admin_dashboard"))

    elections = db.get_active_elections()

    if request.method == "POST":
        election_id = request.form.get("election_id")
        candidate_id = request.form.get("candidate")

        if not election_id or not candidate_id:
            flash("Please select a candidate.", "danger")
            return render_template("vote.html", elections=elections, voter=db.get_voter(current_user.id))

        if db.has_voter_voted(current_user.id, election_id):
            flash("You have already voted in this election!", "warning")
            return render_template("vote.html", elections=elections, voter=db.get_voter(current_user.id))

        election = db.get_election(election_id)
        if not election:
            flash("Election not found.", "danger")
            return render_template("vote.html", elections=elections, voter=db.get_voter(current_user.id))

        candidate = None
        for c in election["candidates"]:
            if c["id"] == candidate_id:
                candidate = c
                break

        if not candidate:
            flash("Invalid candidate selection.", "danger")
            return render_template("vote.html", elections=elections, voter=db.get_voter(current_user.id))

        voter_hash = blockchain.generate_voter_hash(current_user.id)

        vote_result = blockchain.add_vote(
            voter_id=current_user.id,
            voter_hash=voter_hash,
            candidate=candidate["name"],
            election_id=election_id
        )

        db.mark_voter_voted(current_user.id, election_id, vote_result["receipt_hash"])

        flash(
            "Your vote has been recorded on the blockchain! Receipt Hash: " +
            vote_result["receipt_hash"][:32] + "... (Block #" + str(vote_result["block_index"]) + ")",
            "success"
        )

        return redirect(url_for("vote_success", receipt=vote_result["receipt_hash"]))

    voter = db.get_voter(current_user.id)
    return render_template("vote.html", elections=elections, voter=voter)


@app.route("/vote/success/<receipt>")
@login_required
def vote_success(receipt):
    return render_template("verify.html", receipt=receipt, auto_verify=True)


@app.route("/results")
def results():
    elections = db.get_all_elections()
    results_data = {}

    for election in elections:
        vote_count = blockchain.get_vote_count(election["id"])
        total_votes = sum(vote_count.values())
        total_registered = db.get_total_voters()

        candidates_results = []
        for candidate in election["candidates"]:
            votes = vote_count.get(candidate["name"], 0)
            if total_votes > 0:
                percentage = round(votes / total_votes * 100, 2)
            else:
                percentage = 0
            candidates_results.append({
                "name": candidate["name"],
                "party": candidate["party"],
                "symbol": candidate["symbol"],
                "votes": votes,
                "percentage": percentage
            })

        candidates_results.sort(key=lambda x: x["votes"], reverse=True)

        if total_registered > 0:
            turnout = round(total_votes / total_registered * 100, 2)
        else:
            turnout = 0

        results_data[election["id"]] = {
            "election": election,
            "candidates": candidates_results,
            "total_votes": total_votes,
            "total_registered": total_registered,
            "turnout": turnout
        }

    return render_template("results.html", results_data=results_data)


@app.route("/verify", methods=["GET", "POST"])
def verify():
    result = None
    receipt = request.args.get("receipt", "")

    if request.method == "POST":
        receipt = request.form.get("receipt_hash", "").strip()
        if receipt:
            result = blockchain.verify_vote(receipt)

    return render_template("verify.html", result=result, receipt=receipt)


@app.route("/blockchain")
def blockchain_explorer():
    chain_data = blockchain.get_chain_data()
    validation = blockchain.is_chain_valid()
    stats = blockchain.get_statistics()
    return render_template("blockchain_explorer.html", chain=chain_data, validation=validation, stats=stats)


@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for("index"))

    stats = blockchain.get_statistics()
    elections = db.get_all_elections()
    voters = db.get_all_voters()
    validation = blockchain.is_chain_valid()

    return render_template("admin.html", stats=stats, elections=elections, voters=voters, validation=validation)


@app.route("/admin/toggle_election/<election_id>", methods=["POST"])
@login_required
def toggle_election(election_id):
    if not current_user.is_admin():
        return jsonify({"error": "Unauthorized"}), 403

    result = db.toggle_election(election_id)
    flash(result["message"], "success" if result["success"] else "danger")
    return redirect(url_for("admin_dashboard"))


@app.route("/api/blockchain/status")
def api_blockchain_status():
    return jsonify(blockchain.get_statistics())


@app.route("/api/blockchain/validate")
def api_blockchain_validate():
    return jsonify(blockchain.is_chain_valid())


@app.route("/api/blockchain/chain")
def api_blockchain_chain():
    return jsonify(blockchain.get_chain_data())


@app.route("/api/results/<election_id>")
def api_results(election_id):
    vote_count = blockchain.get_vote_count(election_id)
    return jsonify(vote_count)


@app.route("/api/verify/<receipt_hash>")
def api_verify(receipt_hash):
    result = blockchain.verify_vote(receipt_hash)
    return jsonify(result)


if __name__ == "__main__":
    print("=" * 60)
    print("  Decentralized E-Voting System using SHA-512")
    print("=" * 60)
    print("  Blockchain initialized with difficulty:", blockchain.difficulty)
    print("  Hash Algorithm: SHA-512")
    print("  Genesis Block Hash:", blockchain.chain[0].hash[:64] + "...")
    print("=" * 60)
    print()
    print("  Test Accounts:")
    print("  " + "-" * 40)
    print("  Admin  -> Username: admin    | Password: admin123")
    print("  Voter  -> Voter ID: VOT001   | Password: passVOT001")
    print("  Voter  -> Voter ID: VOT002   | Password: passVOT002")
    print("  Voter  -> Voter ID: VOT003   | Password: passVOT003")
    print("=" * 60)
    print()
    print("  Open browser: http://127.0.0.1:5000")
    print()

    app.run(debug=True, host="0.0.0.0", port=5000)