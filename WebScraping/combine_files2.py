import os
import urllib.parse

def get_sort_key(filename):
    """
    Extracts the URL path from the filename and creates a sort key
    based on its structure.
    """
    parts = filename.replace("https_", "").replace("http_", "").split("_")
    if len(parts) > 1:
        domain_and_path = "_".join(parts[1:])
        path_segments = [p for p in domain_and_path.split("_") if p and p != "txt"]
        return (len(path_segments), path_segments)
    else:
        return (0, [filename])

def combine_text_files_ordered_by_url(directory_path, output_filename="combined_text.txt"):
    """
    Combines all .txt files in a given directory into a single text file,
    ordered based on the URL structure inferred from the filenames.

    Args:
        directory_path (str): The path to the directory containing the text files.
        output_filename (str, optional): The name of the output file.
                                       Defaults to "combined_text.txt".
    """
    all_text_files = [f for f in os.listdir(directory_path) if f.endswith(".txt")]

    # Sort the files based on the URL structure
    sorted_files = sorted(all_text_files, key=get_sort_key)

    combined_content = ""
    for filename in sorted_files:
        filepath = os.path.join(directory_path, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                combined_content += f"-- Start of {filename} --\n"
                combined_content += content
                combined_content += "\n-- End of {filename} --\n\n"
        except Exception as e:
            print(f"Error reading file {filename}: {e}")

    try:
        output_filepath = os.path.join(directory_path, output_filename)
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(combined_content)
        print(f"Successfully combined {len(sorted_files)} text files into {output_filename} in {directory_path}, ordered by URL structure.")
    except Exception as e:
        print(f"Error writing to output file {output_filename}: {e}")

if __name__ == "__main__":
    directory_to_combine = input("Enter the path to the directory containing the scraped text files: ")
    output_name = input("Enter the desired name for the combined text file (e.g., combined_output.txt): ")
    combine_text_files_ordered_by_url(directory_to_combine, output_name)