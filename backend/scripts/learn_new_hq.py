import os
import sys
import subprocess

def run_script(script_name):
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    print(f"========================================")
    print(f"Running {script_name}...")
    print(f"========================================")
    result = subprocess.run([sys.executable, script_path])
    if result.returncode != 0:
        print(f"Error: {script_name} failed with return code {result.returncode}")
        sys.exit(1)

def main():
    print("Starting Knowledge Update Pipeline...")
    
    # Bước 1: Nạp file HQ mới vào CSDL
    run_script("seed_ground_truth.py")
    
    # Bước 2: Sinh/Cập nhật Từ điển Vàng (Quy tắc Ưu tiên)
    run_script("extract_supervised_dict.py")
    
    # Bước 3: Huấn luyện lại AI Mô hình dự đoán nhẹ
    run_script("train_model.py")
    
    print("========================================")
    print("Knowledge Update Pipeline completed successfully!")
    print("Hệ thống đã học được các mẫu mới từ file HQ và sẵn sàng sử dụng.")

if __name__ == "__main__":
    main()
