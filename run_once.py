"""Entrypoint for scheduled environments (e.g. GitHub Actions) that run one
check-and-upload cycle per invocation, instead of main.py's persistent loop."""
import db
import main

db.init_db()
main.run_cycle()
