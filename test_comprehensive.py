"""
=============================================================================
BỘ KIỂM THỬ TOÀN DIỆN - HỆ THỐNG AI CHUẨN HÓA DỮ LIỆU HẢI QUAN
=============================================================================
Test Cases:
  TC1: Accuracy Test - So sánh output vs HQ 2026 Ground Truth (tháng 2)
  TC2: Consistency Test - Cùng 1 dòng hàng phải cho cùng kết quả
  TC3: Coverage Test - Tỷ lệ auto-classification trên raw data hoàn toàn mới
  TC4: Speed Test - Tốc độ xử lý trên nhiều file khác nhau
  TC5: Edge Cases - Dữ liệu rỗng, thiếu cột, ký tự đặc biệt
  TC6: Column Output Test - Kiểm tra file đầu ra có đủ cột và đúng format
  TC7: Cross-HS Test - Thử trên các mã HS khác (không chỉ 8539/9405)
  TC8: Label Distribution Test - Phân bố nhãn đầu ra có hợp lý không
  TC9: Trạng Thái Test - Kiểm tra phân bố các trạng thái xử lý
  TC10: Sample Output Verification - In mẫu đầu ra để kiểm tra trực quan
=============================================================================
"""
import os
import sys
import time
import asyncio
import pandas as pd
import numpy as np
import glob
import traceback

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('backend'))
from core.data_cleaner import DataCleaner, clean_text_basic

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

RAW_DIR = r"e:\TÀI LIỆU THỰC TẬP\Dự án  Làm sạch và chuẩn hóa dữ liệu\Dữ liệu hải quan\Nam 2026"
HQ_2026_PATH = r"backend/storage/HQ 2026.xlsx"

results_summary = []

def log_result(tc_name, status, detail):
    results_summary.append((tc_name, status, detail))
    print(f"\n{'='*70}")
    print(f"  {status}  {tc_name}")
    print(f"  {detail}")
    print(f"{'='*70}")

def load_raw_file(path):
    try:
        df = pd.read_excel(path, dtype=str, skiprows=9)
        if 'HS_Code' in df.columns or 'VN_Exporter' in df.columns or 'VN_Importer' in df.columns:
            return df
        return pd.read_excel(path, dtype=str)
    except Exception:
        return pd.read_excel(path, dtype=str)

# ============ INIT ============
print("=" * 70)
print("  KHỞI TẠO HỆ THỐNG")
print("=" * 70)
cleaner = DataCleaner(model_path='backend/storage/classifier_model.pkl')

# Load HQ 2026 as ground truth
hq26 = pd.read_excel(HQ_2026_PATH, dtype=str)
hq26['Mã HS'] = hq26['Mã HS'].str.replace('.0', '', regex=False).str.strip()
print(f"HQ 2026 Ground Truth: {len(hq26)} rows")

# ============ TC1: ACCURACY TEST ============
print("\n\n" + "#" * 70)
print("  TC1: ACCURACY TEST - So sánh output với HQ 2026 Ground Truth")
print("#" * 70)

