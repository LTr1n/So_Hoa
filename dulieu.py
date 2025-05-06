import pandas as pd
import numpy as np

# Bước 1: Đọc dữ liệu từ file
df = pd.read_csv("uploads/HIV_dataset_enhanced.csv")

# Bước 2: Tạo lại cột mã số bệnh nhân chỉ là số
df['ID'] = [str(i).zfill(4) for i in range(1, len(df) + 1)]

# Bước 3: Đổi tên cột tên bệnh nhân
df['Name'] = df['Full_Name'].astype(str)

# Bước 4: Chuẩn hóa cột tỉnh thành (viết hoa chữ cái đầu)
df['Location'] = df['Location'].str.strip().str.title()

# Bước 5: Thêm 2 cột mới (Raw_Symptom và Raw_Behavior)
# Danh sách triệu chứng và hành vi
symptoms = ["Sốt", "Sụt cân", "Nổi hạch"]
behaviors = ["Quan hệ không bảo vệ", "Tiêm chích ma túy", "Nhiều bạn tình", "Không hành vi nguy cơ"]

# Thêm cột triệu chứng ngẫu nhiên (mỗi người 1 triệu chứng)
df['Raw_Symptom'] = np.random.choice(symptoms, size=len(df))

# Thêm cột hành vi ngẫu nhiên (ưu tiên hành vi nguy cơ cho HIV+)
df['Raw_Behavior'] = np.where(
    df['Result'] == 'POSITIVE',
    np.random.choice(behaviors[:-1], size=len(df), p=[0.6, 0.3, 0.1]),  # Bỏ "Không hành vi nguy cơ" cho HIV+
    np.random.choice(behaviors, size=len(df), p=[0.2, 0.1, 0.2, 0.5])    # 50% không có hành vi nguy cơ cho HIV-
)

# Bước 6: Xác định thứ tự cột mới
column_order = [
    'ID', 'Name', 'Age', 'Location', 'Raw_Symptom', 'Raw_Behavior',
    'Marital Staus', 'STD', 'Educational Background', 
    'HIV TEST IN PAST YEAR', 'AIDS education',
    'Places of seeking sex partners', 'SEXUAL ORIENTATION', 
    'Drug- taking', 'Result'
]

# Bước 7: Tạo bảng mới và lưu ra file CSV hoàn chỉnh
df_final = df[column_order]
df_final.to_csv("HIV_dataset_final_with_symptoms_behaviors.csv", index=False, encoding='utf-8-sig')

print("✅ Xuất file thành công: HIV_dataset_final_with_symptoms_behaviors.csv")