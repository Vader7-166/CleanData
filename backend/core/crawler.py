"""
Online HS Code Crawler Module.

Attempts to look up HS code descriptions from public customs directories.
Falls back gracefully if the lookup fails (the UI will prompt the user).
"""
import httpx
import re
import os
import json
from bs4 import BeautifulSoup
from typing import Optional, Dict

# Keywords used to infer NC (Nguyên chiếc) vs LK (Linh kiện)
LK_INDICATOR_KEYWORDS = [
    'bộ phận', 'linh kiện', 'phụ tùng', 'phụ kiện', 'nắp', 'vỏ',
    'lõi', 'ruột', 'đui', 'chấn lưu', 'driver', 'mạch', 'module',
    'mô-đun', 'điện trở', 'tấm', 'khung', 'đế', 'ống', 'khuôn',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
}

# Mapping 4-digit HS chapter prefixes to product line names
DONG_SP_FALLBACK = {
    '9617': 'SP BÌNH/PHÍCH',
    '7020': 'SP THỦY TINH',
    '8539': 'SP ĐÈN/BÓNG ĐÈN',
    '9405': 'SP ĐÈN/THIẾT BỊ CHIẾU SÁNG',
    '8516': 'SP THIẾT BỊ ĐIỆN GIA DỤNG',
}


def infer_default_type(description: str) -> str:
    """Infer NC (finished product) or LK (component) from description text."""
    desc_lower = description.lower()
    hits = sum(1 for kw in LK_INDICATOR_KEYWORDS if kw in desc_lower)
    return 'LK' if hits >= 1 else 'NC'


def clean_dong_sp_description(desc: str) -> str:
    """Clean the Heading description to serve as a Product Line (dong_sp) name."""
    if not desc:
        return ""
    # Remove content inside parentheses to avoid unbalanced brackets
    clean = re.sub(r'\(.*?\)', '', desc)
    # Split by common conjunctions or separators
    parts = re.split(r'[;,]|\bhoặc\b|\bkể cả\b|\bdùng cho\b|\bdùng để\b', clean, flags=re.IGNORECASE)
    first_part = parts[0].strip()
    # Clean leading/trailing non-alphanumeric chars
    first_part = re.sub(r'^\W+|\W+$', '', first_part)
    first_part = re.sub(r'\s+', ' ', first_part).strip()
    
    if len(first_part) > 3:
        return f"SP {first_part.upper()}"
    return f"SP {desc.split()[0].upper()}"


def clean_industry_name(desc: str) -> str:
    """Clean full HS description for Lớp 1 (industry_name) by removing English suffixes."""
    if not desc:
        return ""
    # Remove English descriptions in parens (e.g. "(Other LED lamps)")
    def remove_english_parens(match):
        content = match.group(1)
        has_vietnamese = bool(re.search(r'[àáảãạăắằẳẵặâấầẩẫậèéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợùúụủũưừứựửữỳýỵỷỹđ]', content, re.IGNORECASE))
        if not has_vietnamese and len(content) > 3:
            return ""
        return match.group(0)
    
    cleaned = re.sub(r'\((.*?)\)', remove_english_parens, desc)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'^\W+|\W+$', '', cleaned)
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def infer_dong_sp(hs_code: str) -> str:
    """Infer the product line from the 4-digit prefix of the HS code."""
    prefix4 = hs_code[:4]
    if prefix4 in DONG_SP_FALLBACK:
        return DONG_SP_FALLBACK[prefix4]
        
    try:
        from backend.main import hs_customs_cache
        if prefix4 in hs_customs_cache:
            desc = hs_customs_cache[prefix4].get("description_vn")
            if desc:
                return clean_dong_sp_description(desc)
    except Exception:
        pass
    return f'SP {prefix4}'




