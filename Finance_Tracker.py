import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
from datetime import datetime
import re

class Transaction:
    def __init__(self, amount, category, date=None):
        self.date = date if date else datetime.now()
        self.amount = amount
        self.category = category

class User:
    def __init__(self, username, password, income):
        self.username = username
        if self.is_valid_password(password):
            self.password = password
        else:
            raise ValueError("Invalid password format")
        self.income = income
        self.transactions = []

    def is_valid_password(self, password):
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%^&+=]).{8,}$"
        return re.match(pattern, password)

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        self.income -= transaction.amount

    def update_income(self, amount):
        self.income += amount

class FinanceTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Finance Tracker")

        # Connect to SQLite database
        self.conn = sqlite3.connect('finance_tracker.db')
        self.cursor = self.conn.cursor()
        self.setup_database()

        self.user = None

        self.login_menu()

    def setup_database(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                               username TEXT PRIMARY KEY,
                               password TEXT,
                               income REAL)''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               username TEXT,
                               date TEXT,
                               amount REAL,
                               category TEXT,
                               FOREIGN KEY(username) REFERENCES users(username))''')

        self.conn.commit()

    def login_menu(self):
        self.clear_frame()
        tk.Label(self.root, text="Finance Tracker Login", font=("Arial", 20)).pack(pady=20)
        tk.Button(self.root, text="Create Account", command=self.create_user).pack(pady=10)
        tk.Button(self.root, text="Log In", command=self.login_user).pack(pady=10)

    def create_user(self):
        username = simpledialog.askstring("Create User", "Enter your username:")
        while True:
            password = simpledialog.askstring("Create User", "Enter your password:", show='*')
            try:
                income = simpledialog.askfloat("Create User", "Enter your income:")
                if self.is_valid_password(password):
                    self.cursor.execute("INSERT INTO users (username, password, income) VALUES (?, ?, ?)",
                                        (username, password, income))
                    self.conn.commit()
                    messagebox.showinfo("Success", "Account created successfully!")
                    self.login_menu()
                    return
                else:
                    raise ValueError("Invalid password format")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists.")
                return
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    def is_valid_password(self, password):
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%^&+=]).{8,}$"
        return re.match(pattern, password)

    def login_user(self):
        username = simpledialog.askstring("Login", "Enter your username:")
        password = simpledialog.askstring("Login", "Enter your password:", show='*')

        self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        result = self.cursor.fetchone()
        if result:
            self.user = User(username, password, result[2])
            self.load_user_transactions()
            self.main_menu()
        else:
            messagebox.showerror("Error", "Invalid username or password")
            self.login_menu()

    def load_user_transactions(self):
        self.cursor.execute("SELECT date, amount, category FROM transactions WHERE username=?", (self.user.username,))
        rows = self.cursor.fetchall()
        for row in rows:
            date, amount, category = row
            transaction = Transaction(amount, category, datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f"))
            self.user.transactions.append(transaction)

    def main_menu(self):
        self.clear_frame()
        tk.Label(self.root, text="Personal Finance Tracker Menu", font=("Arial", 20)).pack(pady=20)
        tk.Button(self.root, text="Log Transaction", command=self.log_transaction).pack(pady=10)
        tk.Button(self.root, text="Show Transactions", command=self.show_transactions).pack(pady=10)
        tk.Button(self.root, text="Monthly Spendings", command=self.show_monthly_spendings).pack(pady=10)
        tk.Button(self.root, text="Add Monthly Salary", command=self.add_monthly_salary).pack(pady=10)
        tk.Button(self.root, text="Savings", command=self.show_savings).pack(pady=10)
        tk.Button(self.root, text="Exit", command=self.save_and_exit).pack(pady=10)

    def log_transaction(self):
        amount = simpledialog.askfloat("Transaction", "Enter amount:")
        if amount is None:
            return
        if amount > self.user.income:
            messagebox.showerror("Error", "Insufficient funds. Transaction cannot be completed.")
            return

        category = simpledialog.askstring("Transaction", "Enter expense category (e.g., FOOD, HOUSING, TRANSPORTATION):")
        if category is None:
            return

        transaction = Transaction(amount, category)
        self.user.add_transaction(transaction)
        self.cursor.execute("INSERT INTO transactions (username, date, amount, category) VALUES (?, ?, ?, ?)",
                            (self.user.username, transaction.date, transaction.amount, transaction.category))
        self.conn.commit()
        messagebox.showinfo("Success", "Transaction logged successfully!")
        self.main_menu()

    def add_monthly_salary(self):
        amount = simpledialog.askfloat("Add Monthly Salary", "Enter your monthly salary:")
        if amount is not None:
            self.user.update_income(amount)
            self.cursor.execute("UPDATE users SET income = ? WHERE username = ?", (self.user.income, self.user.username))
            self.conn.commit()
            messagebox.showinfo("Success", "Monthly salary added successfully!")
        self.main_menu()

    def show_transactions(self):
        self.clear_frame()
        tk.Label(self.root, text=f"Transactions for {self.user.username}", font=("Arial", 20)).pack(pady=20)
        for transaction in self.user.transactions:
            tk.Label(self.root, text=f"Date: {transaction.date}, Amount: ${transaction.amount}, Category: {transaction.category}").pack()
        tk.Label(self.root, text=f"Remaining Income: ${self.user.income}", font=("Arial", 14)).pack(pady=10)
        tk.Button(self.root, text="Back to Main Menu", command=self.main_menu).pack(pady=10)

    def show_monthly_spendings(self):
        self.clear_frame()
        tk.Label(self.root, text=f"Monthly Spendings for {self.user.username}", font=("Arial", 20)).pack(pady=20)
        
        current_month = datetime.now().month
        current_year = datetime.now().year

        self.cursor.execute('''SELECT category, SUM(amount) 
                               FROM transactions 
                               WHERE username = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ? 
                               GROUP BY category''', 
                            (self.user.username, f"{current_month:02d}", current_year))
        rows = self.cursor.fetchall()
        
        for row in rows:
            category, total_amount = row
            tk.Label(self.root, text=f"Category: {category}, Total Amount: ${total_amount:.2f}").pack()
        
        tk.Button(self.root, text="Back to Main Menu", command=self.main_menu).pack(pady=10)

    def show_savings(self):
        self.clear_frame()
        tk.Label(self.root, text=f"Savings for {self.user.username}", font=("Arial", 20)).pack(pady=20)
        
        initial_income = self.user.income + sum(transaction.amount for transaction in self.user.transactions)
        total_expense = sum(transaction.amount for transaction in self.user.transactions)
        savings = initial_income - total_expense
        
        tk.Label(self.root, text=f"Total Savings: ${savings:.2f}", font=("Arial", 14)).pack(pady=10)
        
        tk.Button(self.root, text="Back to Main Menu", command=self.main_menu).pack(pady=10)

    def save_and_exit(self):
        self.conn.close()
        self.root.quit()

    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceTrackerApp(root)
    root.mainloop()
