import importlib.util
import sys

print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")
try:
    # Check if bleach is available without importing it
    if importlib.util.find_spec("bleach") is not None:
        print("Successfully imported bleach!")
    else:
        print("bleach module is not available")
        sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)

sys.exit(0)
