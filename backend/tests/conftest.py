"""
Test bootstrap. The app modules read DATABASE_URL at import time (SQLAlchemy's
create_engine is lazy, so a dummy URL is fine — these tests never touch a DB).
Set it before anything under app/ is imported.
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/test")
os.environ.setdefault("USE_RULE_ANALYSIS", "true")

# Manual scripts against a running server (`python tests/test_profiles.py
# --host ...`), not pytest tests. They replace sys.stdout at import time,
# which closes pytest's capture stream and aborts the whole run before any
# test executes — so pytest must never import them.
collect_ignore = ["test_profiles.py", "test_targeted.py"]
