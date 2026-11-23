"""The shop database (SQLite).

On first start we build data/shop.db from the CSV files in "data files/"
(file name = table name). If that folder has no CSVs, a small demo shop is
generated instead, so the app always starts.
"""
import csv
import glob
import os
import random
import sqlite3
import time
from datetime import datetime, timedelta

from app import config

# Columns that look like numbers but must stay text ("02675" is not 2675)
TEXT_COLUMNS = {"postal_code", "sku", "product_sku", "session_id", "ip_address"}
INDEX_COLUMNS = {"order_id", "user_id", "product_id", "status", "created_at", "event_type"}
QUERY_SECONDS = 60  # a guardrail: stop any query that runs longer than this (full events scans take ~20 s)


def clean(value):
    """'' -> NULL, and drop ' UTC' so SQLite date functions work."""
    if value == "":
        return None
    return value[:-4] if value.endswith(" UTC") else value


def load_csv(con, path):
    table = os.path.splitext(os.path.basename(path))[0].lower().replace(" ", "_").replace("-", "_")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        cols = [c.strip().lower() for c in next(reader)]
        types = ["TEXT" if c in TEXT_COLUMNS else "NUMERIC" for c in cols]
        con.execute(f"CREATE TABLE {table} ({', '.join(f'{c} {t}' for c, t in zip(cols, types))})")
        marks = ", ".join("?" * len(cols))
        rows = ([clean(v) for v in row] for row in reader)
        con.executemany(f"INSERT INTO {table} VALUES ({marks})", rows)
    for c in cols:
        if c in INDEX_COLUMNS or c == "id":
            con.execute(f"CREATE INDEX idx_{table}_{c} ON {table}({c})")
    count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  loaded {table}: {count:,} rows", flush=True)


def demo_rows(seed=42):
    rnd = random.Random(seed)
    start = datetime(2023, 1, 1)
    statuses = ["Complete"] * 6 + ["Shipped"] * 2 + ["Returned", "Cancelled"]
    users = [(i, rnd.choice(["United States", "Brasil", "China"]), rnd.randint(18, 70)) for i in range(1, 501)]
    products = []
    for i in range(1, 101):
        price = round(rnd.uniform(10, 150), 2)
        products.append((i, f"Item {i}", rnd.choice(["Jeans", "Tops", "Shoes"]), "Demo",
                         price, round(price * rnd.uniform(0.4, 0.6), 2)))
    orders, items = [], []
    for oid in range(1, 3001):
        day = (start + timedelta(days=rnd.randint(0, 729))).strftime("%Y-%m-%d")
        status = rnd.choice(statuses)
        orders.append((oid, rnd.randint(1, 500), status, day))
        for _ in range(rnd.randint(1, 3)):
            p = rnd.choice(products)
            items.append((len(items) + 1, oid, p[0], status, p[4], day))
    return {
        "users(id, country, age)": users,
        "products(id, name, category, brand, retail_price, cost)": products,
        "orders(order_id, user_id, status, created_at)": orders,
        "order_items(id, order_id, product_id, status, sale_price, created_at)": items,
    }


def build_db():
    if os.path.exists(config.SHOP_DB):
        return
    os.makedirs(config.DATA_DIR, exist_ok=True)
    tmp = config.SHOP_DB + ".building"   # build aside, so a crash never leaves half a database
    if os.path.exists(tmp):
        os.remove(tmp)
    con = sqlite3.connect(tmp)
    csv_files = sorted(p for p in glob.glob(os.path.join(config.CSV_DIR, "*.csv")) if os.path.getsize(p) > 0)
    started = time.time()
    if csv_files:
        print(f"Building shop.db from {len(csv_files)} CSV files in '{config.CSV_DIR}' (first start only)...", flush=True)
        for path in csv_files:
            load_csv(con, path)
    else:
        print(f"No CSV files in '{config.CSV_DIR}', using the small demo shop.", flush=True)
        for table, rows in demo_rows().items():
            con.execute(f"CREATE TABLE {table}")
            marks = ", ".join("?" * len(rows[0]))
            con.executemany(f"INSERT INTO {table.split('(')[0]} VALUES ({marks})", rows)
    con.commit()
    con.close()
    os.replace(tmp, config.SHOP_DB)
    print(f"shop.db ready in {time.time() - started:.0f}s", flush=True)


def connect_read_only():
    con = sqlite3.connect(f"file:{config.SHOP_DB}?mode=ro", uri=True)
    deadline = time.time() + QUERY_SECONDS
    con.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 10_000)
    return con


def query(sql, max_rows=50):
    """Run SQL on a READ-ONLY connection, so the agent can never change data."""
    con = connect_read_only()
    try:
        cur = con.execute(sql)
        cols = [c[0] for c in cur.description or []]
        return cols, cur.fetchmany(max_rows)
    finally:
        con.close()


def schema():
    """Table and column names, as text the LLM can read."""
    con = connect_read_only()
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    lines = []
    for t in tables:
        cols = [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
        lines.append(f"{t}({', '.join(cols)})")
    con.close()
    lines.append("Dates are text like '2023-09-23 08:12:00'; use strftime('%Y', created_at) for the year.")
    return "\n".join(lines)
