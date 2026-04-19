from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import traceback
import sys

# ── Imports ────────────────────────────────────────────────
try:
    from main_ import BankSystem, initialize_tables, Account
    from Database import connect_to_database
    print("[OK] Imports successful")
except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

app = Flask(__name__)
CORS(app)

FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Init DB ────────────────────────────────────────────────
try:
    initialize_tables()
    bank = BankSystem()
    print("[OK] Database ready")
except Exception as e:
    print(f"[ERROR] DB init failed: {e}")
    traceback.print_exc()
    sys.exit(1)


# ── Log every request ──────────────────────────────────────
@app.after_request
def log_request(response):
    print(f"  {request.method} {request.path} => {response.status_code}")
    return response

# ── Global error handler ───────────────────────────────────
@app.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500


# ── Timestamp helper ───────────────────────────────────────
def fix_ts(log):
    ts = log.get("timestamp")
    if ts and hasattr(ts, "strftime"):
        log["timestamp"] = ts.strftime("%Y-%m-%d %H:%M:%S")
    return log


# ── Serve frontend files ───────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ── API: Signup ────────────────────────────────────────────
@app.route("/api/signup", methods=["POST"])
def signup():
    try:
        d    = request.get_json(force=True, silent=True) or {}
        name = (d.get("name") or "").strip()
        pin  = (d.get("pin")  or "").strip()
        print(f"  [signup] name={name} pin={pin}")

        if not name:
            return jsonify({"error": "Name is required."}), 400
        if len(pin) != 4 or not pin.isdigit():
            return jsonify({"error": "PIN must be exactly 4 digits."}), 400

        acct = bank.create_account(name, pin)
        if not acct:
            return jsonify({"error": "Could not create account."}), 500

        return jsonify({
            "account_number": acct.get_account_number(),
            "name":           acct.get_name(),
            "balance":        float(acct.get_balance()),
        }), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── API: Login ─────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    try:
        d   = request.get_json(force=True, silent=True) or {}
        num = (d.get("account_number") or "").strip().upper()
        pin = (d.get("pin")            or "").strip()
        print(f"  [login] num={num} pin={pin}")

        acct = bank.read_account(num, pin)
        if not acct:
            return jsonify({"error": "Invalid account number or PIN."}), 401

        return jsonify({
            "account_number": acct.get_account_number(),
            "name":           acct.get_name(),
            "balance":        float(acct.get_balance()),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── API: Deposit ───────────────────────────────────────────
@app.route("/api/deposit", methods=["POST"])
def deposit():
    try:
        d      = request.get_json(force=True, silent=True) or {}
        num    = (d.get("account_number") or "").strip().upper()
        pin    = (d.get("pin")            or "").strip()
        amount = float(d.get("amount", 0))
        print(f"  [deposit] num={num} amount={amount}")

        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero."}), 400
        if not bank.deposit(num, pin, amount):
            return jsonify({"error": "Deposit failed. Check credentials."}), 400

        acct = Account.load_from_db(num, pin)
        return jsonify({
            "balance": float(acct.get_balance()) if acct else 0.0,
            "message": f"${amount:.2f} deposited successfully."
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── API: Withdraw ──────────────────────────────────────────
@app.route("/api/withdraw", methods=["POST"])
def withdraw():
    try:
        d      = request.get_json(force=True, silent=True) or {}
        num    = (d.get("account_number") or "").strip().upper()
        pin    = (d.get("pin")            or "").strip()
        amount = float(d.get("amount", 0))
        print(f"  [withdraw] num={num} amount={amount}")

        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero."}), 400
        if not bank.withdraw(num, pin, amount):
            return jsonify({"error": "Insufficient funds or wrong credentials."}), 400

        acct = Account.load_from_db(num, pin)
        return jsonify({
            "balance": float(acct.get_balance()) if acct else 0.0,
            "message": f"${amount:.2f} withdrawn successfully."
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── API: Update account ────────────────────────────────────
@app.route("/api/update", methods=["POST"])
def update():
    try:
        d        = request.get_json(force=True, silent=True) or {}
        num      = (d.get("account_number") or "").strip().upper()
        pin      = (d.get("pin")            or "").strip()
        new_name = (d.get("new_name")       or "").strip()
        new_pin  = (d.get("new_pin")        or "").strip()

        acct = Account.load_from_db(num, pin)
        if not acct:
            return jsonify({"error": "Invalid credentials."}), 401
        if new_name:
            acct.set_name(new_name)
        if new_pin:
            if len(new_pin) != 4 or not new_pin.isdigit():
                return jsonify({"error": "New PIN must be 4 digits."}), 400
            acct.set_pin(new_pin)
        if bank.update_account(acct):
            return jsonify({"message": "Account updated successfully."})
        return jsonify({"error": "Update failed."}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── API: Delete account ────────────────────────────────────
@app.route("/api/delete", methods=["POST"])
def delete():
    try:
        d   = request.get_json(force=True, silent=True) or {}
        num = (d.get("account_number") or "").strip().upper()
        pin = (d.get("pin")            or "").strip()

        if not bank.delete_account(num, pin):
            return jsonify({"error": "Deletion failed. Check credentials."}), 400
        return jsonify({"message": "Account deleted successfully."})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── API: Transactions ──────────────────────────────────────
@app.route("/api/transactions", methods=["POST"])
def transactions():
    try:
        d    = request.get_json(force=True, silent=True) or {}
        num  = (d.get("account_number") or "").strip().upper()
        logs = [fix_ts(l) for l in bank.get_audit_logs(num)]
        return jsonify({"logs": logs})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── API: Admin logs ────────────────────────────────────────
@app.route("/api/admin/logs", methods=["GET"])
def admin_logs():
    try:
        logs = [fix_ts(l) for l in bank.get_all_audit_logs()]
        return jsonify({"logs": logs})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── API: Admin stats ───────────────────────────────────────
@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    try:
        total_accounts = 0
        conn = connect_to_database()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM accounts")
            total_accounts = cur.fetchone()[0]
            cur.close()
            conn.close()

        logs        = bank.get_all_audit_logs()
        deposits    = sum(float(l["amount"]) for l in logs if "deposit"  in l["action"].lower())
        withdrawals = sum(float(l["amount"]) for l in logs if "withdraw" in l["action"].lower())

        return jsonify({
            "total_accounts":    total_accounts,
            "total_deposits":    deposits,
            "total_withdrawals": withdrawals,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── Run ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 45)
    print("  MudraBank server running!")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("=" * 45)
    app.run(debug=True, port=5000)