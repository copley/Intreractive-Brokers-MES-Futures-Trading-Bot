import os

def write_python_files_to_output(output_filename="output.txt"):
    root_dir = os.getcwd()
    output_path = os.path.join(root_dir, output_filename)
    
    with open(output_path, "w", encoding="utf-8") as output_file:
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.endswith(".py"):  # Only process Python files
                    file_path = os.path.join(dirpath, filename)
                    
                    # Write file separator
                    output_file.write(f"\n# File: {file_path}\n")
                    output_file.write("#" * 80 + "\n\n")
                    
                    # Read and write file content
                    try:
                        with open(file_path, "r", encoding="utf-8") as py_file:
                            output_file.write(py_file.read())
                    except Exception as e:
                        output_file.write(f"\n# ERROR READING FILE: {e}\n")
                    
                    output_file.write("\n" + "#" * 80 + "\n")
    
    print(f"All Python files have been written to {output_filename}")

if __name__ == "__main__":
    write_python_files_to_output()

