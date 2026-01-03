import sqlite3
import pandas as pd
from typing import Optional, List, Any

# --- Database & Schema Setup ---
def setup_db(db_name: str = ':memory:') -> sqlite3.Connection:
    conn = sqlite3.connect(db_name)
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS Customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT,
            segment TEXT
        );

        CREATE TABLE IF NOT EXISTS Orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date DATE,
            amount DECIMAL(10, 2),
            FOREIGN KEY(customer_id) REFERENCES Customers(customer_id)
        );
        
        DELETE FROM Orders;
        DELETE FROM Customers;

        INSERT INTO Customers VALUES 
        (1, 'Alpha Corp', 'EU', 'Corporate'),
        (2, 'Beta Ltd', 'US', 'SME'),
        (3, 'Gamma Inc', 'EU', 'Corporate'),
        (4, 'Delta LLC', 'Asia', 'SME');

        INSERT INTO Orders VALUES 
        (101, 1, '2023-01-15', 5000.00),
        (102, 2, '2023-01-20', 1500.00),
        (103, 1, '2023-02-10', 6000.00),
        (104, 3, '2023-02-15', 12000.00),
        (105, 4, '2023-03-05', 800.00),
        (106, 2, '2023-03-10', 2000.00),
        (107, 1, '2023-03-25', 5500.00);
    ''')
    conn.commit()
    return conn

# --- Analysis Helper ---
def run_query(conn: sqlite3.Connection, description: str, sql: str) -> None:
    print(f"\n--- {description} ---")
    print(pd.read_sql_query(sql, conn).to_string(index=False))

# --- Main Execution ---
if __name__ == "__main__":
    conn = setup_db()
    
    # 1. Aggregation
    run_query(conn, "Total Revenue by Region", '''
        SELECT region, SUM(amount) as total_revenue
        FROM Customers c JOIN Orders o ON c.customer_id = o.customer_id
        GROUP BY region ORDER BY total_revenue DESC;
    ''')

    # 2. Window Function 
    run_query(conn, "Avg Order Value (Window Func)", '''
        SELECT c.name, o.amount,
            AVG(o.amount) OVER (PARTITION BY c.customer_id) as avg_spend,
            o.amount - AVG(o.amount) OVER (PARTITION BY c.customer_id) as diff
        FROM Customers c JOIN Orders o ON c.customer_id = o.customer_id;
    ''')

    # 3. CTE & Date Math 
    run_query(conn, "MoM Growth (CTE)", '''
        WITH MonthlyStats AS (
            SELECT strftime('%Y-%m', order_date) as month, SUM(amount) as revenue
            FROM Orders GROUP BY month
        )
        SELECT curr.month, 
               curr.revenue as curr_rev, 
               prev.revenue as prev_rev,
               ROUND((curr.revenue - prev.revenue) * 100.0 / prev.revenue, 1) as growth_pct
        FROM MonthlyStats curr
        LEFT JOIN MonthlyStats prev ON 
            date(curr.month || '-01') = date(prev.month || '-01', '+1 month');
    ''')
    
    conn.close()
