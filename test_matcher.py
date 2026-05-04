import time
from backend.core.dictionary_matcher import DictionaryMatcher

def test():
    t0 = time.time()
    matcher = DictionaryMatcher()
    print(f"Loaded DictionaryMatcher in {time.time() - t0:.4f}s")
    
    text = "viền trang trí camera"
    t1 = time.time()
    res = matcher.predict(text)
    print(f"Prediction for '{text}':")
    print(res)
    print(f"Prediction time: {time.time() - t1:.6f}s")

    # Edge cases
    text2 = "đèn led 10w"
    res2 = matcher.predict(text2)
    print(f"Prediction for '{text2}':\n{res2}")
    
if __name__ == '__main__':
    test()
