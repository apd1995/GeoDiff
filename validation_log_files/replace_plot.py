import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Plot Smoothed Validation Loss')
parser.add_argument('--window_size', type=int, default=5, help='Window size for smoothing')
args = parser.parse_args()

# Your list of CSV file paths
csv_files = [
    './validation_files/output_baseline_20K_validation_loss.csv',
    './validation_files/output_baseline_40K_validation_loss.csv',
    './validation_files/output_rep_1_validation_loss.csv',
    './validation_files/output_rep_2_validation_loss.csv',
    './validation_files/output_rep_3_validation_loss.csv',
    './validation_files/output_rep_4_validation_loss.csv',
    './validation_files/output_rep_5_validation_loss.csv'
]

# Custom legend labels for each CSV file
legend_labels = {
    'output_baseline_20K_validation_loss.csv': 'Baseline 20K',
    'output_baseline_40K_validation_loss.csv': 'Baseline 40K',
    'output_rep_1_validation_loss.csv': 'Replace 1',
    'output_rep_2_validation_loss.csv': 'Replace 2',
    'output_rep_3_validation_loss.csv': 'Replace 3',
    'output_rep_4_validation_loss.csv': 'Replace 4',
    'output_rep_5_validation_loss.csv': 'Replace 5',
}

plt.figure(figsize=(12, 8))

for csv_file in csv_files:
    filename = os.path.basename(csv_file)
    df = pd.read_csv(csv_file)
    df['Iteration'] = df['Iteration'].astype(int)
    
    df = df[df['Iteration'] <= 41000]
    
    # Apply smoothing with the specified window size
    df['Smoothed Local Loss'] = df['Local Loss'].rolling(window=args.window_size).mean()

    label = legend_labels.get(filename, "Unknown")  # Get custom label

    sns.lineplot(data=df, x='Iteration', y='Smoothed Local Loss', label=label)

plt.title('Replace', fontsize = 24)
plt.xlabel('Training Step', fontsize = 22)
plt.ylabel('Validation Loss', fontsize = 22)
plt.grid(True)
plt.legend(title='Experiment', title_fontsize='22', fontsize='20')
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.ylim(None, 700)
plt.tight_layout()

# Specify the path and filename where you want to save the plot
plot_filename = 'replace_plot.png'
plt.savefig(plot_filename, dpi=300, bbox_inches='tight')

plt.show()
