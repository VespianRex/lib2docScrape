import sys
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")
try:
    import bleach
    print("Successfully imported bleach!")
except ImportError as e:
    print(f"Failed to import bleach: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)

sys.exit(0)