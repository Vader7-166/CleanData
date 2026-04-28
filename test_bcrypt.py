from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    hash = pwd_context.hash("123")
    print(hash)
except Exception as e:
    import traceback
    traceback.print_exc()