async def crawl_hs_code(hs_code: str) -> Optional[Dict[str, str]]:
    """
    Attempt to look up an HS code description from public sources.
    
    Returns a dict with keys: hs_code_prefix, dong_sp, industry_name, default_type
    or None if lookup fails.
    """
    # Clean HS code: remove dots and non-digits
    clean_code = re.sub(r'\D', '', str(hs_code))
    if not clean_code or len(clean_code) < 4:
        return None

    description = None
    dong_sp_desc = None

    # Strategy 1: Try hscode.pro.vn
    try:
        description = await _crawl_hscode_pro(clean_code)
    except Exception as e:
        print(f"DEBUG Crawler: hscode.pro.vn failed for {clean_code}: {e}")

    # Strategy 2: Try customs.gov.vn search  
    if not description:
        try:
            description = await _crawl_customs_gov(clean_code)
        except Exception as e:
            print(f"DEBUG Crawler: customs.gov.vn failed for {clean_code}: {e}")

    # Strategy 3: Try DeepSeek LLM fallback
    if not description:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if api_key:
            try:
                from openai import AsyncOpenAI
                prompt = f"""Bạn là một chuyên gia về hải quan và phân loại hàng hóa xuất nhập khẩu Việt Nam. 
Hãy cho biết thông tin phân loại hải quan chính thức (theo Danh mục hàng hóa xuất nhập khẩu Việt Nam) cho mã HS {clean_code}.

Hãy trả về kết quả ở định dạng JSON với cấu trúc sau:
{{
  "dong_sp_desc": "Mô tả ngắn gọn tiếng Việt của nhóm 4 số đầu (Heading) của mã HS này. Ví dụ với 85395210 thì nhóm 4 số là 8539: Bóng đèn điện dây tóc hoặc bóng đèn phóng điện",
  "industry_name": "Mô tả chi tiết bằng tiếng Việt của riêng mã HS 8-số cụ thể này (leaf node). YÊU CẦU: Phải là mô tả cụ thể nhất của mã 8-số này trong biểu thuế. KHÔNG ĐƯỢC sao chép mô tả chung của nhóm 4-số (Heading) hay nhóm cha lớn hơn nếu phân nhóm 8-số có định nghĩa riêng chi tiết hơn. Ví dụ: mã 90012000 là 'Vật liệu phân cực dạng tấm và lá' (không được trả về 'Thấu kính, lăng kính...'), mã 74061000 là 'Bột không cấu trúc lớp' (không được nhầm với cấu trúc dạng phiến)."
}}

CHỈ trả về JSON hợp lệ, KHÔNG GIẢI THÍCH."""

                client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                
                resp = await client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                
                content = resp.choices[0].message.content.strip()
                js_data = json.loads(content)
                description = js_data.get("industry_name")
                dong_sp_desc = js_data.get("dong_sp_desc")
                print(f"DEBUG Crawler: DeepSeek successfully resolved HS code {clean_code}")
            except Exception as e:
                print(f"DEBUG Crawler: DeepSeek API failed for {clean_code}: {e}")

    if not description:
        return None

    # Fetch Heading level description for Dòng SP if not yet resolved
    prefix4 = clean_code[:4]
    if not dong_sp_desc:
        try:
            dong_sp_desc = await _crawl_hscode_pro(prefix4)
        except Exception as e:
            print(f"DEBUG Crawler: hscode.pro.vn failed for prefix {prefix4}: {e}")
            
        if not dong_sp_desc:
            try:
                dong_sp_desc = await _crawl_customs_gov(prefix4)
            except Exception as e:
                print(f"DEBUG Crawler: customs.gov.vn failed for prefix {prefix4}: {e}")

    if dong_sp_desc:
        dong_sp = clean_dong_sp_description(dong_sp_desc)
    else:
        dong_sp = infer_dong_sp(clean_code)

    cleaned_description = clean_industry_name(description)

    return {
        'hs_code_prefix': clean_code,
        'dong_sp': dong_sp,
        'industry_name': cleaned_description,
        'default_type': infer_default_type(cleaned_description),
    }


async def _crawl_hscode_pro(hs_code: str) -> Optional[str]:
    """Scrape HS description from hscode.pro.vn."""
    url = f"https://hscode.pro.vn/tra-cuu?q={hs_code}"
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=HEADERS)
        if resp.status_code != 200:
            return None

    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Look for table rows containing the HS code
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            code_cell = cells[0].get_text(strip=True).replace('.', '')
            if code_cell == hs_code:
                desc = cells[1].get_text(strip=True)
                if desc and len(desc) > 3:
                    return desc
    
    # Fallback: look for any description text near the HS code
    text = soup.get_text()
    # Find Vietnamese description near the full code
    pattern = re.compile(
        rf'{re.escape(hs_code)}[.\d]*\s*[-–:]\s*(.{{10,120}})',
        re.IGNORECASE
    )
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    
    return None


async def _crawl_customs_gov(hs_code: str) -> Optional[str]:
    """Scrape HS description from customs.gov.vn search."""
    url = f"https://www.customs.gov.vn/SitePages/Tariff.aspx?keyword={hs_code}"
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=HEADERS)
        if resp.status_code != 200:
            return None

    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Look for result table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 3:
            code_cell = cells[0].get_text(strip=True).replace('.', '')
            if code_cell == hs_code:
                desc = cells[2].get_text(strip=True)
                if desc and len(desc) > 3:
                    return desc
    
    return None


async def crawl_multiple_hs_codes(hs_codes: list[str]) -> Dict[str, Optional[Dict[str, str]]]:
    """
    Attempt to crawl descriptions for multiple HS codes.
    Returns a dict mapping hs_code -> result dict or None.
    """
    results = {}
    for code in hs_codes:
        result = await crawl_hs_code(code)
        results[code] = result
    return results
