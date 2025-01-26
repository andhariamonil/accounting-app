import os
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Get the database URL from the environment variable (defaults to 'accounting.db' if not set)
DATABASE_URL = os.path.join(os.getcwd(), os.getenv('DATABASE_URL', 'accounting.db'))


# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT name FROM accounts WHERE id = ?", (account_id,))
    account = c.fetchone()
    conn.close()
    return account[0] if account else 'Unknown'

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()

    # Fetch accounts
    c.execute("SELECT * FROM accounts")
    accounts = c.fetchall()

    transactions = []
    start_date = None
    end_date = None
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Fetch transactions within the date range
        c.execute('''SELECT * FROM transactions 
                     WHERE date BETWEEN ? AND ?''', 
                     (start_date, end_date))
        transactions = c.fetchall()

    # Calculate debt summary
    c.execute('''SELECT a1.name AS from_account, 
                        a2.name AS to_account, 
                        SUM(CASE WHEN t.from_account = a1.id THEN t.amount ELSE -t.amount END) AS balance
                 FROM accounts a1
                 JOIN accounts a2 ON a1.id != a2.id
                 LEFT JOIN transactions t ON (t.from_account = a1.id AND t.to_account = a2.id) 
                                         OR (t.from_account = a2.id AND t.to_account = a1.id)
                 GROUP BY a1.name, a2.name
                 HAVING balance > 0''')
    debt_summary = c.fetchall()

    conn.close()

    return render_template(
        'index3.html',
        accounts=accounts,
        transactions=transactions,
        debt_summary=debt_summary,
        get_account_name=get_account_name,
        start_date=start_date,  # Pass start_date and end_date to preserve them
        end_date=end_date
    )

@app.route('/add_account', methods=['POST'])
def add_account():
    account_name = request.form['account_name']
    if account_name:
        conn = sqlite3.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("INSERT INTO accounts (name) VALUES (?)", (account_name,))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_account/<int:account_id>')
def delete_account(account_id):
    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE from_account = ? OR to_account = ?", (account_id, account_id))
    c.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
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

    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('''INSERT INTO transactions (date, from_account, to_account, amount, remark) 
                 VALUES (?, ?, ?, ?, ?)''', 
              (date, from_account, to_account, amount, remark))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_transaction', methods=['POST'])
def delete_transaction():
    transaction_ids = request.form.getlist('transaction_ids')  # Get a list of selected transaction IDs

    if transaction_ids:
        conn = sqlite3.connect(DATABASE_URL)
        c = conn.cursor()
        c.executemany("DELETE FROM transactions WHERE id = ?", [(int(tid),) for tid in transaction_ids])
        conn.commit()
        conn.close()

    return redirect(url_for('index'))

@app.route('/ledger_report', methods=['GET', 'POST'])
def ledger_report():
    conn = sqlite3.connect(DATABASE_URL)
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
        c.execute("SELECT name FROM accounts WHERE id = ?", (account_id,))
        account_name = c.fetchone()[0]  # Fetch the account name

        # Query to get ledger data for the selected account and date range
        c.execute('''SELECT t.date, 
                            SUM(CASE WHEN t.from_account = ? THEN t.amount ELSE 0 END) AS money_sent,
                            SUM(CASE WHEN t.to_account = ? THEN t.amount ELSE 0 END) AS money_received
                     FROM transactions t
                     WHERE t.date BETWEEN ? AND ? 
                     AND (t.from_account = ? OR t.to_account = ?)
                     GROUP BY t.date
                     ORDER BY t.date''', 
                  (account_id, account_id, start_date, end_date, account_id, account_id))

        ledger_data = c.fetchall()
        conn.close()

    return render_template(
        'ledger_report.html',
        accounts=accounts,
        ledger_data=ledger_data,
        account_name=account_name  # Pass the account name here
    )

@app.route('/account_summary', methods=['GET', 'POST'])
def account_summary():
    conn = sqlite3.connect(DATABASE_URL)
    c = conn.cursor()

    # Fetch accounts
    c.execute("SELECT * FROM accounts")
    accounts = c.fetchall()

    report_data = None
    selected_account_name = None
    if request.method == 'POST':
        account_id = request.form['account_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Get account name from the selected account_id
        c.execute("SELECT name FROM accounts WHERE id = ?", (account_id,))
        selected_account_name = c.fetchone()[0]  # Fetch the account name

        # Query to get account summary data for the selected account and date range
        c.execute('''SELECT a2.name AS other_account,
                            SUM(CASE WHEN t.from_account = ? AND t.to_account = a2.id THEN t.amount ELSE 0 END) AS money_sent,
                            SUM(CASE WHEN t.to_account = ? AND t.from_account = a2.id THEN t.amount ELSE 0 END) AS money_received
                     FROM transactions t
                     JOIN accounts a2 ON a2.id != ?
                     WHERE t.date BETWEEN ? AND ? 
                     AND (t.from_account = ? OR t.to_account = ?)
                     GROUP BY a2.name''', 
                  (account_id, account_id, account_id, start_date, end_date, account_id, account_id))

        report_data = c.fetchall()
        conn.close()

    return render_template(
        'account_summary_report.html',
        accounts=accounts,
        report_data=report_data,
        selected_account_name=selected_account_name,  # Pass the selected account name here
    )

if __name__ == '__main__':
    init_db()
   port = int(os.environ.get("PORT", 10000))  # Default port is 10000 if not set by Render
   app.run(host="0.0.0.0", port=port, debug=True)