import os
import tkinter as tk
from tkinter import filedialog
import logging

# Setting up logging
logging.basicConfig(filename='delete_lrv_thm.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def delete_files(directory):
    """
    Recursively delete all .lrv and .thm files in the specified directory and its subdirectories.
    """
    if not os.path.isdir(directory):
        print(f"Invalid directory: {directory}")
        logging.error(f"Invalid directory: {directory}")
        return

    file_found = False
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.lrv') or file.lower().endswith('.thm'):
                file_found = True
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    logging.info(f"Deleted file: {file_path}")
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    logging.error(f"Error deleting file: {file_path}. Error: {str(e)}")
                    print(f"Error deleting: {file_path}. Error: {str(e)}")

    if not file_found:
        print("No .lrv or .thm files found.")
        logging.info("No .lrv or .thm files found.")

def select_directory():
    """
    Open a dialog to select a directory.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    selected_dir = filedialog.askdirectory(title="Select Directory to Clean Up")
    if selected_dir:
        print(f"Selected directory: {selected_dir}")
        logging.info(f"Selected directory: {selected_dir}")
        delete_files(selected_dir)
    else:
        print("No directory selected. Exiting.")
        logging.info("No directory selected.")

if __name__ == "__main__":
    select_directory()