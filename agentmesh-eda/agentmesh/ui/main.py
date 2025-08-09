from flask import Flask, render_template, request, redirect, url_for
import json
import os
import uuid
from agentmesh.db.database import SessionLocal, Tenant, Message, init_db

app = Flask(__name__)

# TENANTS_FILE = "tenants.json" # No longer needed

# def get_tenants(): # No longer needed
#     if not os.path.exists(TENANTS_FILE):
#         return []
#     with open(TENANTS_FILE, "r") as f:
#         return json.load(f)

@app.before_first_request
def initialize_database():
    init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/tenants", methods=["GET", "POST"])
def tenants():
    db = SessionLocal()
    try:
        if request.method == "POST":
            tenant_name = request.form["tenant_name"]
            existing_tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
            if not existing_tenant:
                new_tenant = Tenant(id=str(uuid.uuid4()), name=tenant_name)
                db.add(new_tenant)
                db.commit()
                db.refresh(new_tenant)
            return redirect(url_for("tenants"))
        tenants = db.query(Tenant).all()
        return render_template("tenants.html", tenants=tenants)
    finally:
        db.close()

@app.route("/status")
def status():
    # In a real application, this would check the health of the messaging system,
    # the agent registry, and other components.
    return render_template("status.html", system_status="OK")

@app.route("/messages")
def messages():
    db = SessionLocal()
    try:
        messages = db.query(Message).all()
        return render_template("messages.html", messages=messages)
    finally:
        db.close()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
