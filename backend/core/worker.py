import pandas as pd
import re

# Global dictionary matcher instance for the worker process
matcher = None

def init_worker(dict_path):
    global matcher
    from backend.core.dictionary_matcher import DictionaryMatcher
    matcher = DictionaryMatcher(dict_path=dict_path)

def trich_xuat_thong_tin(raw_text):
    raw_text = str(raw_text)
    if '#&' in raw_text:
        parts = raw_text.split('#&')
        parts = [p.strip() for p in parts if p.strip()]
        if parts:
            raw_text = max(parts, key=len)

    raw_text_lower = raw_text.lower()
    cong_suat = ""
    match_w = re.search(r'(\d+(?:\.\d+)?)\s*(w|watt|hp|kw|kva|v)', raw_text_lower)
    if match_w:
        cong_suat = match_w.group(0).strip()

    hang = ""
    danh_sach_hang = ['rạng đông', 'điện quang', 'panasonic', 'philips', 'lg', 'samsung', 'daikin', 'sony', 'toshiba', 'sharp', 'sino', 'cadivi']
    for h in danh_sach_hang:
        if h in raw_text_lower:
            hang = h.capitalize()
            break
    return hang, cong_suat, raw_text

def process_chunk(chunk_df):
    """
    chunk_df contains 'Tên hàng raw'.
    Returns a dataframe containing:
    'Hãng', 'Công suất', 'Tên hàng', 'input_for_ai', 'Ket_Qua_Gop', 'Độ Tự Tin (%)', 'Trạng Thái'
    """
    global matcher
    
    # 1. Trich xuat thong tin
    extracted = chunk_df['Tên hàng raw'].apply(lambda x: pd.Series(trich_xuat_thong_tin(x)))
    if extracted.empty:
        extracted = pd.DataFrame(columns=[0, 1, 2])
    
    extracted.columns = ['Hãng', 'Công suất', 'Tên hàng']
    
    # 2. Prepare input for AI & Dict
    input_for_ai = "Hãng: " + extracted['Hãng'].astype(str) + " - Công suất: " + extracted['Công suất'].astype(str) + " - Sản phẩm: " + extracted['Tên hàng'].astype(str).str.lower()
    input_for_ai = input_for_ai.apply(matcher.clean_text_for_dict)
    
    # 3. Predict with DictionaryMatcher
    dict_predictions = input_for_ai.apply(matcher.predict)
    dict_predictions.columns = ['Ket_Qua_Gop', 'Độ Tự Tin (%)', 'Trạng Thái']
    
    # Concatenate all results
    result_df = pd.concat([extracted, input_for_ai.rename('input_for_ai'), dict_predictions], axis=1)
    return result_df
