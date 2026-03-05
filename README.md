# 📊 Accounting Transaction Manager

A simple **Flask-based accounting web application** that helps manage accounts, record transactions, track debts, and generate financial reports.  
The application uses **SQLite** for data storage and provides an easy interface for managing financial records.

---

## 🚀 Features

- Create and manage accounts
- Record transactions between accounts
- Delete accounts and transactions
- View transaction history within a date range
- Generate **Ledger Reports**
- Generate **Account Summary Reports**
- Automatic **Debt Summary Calculation**
- SQLite database for lightweight storage

---

## 🛠️ Tech Stack

- Backend: Flask (Python Web Framework)
- Database: SQLite
- Frontend: HTML, CSS (Flask Templates)
- Language: Python

---

## 📂 Project Structure

```
project/
│
├── app.py
├── accounting.db
├── templates/
│   ├── index3.html
│   ├── ledger_report.html
│   └── account_summary_report.html
│
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the repository

```
git clone https://github.com/your-username/repository-name.git
```

### 2. Navigate to project folder

```
cd repository-name
```

### 3. Install dependencies

```
pip install flask
```

---

## ▶️ Running the Application

Run the application using:

```
python app.py
```

The application will start at:

```
http://localhost:10000
```

---

## 🗄️ Database

The application automatically creates a **SQLite database** named:

```
accounting.db
```

### Accounts Table

| Column | Description |
|------|-------------|
| id | Unique account ID |
| name | Account name |

### Transactions Table

| Column | Description |
|------|-------------|
| id | Transaction ID |
| date | Transaction date |
| from_account | Sender account |
| to_account | Receiver account |
| amount | Transaction amount |
| remark | Optional note |

---

## 📈 Reports

### Ledger Report
Shows the **money sent and received for a specific account within a date range**.

### Account Summary
Displays **total transactions between the selected account and other accounts**.

---

## 💡 Future Improvements

- User authentication
- Export reports to PDF or Excel
- Dashboard with charts
- REST API integration
- Multi-user support

---

## 📜 License

This project is open-source and available for educational purposes.
