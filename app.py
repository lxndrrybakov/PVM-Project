from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
import mysql.connector
from datetime import datetime, timedelta
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Настройки базы данных
db_config = {
    'user': 'your_user',  # замените на ваше имя пользователя MySQL
    'password': 'your_password',  # замените на ваш пароль MySQL
    'host': 'localhost',
    'database': 'pvm_mileage'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Инициализация статуса ПВМ
def initialize_pvm_status():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pvm_number FROM pvm_status")
    existing_pvms = [row[0] for row in cursor.fetchall()]
    for i in range(1, 12):
        pvm_number = str(i)
        if pvm_number not in existing_pvms:
            cursor.execute("INSERT INTO pvm_status (pvm_number, status) VALUES (%s, %s)", (pvm_number, 'inWork'))
    conn.commit()
    cursor.close()
    conn.close()

initialize_pvm_status()

def get_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pvm_number, date, mileage, comment FROM mileage ORDER BY date")
    records = cursor.fetchall()
    summary = {}
    for pvm_number, date, mileage, comment in records:
        if pvm_number not in summary:
            summary[pvm_number] = []
        summary[pvm_number].append(f"{date}, {mileage} тонн, {comment}")
    cursor.close()
    conn.close()
    return summary

def get_all_series_runs(pvm_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, mileage FROM mileage WHERE pvm_number = %s AND comment = 'Пробег за серию'", (pvm_number,))
    records = cursor.fetchall()
    all_series_runs = [f"{record[0]}, {record[1]} тонн" for record in records]
    cursor.close()
    conn.close()
    return all_series_runs

def get_current_series_run(pvm_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(mileage) FROM mileage WHERE pvm_number = %s AND comment = 'Пробег за серию'", (pvm_number,))
    total_distance = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total_distance or 0

def get_total_run(pvm_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(mileage) FROM mileage WHERE pvm_number = %s AND comment = 'Пробег за серию'", (pvm_number,))
    total_distance = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total_distance or 0


def get_last_repair_run(pvm_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, mileage FROM mileage WHERE pvm_number = %s AND comment = 'Пробег до ремонта' ORDER BY date DESC LIMIT 1", (pvm_number,))
    record = cursor.fetchone()
    last_repair_run = f"{record[0]}, {record[1]} тонн" if record else ""
    cursor.close()
    conn.close()
    return last_repair_run

def reset_run(pvm_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mileage WHERE pvm_number = %s AND comment != 'Пробег до ремонта' AND comment != 'Пробег за серию'", (pvm_number,))
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    pvm_numbers = range(1, 12)
    runs = {str(pvm): get_current_series_run(str(pvm)) for pvm in pvm_numbers}
    total_runs = {str(pvm): get_total_run(str(pvm)) for pvm in pvm_numbers}
    all_series_runs = {str(pvm): get_all_series_runs(str(pvm)) for pvm in pvm_numbers}
    last_repair_runs = {str(pvm): get_last_repair_run(str(pvm)) for pvm in pvm_numbers}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pvm_number, status FROM pvm_status")
    pvm_status = dict(cursor.fetchall())
    cursor.close()
    conn.close()
    return render_template('index.html', runs=runs, total_runs=total_runs, all_series_runs=all_series_runs, last_repair_runs=last_repair_runs, pvm_status=pvm_status)

@app.route('/add_run', methods=['POST'])
def add_run():
    pvm_number = request.form['pvm_number']
    num_blanks = int(request.form['num_blanks'])
    blank_size = request.form['blank_size']
    tech_scrap = float(request.form['tech_scrap'])
    
    coefficients = {'130': 1.6, '150': 2.2}
    fixed_scrap = {'130': 0.066, '150': 0.091}
    run_distance = (num_blanks * coefficients[blank_size]) + (tech_scrap + fixed_scrap[blank_size])
    
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    comment = "Пробег за серию"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mileage (pvm_number, date, mileage, comment) VALUES (%s, %s, %s, %s)", 
                   (pvm_number, current_date, run_distance, comment))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash(f'Пробег для ПВМ №{pvm_number} добавлен. Текущий пробег: {get_current_series_run(pvm_number)} тонн')
    return redirect(url_for('index'))

@app.route('/move_pvm', methods=['POST'])
def move_pvm():
    data = request.get_json()
    pvm_number = data.get('pvm_number')
    new_location = data.get('new_location')
    app.logger.info(f"Moving PVM {pvm_number} to {new_location}")
    if pvm_number and new_location:
        conn = get_db_connection()
        cursor = conn.cursor()
        if new_location == 'inRepair':
            total_run = get_current_series_run(pvm_number)
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            comment = "Пробег до ремонта"
            cursor.execute("INSERT INTO mileage (pvm_number, date, mileage, comment) VALUES (%s, %s, %s, %s)", 
                           (pvm_number, current_date, total_run, comment))
            conn.commit()
            reset_run(pvm_number)
        elif new_location == 'inWork':
            reset_run(pvm_number)  # Сброс пробега при возврате в работу
        cursor.execute("UPDATE pvm_status SET status = %s WHERE pvm_number = %s", (new_location, pvm_number))
        conn.commit()
        cursor.close()
        conn.close()
        app.logger.info(f"PVM {pvm_number} moved to {new_location}")
        return jsonify(success=True)
    else:
        app.logger.error(f"Invalid data: {data}")
        return jsonify(success=False, error="Invalid data")

@app.route('/reset_run', methods=['POST'])
def reset_run_route():
    data = request.get_json()
    pvm_number = data.get('pvm_number')
    password = data.get('password')
    if password == '447':
        reset_run(pvm_number)
        return jsonify(success=True)
    else:
        return jsonify(success=False, error="Invalid password")

@app.route('/reset_mileage', methods=['POST'])
def reset_mileage():
    data = request.get_json()
    period = data.get('period')
    
    if period not in ['day', 'week', 'month', 'all']:
        return jsonify(success=False, error="Invalid period")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if period == 'day':
        cutoff_date = datetime.now() - timedelta(days=1)
    elif period == 'week':
        cutoff_date = datetime.now() - timedelta(weeks=1)
    elif period == 'month':
        cutoff_date = datetime.now() - timedelta(days=30)
    elif period == 'all':
        cutoff_date = datetime(1970, 1, 1)  # Arbitrary old date to delete all
    
    cursor.execute("DELETE FROM mileage WHERE date >= %s", (cutoff_date,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify(success=True)

@app.route('/history')
def history():
    summary = get_summary()
    return render_template('history.html', summary=summary)

@app.route('/statistics')
def statistics():
    summary = get_summary()
    detailed_summary = []
    for pvm_number, logs in summary.items():
        total_run = get_total_run(pvm_number)  # Использование обновленной функции
        repair_runs = [log for log in logs if 'Пробег до ремонта' in log and is_valid_log(log)]
        series_runs = [log for log in logs if 'Пробег за серию' in log and is_valid_log(log)]
        detailed_summary.append({
            'pvm_number': pvm_number,
            'total_run': total_run,
            'repair_runs': repair_runs,
            'series_runs': series_runs
        })
    return render_template('statistics.html', summary=detailed_summary)


def is_valid_log(log):
    try:
        float(log.split(', ')[1].split(' ')[0])
        return True
    except (ValueError, IndexError):
        return False

@app.route('/export_excel')
def export_excel():
    summary = get_summary()
    filename = f'Пробеги_ПВМ_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    filepath = os.path.join('run_data', filename)
    
    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        for pvm_number, logs in summary.items():
            data_series = []
            data_repairs = []
            
            for log in logs:
                parts = log.split(', ')
                date = parts[0]
                mileage_comment = ', '.join(parts[1:])
                mileage, comment = mileage_comment.split(' тонн, ', 1)
                if "Пробег за серию" in comment:
                    data_series.append([date, mileage])
                elif "Пробег до ремонта" in comment:
                    data_repairs.append([date, mileage])
            
            df_series = pd.DataFrame(data_series, columns=['Дата', 'Пробег за серию (тонн)'])
            df_repairs = pd.DataFrame(data_repairs, columns=['Дата', 'Пробег до ремонта (тонн)'])
            
            df_series.to_excel(writer, sheet_name=f'ПВМ {pvm_number} - Серии', index=False)
            df_repairs.to_excel(writer, sheet_name=f'ПВМ {pvm_number} - Ремонт', index=False)
    
    return send_file(filepath, as_attachment=True)

@app.route('/current_run/<pvm_number>', methods=['GET'])
def current_run(pvm_number):
    current_run = get_current_series_run(pvm_number)
    return jsonify(current_run=current_run)

if __name__ == '__main__':
    if not os.path.exists('run_data'):
        os.makedirs('run_data')
    app.run(debug=True)
