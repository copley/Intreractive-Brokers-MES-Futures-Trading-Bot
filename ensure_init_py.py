import os

def ensure_init_py(directory):
    """
    Recursively traverse directories and ensure each folder contains an __init__.py file.
    """
    for root, dirs, files in os.walk(directory):
        if any(fname.endswith(".py") for fname in files) or dirs:
            init_file = os.path.join(root, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    pass  # Create an empty __init__.py file
                print(f"Created: {init_file}")

if __name__ == "__main__":
    root_dir = os.getcwd()  # Use current working directory
    ensure_init_py(root_dir)

