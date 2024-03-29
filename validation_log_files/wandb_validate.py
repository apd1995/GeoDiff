#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 12:59:55 2024

@author: apratimdey
"""

import re
import csv

log_file_path = './output_baseline_20K.txt'  # Adjust this to your log file's path
csv_file_path = './output_validation_loss_baseline_20K.csv'  # Adjust this to where you want the CSV file saved

# Regex to match validation loss lines and capture relevant parts
pattern = re.compile(r'\[Validate\] Iter (\d+) \| Loss ([\d.]+) \| Loss\(Global\) ([\d.]+) \| Loss\(Local\) ([\d.]+)')

# Open log file and CSV file
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

print(f'Validation loss data has been extracted and saved to {csv_file_path}')