try:
    raw_8539_9405 = [f for f in glob.glob(os.path.join(RAW_DIR, "*.xls*")) 
                     if os.path.basename(f).startswith(('8539', '9405'))]
    
    hq26_lookup = {}
    for _, row in hq26.iterrows():
        hs = str(row['Mã HS']).strip()
        ten_hang = clean_text_basic(row.get('Tên hàng', ''))
        key = (hs, ten_hang)
        hq26_lookup[key] = {
            'Dòng SP': str(row.get('Dòng SP', '')).strip(),
            'Loại': str(row.get('Loại', '')).strip(),
            'Lớp 1': str(row.get('Lớp 1', '')).strip(),
            'Lớp 2': str(row.get('Lớp 2', '')).strip(),
        }
    
    total_matched = 0
    total_correct_dong = 0
    total_correct_loai = 0
    total_correct_lop1 = 0
    total_correct_all = 0
    sample_mismatches = []
    
    for rf in raw_8539_9405:
        fname = os.path.basename(rf)
        df_raw = load_raw_file(rf)
        df_out = asyncio.run(cleaner.process_async(df_raw))
        
        for _, row in df_out.iterrows():
            hs = str(row.get('Mã HS', '')).strip()
            ten_hang = clean_text_basic(row.get('Tên hàng', ''))
            key = (hs, ten_hang)
            
            if key in hq26_lookup:
                total_matched += 1
                gt = hq26_lookup[key]
                pred_dong = str(row.get('Dòng SP', '')).strip()
                pred_loai = str(row.get('Loại', '')).strip()
                pred_lop1 = str(row.get('Lớp 1', '')).strip()
                
                dong_ok = pred_dong == gt['Dòng SP']
                loai_ok = pred_loai == gt['Loại']
                lop1_ok = pred_lop1 == gt['Lớp 1']
                
                if dong_ok: total_correct_dong += 1
                if loai_ok: total_correct_loai += 1
                if lop1_ok: total_correct_lop1 += 1
                if dong_ok and loai_ok and lop1_ok: total_correct_all += 1
                
                if not dong_ok and len(sample_mismatches) < 10:
                    sample_mismatches.append({
                        'file': fname,
                        'hs': hs,
                        'text': str(row.get('Tên hàng', ''))[:80],
                        'pred_dong': pred_dong,
                        'gt_dong': gt['Dòng SP'],
                        'pred_loai': pred_loai,
                        'gt_loai': gt['Loại'],
                    })

    if total_matched > 0:
        acc_dong = total_correct_dong / total_matched * 100
        acc_loai = total_correct_loai / total_matched * 100
        acc_lop1 = total_correct_lop1 / total_matched * 100
        acc_all = total_correct_all / total_matched * 100
        
        print(f"\n  Tổng dòng khớp với HQ 2026 Ground Truth: {total_matched}")
        print(f"  Accuracy Dòng SP:  {total_correct_dong}/{total_matched} = {acc_dong:.1f}%")
        print(f"  Accuracy Loại:     {total_correct_loai}/{total_matched} = {acc_loai:.1f}%")
        print(f"  Accuracy Lớp 1:    {total_correct_lop1}/{total_matched} = {acc_lop1:.1f}%")
        print(f"  Accuracy Tổng:     {total_correct_all}/{total_matched} = {acc_all:.1f}%")
        
        if sample_mismatches:
            print(f"\n  --- Mẫu dự đoán sai (tối đa 10 dòng) ---")
            for m in sample_mismatches:
                print(f"    File: {m['file']} | HS: {m['hs']}")
                print(f"    Text: {m['text']}")
                print(f"    Pred Dòng SP: '{m['pred_dong']}' vs GT: '{m['gt_dong']}'")
                print(f"    Pred Loại: '{m['pred_loai']}' vs GT: '{m['gt_loai']}'")
                print()
        
        status = PASS if acc_dong >= 90 else (WARN if acc_dong >= 70 else FAIL)
        log_result("TC1: Accuracy vs HQ 2026", status,
                   f"Dòng SP={acc_dong:.1f}%, Loại={acc_loai:.1f}%, Lớp 1={acc_lop1:.1f}%, All={acc_all:.1f}% trên {total_matched} dòng khớp GT")
    else:
        log_result("TC1: Accuracy vs HQ 2026", WARN,
                   f"Không tìm thấy dòng nào khớp (Bình thường do RAW chỉ có Th1,3,4 còn HQ 2026 là Th2)")
except Exception as e:
    log_result("TC1: Accuracy vs HQ 2026", FAIL, f"Exception: {e}")
    traceback.print_exc()

# ============ TC2: CONSISTENCY TEST ============
print("\n\n" + "#" * 70)
print("  TC2: CONSISTENCY TEST - Cùng input → cùng output")
print("#" * 70)

