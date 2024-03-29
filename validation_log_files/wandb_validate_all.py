#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 13:30:33 2024

@author: apratimdey
"""

import re
import csv
import os

log_files_directory = './orig_log_files'  # Directory containing the log files
output_directory = './validation_files'  # Directory to save the output CSV files
pattern = re.compile(r'\[Validate\] Iter (\d+) \| Loss ([\d.]+) \| Loss\(Global\) ([\d.]+) \| Loss\(Local\) ([\d.]+)')

# Create output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Iterate over all log files in the directory
for filename in os.listdir(log_files_directory):
    if filename.endswith(".log"):  # Ensures processing only log files
        log_file_path = os.path.join(log_files_directory, filename)
        csv_file_path = os.path.join(output_directory, f"{os.path.splitext(filename)[0]}_validation_loss.csv")

        with open(log_file_path, 'r') as log_file, open(csv_file_path, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            # Writing header row to CSV
            csv_writer.writerow(['Iteration', 'Total Loss', 'Global Loss', 'Local Loss'])
            
            for line in log_file:
                match = pattern.search(line)
                if match:
                    # Extracting iteration, total loss, global loss, and local loss from the line
                    iteration, total_loss, global_loss, local_loss = match.groups()
                    # Writing extracted data to CSV
                    csv_writer.writerow([iteration, total_loss, global_loss, local_loss])
        
        print(f"Validation loss data extracted and saved for {filename}")

print("All files processed.")
