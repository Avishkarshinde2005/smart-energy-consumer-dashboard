"""
SQLite Database Layer for Smart Waste Management.
Handles schema initialization, CRUD operations for bins and readings,
and data persistence.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
import pandas as pd

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "database", "waste_management.db"
)


class DatabaseManager:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create tables according to TRD Section 4 data models."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Table: bins
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bins (
                    bin_id TEXT PRIMARY KEY,
                    location_name TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    waste_type TEXT,
                    collection_frequency TEXT
                );
            """)

            # Table: bin_readings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bin_readings (
                    reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bin_id TEXT NOT NULL,
                    fill_level REAL NOT NULL,
                    fill_category TEXT,
                    overflow_status BOOLEAN,
                    timestamp DATETIME NOT NULL,
                    FOREIGN KEY (bin_id) REFERENCES bins(bin_id)
                );
            """)

            # Table: priority_scores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS priority_scores (
                    bin_id TEXT PRIMARY KEY,
                    priority_score REAL NOT NULL,
                    rank INTEGER,
                    needs_collection BOOLEAN,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bin_id) REFERENCES bins(bin_id)
                );
            """)

            # Indexes for high performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_bin ON bin_readings(bin_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_ts ON bin_readings(timestamp);")
            conn.commit()

    def insert_bin(self, bin_id: str, location_name: str, latitude: float, longitude: float,
                   waste_type: str = "General", collection_frequency: str = "Daily") -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO bins (bin_id, location_name, latitude, longitude, waste_type, collection_frequency)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (bin_id, location_name, latitude, longitude, waste_type, collection_frequency))
            conn.commit()

    def insert_reading(self, bin_id: str, fill_level: float, fill_category: str,
                       overflow_status: bool, timestamp: str) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO bin_readings (bin_id, fill_level, fill_category, overflow_status, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (bin_id, fill_level, fill_category, int(overflow_status), timestamp))
            conn.commit()

    def bulk_insert_bins(self, bins_data: List[Dict[str, Any]]) -> None:
        with self.get_connection() as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO bins (bin_id, location_name, latitude, longitude, waste_type, collection_frequency)
                VALUES (:bin_id, :location_name, :latitude, :longitude, :waste_type, :collection_frequency)
            """, bins_data)
            conn.commit()

    def bulk_insert_readings(self, readings_data: List[Dict[str, Any]]) -> None:
        with self.get_connection() as conn:
            conn.executemany("""
                INSERT INTO bin_readings (bin_id, fill_level, fill_category, overflow_status, timestamp)
                VALUES (:bin_id, :fill_level, :fill_category, :overflow_status, :timestamp)
            """, readings_data)
            conn.commit()

    def get_latest_readings_df(self) -> pd.DataFrame:
        """
        Query the latest reading for each bin joined with bin metadata.
        """
        query = """
            SELECT 
                b.bin_id,
                b.location_name,
                b.latitude,
                b.longitude,
                b.waste_type,
                b.collection_frequency,
                r.fill_level,
                r.fill_category,
                r.overflow_status,
                r.timestamp
            FROM bins b
            INNER JOIN bin_readings r ON b.bin_id = r.bin_id
            WHERE r.reading_id = (
                SELECT r2.reading_id FROM bin_readings r2
                WHERE r2.bin_id = b.bin_id
                ORDER BY r2.timestamp DESC, r2.reading_id DESC
                LIMIT 1
            )
            ORDER BY r.fill_level DESC;
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn)

    def get_all_readings_df(self) -> pd.DataFrame:
        query = """
            SELECT 
                r.reading_id,
                b.bin_id,
                b.location_name,
                b.latitude,
                b.longitude,
                b.waste_type,
                b.collection_frequency,
                r.fill_level,
                r.fill_category,
                r.overflow_status,
                r.timestamp
            FROM bin_readings r
            JOIN bins b ON r.bin_id = b.bin_id
            ORDER BY r.timestamp ASC;
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn)

    def save_priority_scores(self, scored_df: pd.DataFrame) -> None:
        with self.get_connection() as conn:
            records = []
            for _, row in scored_df.iterrows():
                records.append({
                    "bin_id": row["bin_id"],
                    "priority_score": float(row.get("priority_score", 0.0)),
                    "rank": int(row.get("rank", 0)),
                    "needs_collection": int(row.get("needs_collection", 0))
                })
            conn.executemany("""
                INSERT OR REPLACE INTO priority_scores (bin_id, priority_score, rank, needs_collection)
                VALUES (:bin_id, :priority_score, :rank, :needs_collection)
            """, records)
            conn.commit()
