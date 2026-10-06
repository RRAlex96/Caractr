"""
Test bootstrap. The app modules read DATABASE_URL at import time (SQLAlchemy's
create_engine is lazy, so a dummy URL is fine — these tests never touch a DB).
Set it before anything under app/ is imported.
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/test")
os.environ.setdefault("USE_RULE_ANALYSIS", "true")