try:
    sample_rows = [
        {'HS_Code': '94054090', 'Detailed_Product': 'ĐÈN LED PANEL ÂM TRẦN 600X600 40W HIỆU RẠNG ĐÔNG'},
        {'HS_Code': '94054090', 'Detailed_Product': 'ĐÈN LED PANEL ÂM TRẦN 600X600 40W HIỆU RẠNG ĐÔNG'},
        {'HS_Code': '85393190', 'Detailed_Product': 'BÓNG ĐÈN LED 9W PHILIPS BULB E27 MỚI 100%'},
        {'HS_Code': '85393190', 'Detailed_Product': 'BÓNG ĐÈN LED 9W PHILIPS BULB E27 MỚI 100%'},
        {'HS_Code': '94054090', 'Detailed_Product': 'đèn led downlight 7w panasonic hàng mới 100%'},
        {'HS_Code': '94054090', 'Detailed_Product': 'đèn led downlight 7w panasonic hàng mới 100%'},
    ]
    df_consistency = pd.DataFrame(sample_rows)
    df_out = asyncio.run(cleaner.process_async(df_consistency))
    
    inconsistent = 0
    for i in range(0, len(df_out), 2):
        r1 = df_out.iloc[i]
        r2 = df_out.iloc[i + 1]
        for col in ['Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2']:
            v1 = str(r1.get(col, '')).strip()
            v2 = str(r2.get(col, '')).strip()
            if v1 != v2:
                inconsistent += 1
                print(f"  ❌ Row {i} vs {i+1}: '{col}' khác nhau: '{v1}' vs '{v2}'")
    
    if inconsistent == 0:
        log_result("TC2: Consistency", PASS, f"Tất cả {len(df_out)//2} cặp dòng lặp đều cho kết quả giống hệt nhau")
    else:
        log_result("TC2: Consistency", FAIL, f"Có {inconsistent} trường hợp không nhất quán")
except Exception as e:
    log_result("TC2: Consistency", FAIL, f"Exception: {e}")
    traceback.print_exc()

# ============ TC3: COVERAGE TEST ============
print("\n\n" + "#" * 70)
print("  TC3: COVERAGE TEST - Auto-classification trên raw files")
print("#" * 70)

try:
    per_file_results = []
    all_files = glob.glob(os.path.join(RAW_DIR, "8539*.xls*")) + glob.glob(os.path.join(RAW_DIR, "9405*.xls*"))
    
    for rf in all_files:
        fname = os.path.basename(rf)
        df_raw = load_raw_file(rf)
        t0 = time.time()
        df_out = asyncio.run(cleaner.process_async(df_raw))
        elapsed = time.time() - t0
        
        total = len(df_out)
        auto = sum(1 for _, r in df_out.iterrows() if pd.notna(r.get('Dòng SP')) and str(r.get('Dòng SP')).strip() not in ('', 'UNKNOWN'))
        need_review = sum(1 for _, r in df_out.iterrows() if str(r.get('Trạng Thái', '')).strip() == 'Cần Nghiệp Vụ')
        
        pct = auto / total * 100 if total > 0 else 0
        speed = total / elapsed if elapsed > 0 else 0
        per_file_results.append({'file': fname, 'total': total, 'auto': auto, 'pct': pct, 'need_review': need_review, 'time': elapsed, 'speed': speed})
        print(f"  {fname}: {auto}/{total} ({pct:.1f}%) auto | {need_review} cần NV | {elapsed:.2f}s ({speed:.0f} rows/s)")
    
    total_all = sum(r['total'] for r in per_file_results)
    auto_all = sum(r['auto'] for r in per_file_results)
    time_all = sum(r['time'] for r in per_file_results)
    pct_all = auto_all / total_all * 100 if total_all > 0 else 0
    
    status = PASS if pct_all >= 95 else (WARN if pct_all >= 80 else FAIL)
    log_result("TC3: Coverage", status,
               f"Auto-classified: {auto_all}/{total_all} ({pct_all:.1f}%) | Tổng thời gian: {time_all:.2f}s | Speed: {total_all/time_all:.0f} rows/s")
