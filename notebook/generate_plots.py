
import os
import pandas as pd
import matplotlib.pyplot as plt

def generate_analytics():
    csv_path = os.path.join("data", "test_runs.csv")
    
    if not os.path.exists(csv_path):
        print(f"[-] Data log sheet not found at {csv_path}. Run the fuzzer pipeline first.")
        return
        
    print(f"[*] Ingesting raw telemetry datasets out of {csv_path}...")
    df = pd.read_csv(csv_path)
    
    if df.empty:
        print("[-] Data log file is empty. No telemetry metrics to graph.")
        return

    os.makedirs("notebooks", exist_ok=True)

    plt.rcParams['text.color'] = '#f8fafc'
    plt.rcParams['axes.labelcolor'] = '#94a3b8'
    plt.rcParams['xtick.color'] = '#94a3b8'
    plt.rcParams['ytick.color'] = '#94a3b8'

    print("[*] Compiling Anomaly Frequency Distribution Chart...")
    plt.figure(figsize=(10, 6), facecolor='#0b0f19')
    ax1 = plt.gca()
    ax1.set_facecolor('#151d30')
    
    anomaly_counts = df['Anomaly Group'].value_counts()
    anomaly_counts.plot(kind='bar', color='#ef4444', edgecolor='#b91c1c', width=0.6, zorder=3)
    
    plt.title('Discovered Vulnerability Classification Frequency', fontsize=14, fontweight='bold', pad=15, color='#f8fafc')
    plt.xlabel('Vulnerability Classification Anomaly Group', fontsize=11, labelpad=10)
    plt.ylabel('Total Incident Hits Count', fontsize=11, labelpad=10)
    plt.xticks(rotation=35, ha='right', fontsize=9)
    plt.grid(True, linestyle='--', alpha=0.1, color='#94a3b8', zorder=1)
    
    for spine in ['top', 'right', 'left', 'bottom']:
        ax1.spines[spine].set_color('#233554')
        
    plt.tight_layout()
    plot1_path = os.path.join("notebooks", "vulnerability_distribution.png")
    plt.savefig(plot1_path, dpi=300, facecolor='#0b0f19')
    plt.close()
    print(f"[+] Distribution bar chart successfully exported: {plot1_path}")

    print("[*] Compiling Telemetry Timeline Scatter Map Matrix...")
    plt.figure(figsize=(12, 6), facecolor='#0b0f19')
    ax2 = plt.gca()
    ax2.set_facecolor('#151d30')
    
    df_sorted = df.sort_values(by='Time').reset_index(drop=True)
    
    plt.scatter(
        df_sorted['Time'], 
        df_sorted['Status'], 
        color='#38bdf8', 
        alpha=0.5, 
        edgecolors='#0284c7', 
        s=50, 
        linewidths=0.8,
        zorder=3
    )
    
    plt.title('Microservice Status Responses Distribution Over Session Timeline', fontsize=14, fontweight='bold', pad=15, color='#f8fafc')
    plt.xlabel('Execution Timeline Stamp (IST Clock Zone Target)', fontsize=11, labelpad=12)
    plt.ylabel('HTTP Server Protocol Response Code Status', fontsize=11, labelpad=10)
    
    plt.ylim(-50, 550)
    plt.yticks([0, 200, 400, 413, 429, 500])
    
    total_records = len(df_sorted)
    target_ticks_count = 10
    stride_step = max(1, total_records // target_ticks_count)
    
    sampled_indices = range(0, total_records, stride_step)
    sampled_labels = [df_sorted['Time'].iloc[i] for i in sampled_indices]
    
    ax2.set_xticks(list(sampled_indices))
    ax2.set_xticklabels(sampled_labels, rotation=45, ha='right', fontsize=9)
    
    plt.grid(True, linestyle='--', alpha=0.1, color='#94a3b8', zorder=1)
    
    for spine in ['top', 'right', 'left', 'bottom']:
        ax2.spines[spine].set_color('#233554')
        
    plt.tight_layout()
    plot2_path = os.path.join("notebooks", "telemetry_timeline.png")
    plt.savefig(plot2_path, dpi=300, facecolor='#0b0f19')
    plt.close()
    print(f"[+] Operational timeline tracking plot successfully exported: {plot2_path}")

if __name__ == "__main__":
    generate_analytics()


