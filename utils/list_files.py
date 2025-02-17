import os

def list_files(directory="."):
    """
    List all files and directories starting from the given directory.
    Returns a formatted string of the directory tree.
    """
    output_lines = []
    for root, dirs, files in os.walk(directory):
        level = root.replace(directory, "").count(os.sep)
        indent = "    " * level
        folder_name = os.path.basename(root) if root != directory else directory
        output_lines.append(f"{indent}{folder_name}/")
        for file in files:
            output_lines.append(f"{indent}    {file}")
    return "\n".join(output_lines)

if __name__ == "__main__":
    # If run as a script, print the file structure of the current directory (my_scalp_bot)
    print(list_files("."))