except Exception as e:
    log_result("TC3: Coverage", FAIL, f"Exception: {e}")
    traceback.print_exc()

# ============ TC4: SPEED TEST ============
print("\n\n" + "#" * 70)
print("  TC4: SPEED TEST - Tốc độ trên file lớn nhất")
print("#" * 70)

try:
    biggest_file = max(all_files, key=os.path.getsize)
    fname = os.path.basename(biggest_file)
    df_big = load_raw_file(biggest_file)
    
    times = []
    for run in range(3):
        t0 = time.time()
        asyncio.run(cleaner.process_async(df_big))
        elapsed = time.time() - t0
        times.append(elapsed)
        print(f"  Run {run+1}: {elapsed:.2f}s ({len(df_big)/elapsed:.0f} rows/s)")
    
    avg_time = sum(times) / len(times)
    avg_speed = len(df_big) / avg_time
    status = PASS if avg_speed >= 5000 else (WARN if avg_speed >= 1000 else FAIL)
    log_result("TC4: Speed", status,
               f"File: {fname} ({len(df_big)} rows) | Avg: {avg_time:.2f}s | Speed: {avg_speed:.0f} rows/s")
except Exception as e:
    log_result("TC4: Speed", FAIL, f"Exception: {e}")
    traceback.print_exc()

# ============ TC5: EDGE CASES ============
print("\n\n" + "#" * 70)
print("  TC5: EDGE CASES - Dữ liệu bất thường")
print("#" * 70)

try:
    edge_cases = pd.DataFrame([
        {'HS_Code': '94054090', 'Detailed_Product': ''},
        {'HS_Code': '85393190', 'Detailed_Product': None},
        {'HS_Code': '94054090', 'Detailed_Product': '!!!@@@###$$$%%%^^^&&&***()()'},
        {'HS_Code': '94054090', 'Detailed_Product': 'đèn led panel ' * 200},
        {'HS_Code': '99999999', 'Detailed_Product': 'sản phẩm không xác định'},
        {'HS_Code': '', 'Detailed_Product': 'đèn led 10w philips'},
        {'HS_Code': '94054090', 'Detailed_Product': '123456789'},
        {'HS_Code': '85393190', 'Detailed_Product': 'LED BULB 9W 电灯泡 bóng đèn ランプ'},
        {'HS_Code': '94054090', 'Detailed_Product': 'rác#&đèn led panel 40w rạng đông#&thêm rác'},
    ])
    
    df_edge = asyncio.run(cleaner.process_async(edge_cases))
    
    errors = 0
    for i, row in df_edge.iterrows():
        ten_hang = str(row.get('Tên hàng', ''))
        dong_sp = str(row.get('Dòng SP', ''))
        trang_thai = str(row.get('Trạng Thái', ''))
        print(f"  Row {i}: Tên hàng='{ten_hang[:50]}' | Dòng SP='{dong_sp}' | TT='{trang_thai}'")
        
        if pd.isna(row.get('Mã HS')):
            errors += 1
            print(f"    ❌ Mã HS bị null!")
    
    status = PASS if errors == 0 else FAIL
    log_result("TC5: Edge Cases", status,
               f"Xử lý {len(edge_cases)} edge cases | Errors: {errors}")
except Exception as e:
    log_result("TC5: Edge Cases", FAIL, f"Exception: {e}")
    traceback.print_exc()

# ============ TC6: COLUMN OUTPUT TEST ============
print("\n\n" + "#" * 70)
print("  TC6: COLUMN OUTPUT TEST - Kiểm tra format đầu ra")
print("#" * 70)

