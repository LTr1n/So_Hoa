from flask import Flask, request, render_template, flash, redirect, url_for, session, send_file
import pandas as pd
import sqlite3
import io
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
DB_PATH = './data/HIV_database.db'

# Giả lập tài khoản
USERS = {'khang': 'khang123', 'luan': 'luan123'}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS Patients (
        ID TEXT PRIMARY KEY, Name TEXT, Age INTEGER, Location TEXT, 
        Raw_Symptom TEXT, Raw_Behavior TEXT, "Marital Status" TEXT, 
        STD INTEGER, "Educational Background" TEXT, "HIV TEST IN PAST YEAR" INTEGER, 
        "AIDS education" INTEGER, "Places of seeking sex partners" TEXT, 
        "Sexual Orientation" TEXT, Result TEXT)''')  # Đổi INTEGER thành TEXT
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            return redirect(url_for('upload_file'))
        flash('Sai tên đăng nhập hoặc mật khẩu!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Không có file!')
            return redirect(request.url)
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            try:
                df = pd.read_csv(file)
                # Sửa lỗi chính tả và chuẩn hóa
                df.columns = df.columns.str.replace('Marital Staus', 'Marital Status')
                df['Sexual Orientation'] = df['SEXUAL ORIENTATION'].replace('Hetersexual', 'Heterosexual')
                df['Places of seeking sex partners'] = df['Places of seeking sex partners'].fillna('Unknown')
                binary_cols = ['STD', 'HIV TEST IN PAST YEAR', 'AIDS education']
                for col in binary_cols:
                    if col in df.columns:
                        df[col] = df[col].map({'YES': 1, 'NO': 0})

                # Xử lý cột Result
                if 'Result' not in df.columns:
                    df['Result'] = 'Unknown'
                else:
                    df['Result'] = df['Result'].fillna('Unknown')
                    df['Result'] = df['Result'].apply(lambda x: 'POSITIVE' if x == 'POSITIVE' else 'NEGATIVE' if x == 'NEGATIVE' else 'Unknown')

                df = df.drop(columns=['SEXUAL ORIENTATION'])

                # Kết nối cơ sở dữ liệu
                conn = sqlite3.connect(DB_PATH)

                # Kiểm tra và tạo ID tự động nếu cần
                if 'ID' not in df.columns:
                    df['ID'] = [None] * len(df)
                else:
                    df['ID'] = df['ID'].astype(str).replace('nan', None)

                # Lấy danh sách ID hiện có để kiểm tra trùng lặp
                cursor = conn.cursor()
                cursor.execute("SELECT ID FROM Patients")
                existing_ids = set(row[0] for row in cursor.fetchall())

                # Tạo ID mới cho các hàng không có ID
                max_id = max([int(id) for id in existing_ids], default=0) if existing_ids else 0
                for i in range(len(df)):
                    if df.at[i, 'ID'] is None or pd.isna(df.at[i, 'ID']):
                        new_id = max_id + 1
                        while f"{new_id:04d}" in existing_ids:  # Đảm bảo không trùng lặp
                            new_id += 1
                        df.at[i, 'ID'] = f"{new_id:04d}"
                        existing_ids.add(f"{new_id:04d}")
                        max_id = new_id

                # Nhập dữ liệu vào SQLite
                df.to_sql('Patients', conn, if_exists='append', index=False)
                conn.close()
                flash('Thêm hồ sơ thành công!')
            except Exception as e:
                flash(f'Lỗi: {str(e)}')
            return redirect(url_for('list_patients'))
    return render_template('index.html')

@app.route('/patients', methods=['GET'])
def list_patients():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM Patients", conn)
    conn.close()
    patients = df.to_dict('records')
    return render_template('patients.html', patients=patients)

@app.route('/search', methods=['GET', 'POST'])
def search_patients():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        search_term = request.form['search_term']
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT * FROM Patients WHERE ID LIKE ? OR Name LIKE ? OR Raw_Symptom LIKE ?"
        df = pd.read_sql_query(query, conn, params=(f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        conn.close()
        patients = df.to_dict('records')
        return render_template('patients.html', patients=patients)
    return render_template('search.html')

@app.route('/delete/<patient_id>')
def delete_patient(patient_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM Patients WHERE ID = ?", (patient_id,))
    conn.commit()
    conn.close()
    flash(f'Đã xóa bệnh nhân {patient_id}')
    return redirect(url_for('list_patients'))

@app.route('/export')
def export_data():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM Patients", conn)
    conn.close()
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='patients_export.csv'
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)