import pandas as pd
import sqlite3

# Đường dẫn đến file CSV và cơ sở dữ liệu SQLite
csv_path = './data/HIV_dataset.csv'
db_path = './data/HIV_database.db'

# Đọc dữ liệu từ CSV
df = pd.read_csv(csv_path)

# In danh sách cột để kiểm tra
print("Danh sách cột trong dữ liệu:", df.columns.tolist())

# Làm sạch dữ liệu
df.columns = df.columns.str.replace('Marital Staus', 'Marital Status')
df['Sexual Orientation'] = df['SEXUAL ORIENTATION'].replace('Hetersexual', 'Heterosexual')
df['Places of seeking sex partners'] = df['Places of seeking sex partners'].fillna('Unknown')

# Chuẩn hóa YES/NO
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

# Xóa cột SEXUAL ORIENTATION gốc sau khi sửa
df = df.drop(columns=['SEXUAL ORIENTATION'])

# Kết nối và nhập dữ liệu vào SQLite
conn = sqlite3.connect(db_path)
df.to_sql('Patients', conn, if_exists='replace', index=False)
conn.close()

print("Dữ liệu đã được số hóa và lưu vào hiv_database.db")