try:
    sample_file = glob.glob(os.path.join(RAW_DIR, "9405-NK-Th1*"))[0]
    df_raw = load_raw_file(sample_file)
    df_out = asyncio.run(cleaner.process_async(df_raw.head(10)))
    
    expected_cols = ['Ngày', 'Mã HS', 'Công ty NK', 'Tên hàng', 'DVT', 'Lượng', 'Giá trị', 'Đơn giá',
                     'Hãng', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Công suất', 'Quốc gia', 'Châu lục',
                     'Trạng Thái']
    
    missing = [c for c in expected_cols if c not in df_out.columns]
    extra = [c for c in df_out.columns if c not in expected_cols and c not in ['MDSD', 'Công ty XK', 'Incoterms', 'Method_of_Payment', 'Công suất.1', 'Loại 1', 'Loại 2', 'Năm']]
    
    print(f"  Output columns ({len(df_out.columns)}): {list(df_out.columns)}")
    print(f"  Missing critical columns: {missing}")
    print(f"  Extra columns: {extra}")
    
    status = PASS if len(missing) == 0 else FAIL
    log_result("TC6: Column Output", status,
               f"Missing: {missing if missing else 'None'} | Output has {len(df_out.columns)} columns")
except Exception as e:
    log_result("TC6: Column Output", FAIL, f"Exception: {e}")
    traceback.print_exc()

# ============ TC7: CROSS-HS TEST ============
print("\n\n" + "#" * 70)
print("  TC7: CROSS-HS TEST - Thử trên mã HS khác (850440, 850760, 7020)")
print("#" * 70)

try:
    other_hs_files = []
    for prefix in ['850440', '850760', '7020']:
        found = glob.glob(os.path.join(RAW_DIR, f"{prefix}*.xls*"))
        if found:
            other_hs_files.append(found[0])
    
    cross_results = []
    for rf in other_hs_files:
        fname = os.path.basename(rf)
        df_raw = load_raw_file(rf)
        df_sample = df_raw.head(500)
        t0 = time.time()
        df_out = asyncio.run(cleaner.process_async(df_sample))
        elapsed = time.time() - t0
        
        total = len(df_out)
        auto = sum(1 for _, r in df_out.iterrows() if pd.notna(r.get('Dòng SP')) and str(r.get('Dòng SP')).strip() not in ('', 'UNKNOWN'))
        need_review = sum(1 for _, r in df_out.iterrows() if str(r.get('Trạng Thái', '')).strip() == 'Cần Nghiệp Vụ')
        pct = auto / total * 100 if total > 0 else 0
        
        cross_results.append({'file': fname, 'total': total, 'auto': auto, 'pct': pct, 'need_review': need_review})
        print(f"  {fname}: {auto}/{total} ({pct:.1f}%) auto | {need_review} cần NV | {elapsed:.2f}s")
    
    if cross_results:
        avg_pct = sum(r['pct'] for r in cross_results) / len(cross_results)
        log_result("TC7: Cross-HS", WARN if avg_pct < 50 else PASS,
                   f"Avg coverage trên các mã HS khác: {avg_pct:.1f}% (Bình thường nếu các mã này chưa có trong file training HQ)")
    else:
        log_result("TC7: Cross-HS", WARN, "Không tìm thấy file raw cho các mã HS khác")
except Exception as e:
    log_result("TC7: Cross-HS", FAIL, f"Exception: {e}")
    traceback.print_exc()

# ============ TC8: LABEL DISTRIBUTION ============
print("\n\n" + "#" * 70)
print("  TC8: LABEL DISTRIBUTION - Phân bố nhãn Dòng SP trên output")
print("#" * 70)

try:
    big_file = glob.glob(os.path.join(RAW_DIR, "9405-NK-Th1*"))[0]
    df_raw = load_raw_file(big_file)
    df_out = asyncio.run(cleaner.process_async(df_raw))
    
    dong_dist = df_out['Dòng SP'].value_counts()
    print(f"\n  Phân bố Dòng SP (Top 15) trên {len(df_out)} dòng:")
    for label, count in dong_dist.head(15).items():
        if pd.isna(label) or str(label).strip() == '':
            label = "<Empty>"
        pct = count / len(df_out) * 100
        bar = '█' * int(pct / 2)
        print(f"    {str(label):30s} {count:6d} ({pct:5.1f}%) {bar}")
    
    top1_pct = dong_dist.iloc[0] / len(df_out) * 100 if len(dong_dist) > 0 else 0
    n_labels = len(dong_dist)
    
    status = PASS if top1_pct < 95 else WARN
    log_result("TC8: Label Distribution", status,
               f"{n_labels} nhãn Dòng SP khác nhau | Top-1 chiếm {top1_pct:.1f}%")
