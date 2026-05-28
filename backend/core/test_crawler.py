import asyncio
import sys
import os

# Ensure the project root is on sys.path when run as a module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.core.crawler import crawl_hs_code

async def main():
    test_codes = [
        "85395210", # Valid code
        "85395220", # Valid code
        "90012000", # Sheets and plates of polarising material
        "74061000", # Copper powders of non-lamellar structure
        "99999999", # Invalid/Unknown code
    ]
    
    print("Testing HS Code Crawler...")
    for code in test_codes:
        print(f"\nCrawling HS Code: {code}")
        result = await crawl_hs_code(code)
        if result:
            print(f"Success! Result:")
            for k, v in result.items():
                print(f"  {k}: {v}")
        else:
            print("Failed to find description.")

if __name__ == "__main__":
    asyncio.run(main())
