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
    './validation_files/output_aug_1_validation_loss.csv',
    './validation_files/output_aug_2_validation_loss.csv',
    './validation_files/output_aug_3_validation_loss.csv',
    './validation_files/output_aug_4_validation_loss.csv',
    './validation_files/output_aug_5_validation_loss.csv'
]

# Custom legend labels for each CSV file
legend_labels = {
    'output_baseline_20K_validation_loss.csv': 'Baseline 20K',
    'output_baseline_40K_validation_loss.csv': 'Baseline 40K',
    'output_aug_1_validation_loss.csv': 'Accumulate 1',
    'output_aug_2_validation_loss.csv': 'Accumulate 2',
    'output_aug_3_validation_loss.csv': 'Accumulate 3',
    'output_aug_4_validation_loss.csv': 'Accumulate 4',
    'output_aug_5_validation_loss.csv': 'Accumulate 5',
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

plt.title('Accumulate', fontsize = 20)
plt.xlabel('Training Step', fontsize = 18)
plt.ylabel('Validation Loss', fontsize = 18)
plt.grid(True)
plt.legend(title='Experiment', title_fontsize='18', fontsize='16')
plt.xticks(fontsize=13)
plt.yticks(fontsize=13)
plt.ylim(None, 700)
plt.tight_layout()

# Specify the path and filename where you want to save the plot
plot_filename = 'accumulate_plot.png'
plt.savefig(plot_filename, dpi=300, bbox_inches='tight')

plt.show()
