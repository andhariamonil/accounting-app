import psycopg2
from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# Set up the PostgreSQL connection using the database URL provided by Render
DATABASE_URL = os.environ.get("DATABASE_URL", "your_postgresql_connection_url_here")

# Initialize PostgreSQL database
def init_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()

    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    date TEXT NOT NULL,
                    from_account INTEGER,
                    to_account INTEGER,
                    amount REAL,
                    remark TEXT,
                    FOREIGN KEY(from_account) REFERENCES accounts(id),
                    FOREIGN KEY(to_account) REFERENCES accounts(id))''')
    conn.commit()
    conn.close()

# Get account name from the account ID
def get_account_name(account_id):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("SELECT name FROM accounts WHERE id = %s", (account_id,))
    account = c.fetchone()
    conn.close()
    return account[0] if account else 'Unknown'

@app.route('/')
def index():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()

    # Fetch accounts
    c.execute("SELECT * FROM accounts")
    accounts = c.fetchall()

    # Fetch transactions
    c.execute("SELECT * FROM transactions")
    transactions = c.fetchall()

    # Calculate debt summary
    c.execute('''
        SELECT a1.name AS from_account, 
               a2.name AS to_account, 
               SUM(CASE WHEN t.from_account = a1.id THEN t.amount ELSE -t.amount END) AS balance
        FROM accounts a1
        JOIN accounts a2 ON a1.id != a2.id
        LEFT JOIN transactions t ON (t.from_account = a1.id AND t.to_account = a2.id) 
                                OR (t.from_account = a2.id AND t.to_account = a1.id)
        GROUP BY a1.name, a2.name
        HAVING balance > 0
    ''')
    debt_summary = c.fetchall()

    conn.close()

    return render_template(
        'index3.html',
        accounts=accounts,
        transactions=transactions,
        debt_summary=debt_summary,
        get_account_name=get_account_name,
    )

@app.route('/add_account', methods=['POST'])
def add_account():
    account_name = request.form['account_name']
    if account_name:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        c = conn.cursor()
        c.execute("INSERT INTO accounts (name) VALUES (%s)", (account_name,))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_account/<int:account_id>')
def delete_account(account_id):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE from_account = %s OR to_account = %s", (account_id, account_id))
    c.execute("DELETE FROM accounts WHERE id = %s", (account_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    date = request.form['date']
    from_account = request.form['from_account']
    to_account = request.form['to_account']
    amount = float(request.form['amount'])
    remark = request.form['remark']

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute('''INSERT INTO transactions (date, from_account, to_account, amount, remark) 
                 VALUES (%s, %s, %s, %s, %s)''', 
              (date, from_account, to_account, amount, remark))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_transaction/<int:transaction_id>')
def delete_transaction(transaction_id):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/ledger_report', methods=['GET', 'POST'])
def ledger_report():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()

    # Fetch accounts
    c.execute("SELECT * FROM accounts")
    accounts = c.fetchall()

    ledger_data = None
    account_name = None

    if request.method == 'POST':
        account_id = request.form['account_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Get account name from the selected account_id
        c.execute("SELECT name FROM accounts WHERE id = %s", (account_id,))
        account_name = c.fetchone()[0]  # Fetch the account name

        # Query to get ledger data for the selected account and date range
        c.execute('''
            SELECT t.date, 
                   SUM(CASE WHEN t.from_account = %s THEN t.amount ELSE 0 END) AS money_sent,
                   SUM(CASE WHEN t.to_account = %s THEN t.amount ELSE 0 END) AS money_received
            FROM transactions t
            WHERE t.date BETWEEN %s AND %s
            AND (t.from_account = %s OR t.to_account = %s)
            GROUP BY t.date
            ORDER BY t.date
        ''', (account_id, account_id, start_date, end_date, account_id, account_id))

        ledger_data = c.fetchall()
        conn.close()

    return render_template(
        'ledger_report.html',
        accounts=accounts,
        ledger_data=ledger_data,
        account_name=account_name  # Pass the account name here
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
