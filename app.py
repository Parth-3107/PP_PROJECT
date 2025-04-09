from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import os
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

app = Flask(__name__)

# Create database
def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    category TEXT,
                    amount REAL
                )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT id, date, category, amount FROM expenses')
    rows = c.fetchall()
    conn.close()
    return render_template('index.html', rows=rows)

@app.route('/summary_chart_data')
def summary_chart_data():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT category, SUM(amount) FROM expenses GROUP BY category')
    rows = c.fetchall()
    conn.close()

    labels = [row[0] for row in rows]
    values = [row[1] for row in rows]
    return {'labels': labels, 'values': values}


@app.route('/add', methods=['POST'])
def add_expense():
    date = request.form['date']
    category = request.form['category']
    amount = float(request.form['amount'])

    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('INSERT INTO expenses (date, category, amount) VALUES (?, ?, ?)', (date, category, amount))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id=?', (expense_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/summary_chart')
def summary_chart():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT category, amount FROM expenses')
    data = c.fetchall()
    conn.close()

    categories = {}
    for category, amount in data:
        categories[category] = categories.get(category, 0) + amount

    if not categories:
        plt.figure()
        plt.text(0.5, 0.5, 'No data', ha='center', va='center')
    else:
        plt.figure(figsize=(4, 4))
        plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
    plt.title("Expense Summary")
    path = 'static/summary_chart.png'
    plt.savefig(path)
    plt.close()
    return send_file(path, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
