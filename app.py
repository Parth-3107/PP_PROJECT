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

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT date, category, amount FROM expenses')
    rows = c.fetchall()
    conn.close()

    categories = {}
    for row in rows:
        cat = row[1]
        amount = row[2]
        categories[cat] = categories.get(cat, 0) + amount

    chart_path = "static/summary_chart.png"
    if categories:
        plt.figure(figsize=(4, 4))
        plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
        plt.title("Expense Summary")
        plt.savefig(chart_path)
        plt.close()

    pdf_path = "expenses_report.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "Expense Tracker Report")

    data = [["Date", "Category", "Amount (₹)"]] + rows
    table = Table(data, colWidths=[150, 150, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    table.wrapOn(c, width, height)
    table.drawOn(c, 50, height - 120 - 20 * len(rows))

    if os.path.exists(chart_path):
        c.drawImage(chart_path, 200, 50, width=200, preserveAspectRatio=True, mask='auto')

    c.save()
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
