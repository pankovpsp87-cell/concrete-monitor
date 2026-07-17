# -*- coding: utf-8 -*-
import sqlite3
import datetime
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.path.join(os.path.dirname(__file__), "prices.db")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase_client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    # SQLite initialization
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            url TEXT NOT NULL,
            product_name TEXT NOT NULL,
            grade TEXT,
            price REAL,
            currency TEXT DEFAULT 'UAH',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_price(company, url, product_name, grade, price, timestamp=None):
    # SQLite Insert
    conn = get_connection()
    cursor = conn.cursor()
    now = timestamp or datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO prices (company, url, product_name, grade, price, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (company, url, product_name, grade, price, now))
    conn.commit()
    conn.close()

    # Supabase Insert (if configured)
    if supabase_client:
        try:
            supabase_client.table("prices").insert({
                "company": company,
                "url": url,
                "product_name": product_name,
                "grade": grade,
                "price": float(price),
                "timestamp": now
            }).execute()
            print(f"  [Supabase] Price inserted for {company} ({grade}).")
        except Exception as e:
            print(f"  [Supabase] ERR inserting price for {company}: {e}")

def get_prices():
    # Fetch from Supabase if client is available
    if supabase_client:
        try:
            response = supabase_client.table("prices").select("*").order("timestamp", desc=True).execute()
            df = pd.DataFrame(response.data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Convert id column to int
                df['id'] = df['id'].astype(int)
            return df
        except Exception as e:
            print(f"Failed to fetch from Supabase: {e}. Falling back to SQLite.")

    # SQLite fallback
    if not os.path.exists(DB_NAME):
        return pd.DataFrame()
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM prices ORDER BY timestamp DESC", conn)
    conn.close()
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def delete_price(row_id):
    # SQLite delete
    conn = get_connection()
    conn.execute("DELETE FROM prices WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()

    # Supabase delete
    if supabase_client:
        try:
            supabase_client.table("prices").delete().eq("id", int(row_id)).execute()
            print(f"Deleted row {row_id} from Supabase.")
        except Exception as e:
            print(f"Failed to delete row {row_id} from Supabase: {e}")

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
