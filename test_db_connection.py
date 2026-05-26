import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))


def get_conn():
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        autocommit=False,
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
    )


if __name__ == "__main__":
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT rb.batchID, rb.roastDate, qc.cuppingScore, b.beanName
            FROM RoastingBatch rb
            JOIN BeanLot bl     ON bl.lotID  = rb.lotID
            JOIN CoffeeBean b   ON b.beanID  = bl.beanID
            JOIN QualityControlRecord qc ON qc.batchID = rb.batchID
            LIMIT 5
        """)
        for row in cur.fetchall():
            print(row)
    finally:
        cur.close()
        conn.close()