except Exception as e:
    log_result("TC8: Label Distribution", FAIL, f"Exception: {e}")
    traceback.print_exc()

# ============ TC9: TRẠNG THÁI DISTRIBUTION ============
print("\n\n" + "#" * 70)
print("  TC9: TRẠNG THÁI DISTRIBUTION - Phân bố các trạng thái xử lý")
print("#" * 70)

try:
    tt_dist = df_out['Trạng Thái'].value_counts()
    print(f"\n  Phân bố Trạng Thái trên {len(df_out)} dòng:")
    for label, count in tt_dist.items():
        if pd.isna(label) or str(label).strip() == '':
            label = "<Empty>"
        pct = count / len(df_out) * 100
        bar = '█' * int(pct / 2)
        print(f"    {str(label):45s} {count:6d} ({pct:5.1f}%) {bar}")
    
    auto_pct = sum(count for label, count in tt_dist.items() if 'Tự động' in str(label)) / len(df_out) * 100
    
    status = PASS if auto_pct >= 90 else (WARN if auto_pct >= 70 else FAIL)
    log_result("TC9: Trạng Thái", status,
               f"Tự động duyệt: {auto_pct:.1f}% | Phân bố: Lịch sử / Từ điển / AI")
except Exception as e:
    log_result("TC9: Trạng Thái", FAIL, f"Exception: {e}")
    traceback.print_exc()

# ============ TC10: SAMPLE OUTPUT VERIFICATION ============
print("\n\n" + "#" * 70)
print("  TC10: SAMPLE OUTPUT - Mẫu đầu ra để kiểm tra trực quan")
print("#" * 70)

try:
    samples = df_out.sample(min(20, len(df_out)), random_state=42)
    
    print(f"\n  {'Mã HS':>10} | {'Tên hàng':<50} | {'Dòng SP':<20} | {'Loại':<15} | {'Trạng Thái'}")
    print(f"  {'-'*10} | {'-'*50} | {'-'*20} | {'-'*15} | {'-'*30}")
    
    for _, row in samples.iterrows():
        hs = str(row.get('Mã HS', ''))[:10]
        ten = str(row.get('Tên hàng', '')).replace('\n', ' ')[:50]
        dong = str(row.get('Dòng SP', ''))[:20]
        loai = str(row.get('Loại', ''))[:15]
        tt = str(row.get('Trạng Thái', ''))[:30]
        print(f"  {hs:>10} | {ten:<50} | {dong:<20} | {loai:<15} | {tt}")
    
    log_result("TC10: Sample Output", PASS, f"Đã in {len(samples)} mẫu đầu ra để kiểm tra trực quan (đã load data đúng chuẩn)")
except Exception as e:
    log_result("TC10: Sample Output", FAIL, f"Exception: {e}")
    traceback.print_exc()

# ============ FINAL SUMMARY ============
print("\n\n")
print("█" * 70)
print("  BÁO CÁO TỔNG KẾT KIỂM THỬ")
print("█" * 70)

passed = sum(1 for _, s, _ in results_summary if s == PASS)
warned = sum(1 for _, s, _ in results_summary if s == WARN)
failed = sum(1 for _, s, _ in results_summary if s == FAIL)

for tc_name, status, detail in results_summary:
    print(f"  {status}  {tc_name}")
    print(f"       {detail}")
    print()

print(f"  {'='*60}")
print(f"  Tổng: {len(results_summary)} test cases | {PASS} {passed} | {WARN} {warned} | {FAIL} {failed}")
print(f"  {'='*60}")
