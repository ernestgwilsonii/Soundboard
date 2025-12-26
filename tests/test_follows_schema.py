import sqlite3
import os
import pytest
from config import Config

def test_follows_table_exists():
    # Use the accounts DB from config
    db_path = Config.ACCOUNTS_DB
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check if table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='follows'")
    table = cur.fetchone()
    conn.close()
    
    assert table is not None, "Table 'follows' should exist in the accounts database"
