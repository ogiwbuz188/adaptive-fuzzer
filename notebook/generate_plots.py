
import os
import pandas as pd
import matplotlib.pyplot as plt

def generate_analytics():
    csv_path = os.path.join("data", "test_runs.csv")
    
    if not os.path.exists(csv_path):
        print(f"[-] Data log sheet not found at {csv_path}. Run the fuzzer pipeline first.")
        return
        
    print(f"[*] Reading runtime telemetry datasets out of {csv_path}...")
    df = pd.read_csv(csv_path)
    
    if df.empty:
        print("[-] Data log file is empty. No telemetry metrics to graph.")
        return

    # Create directories for saving visual outputs
    os.makedirs("notebooks", exist_ok=True)

    # Chart 1: Anomaly Frequency Breakdown Bar Chart
    plt.figure(figsize=(10, 6))
    anomaly_counts = df['Anomaly Group'].value_counts()
    anomaly_counts.plot(kind='bar', color='#ef4444', edgecolor='#1e293b')
    plt.title('Discovered Vulnerability Classification Frequency', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Vulnerability Classification', fontsize=11, labelpad=10)
    plt.ylabel('Total Occurrences Count', fontsize=11, labelpad=10)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    plot1_path = os.path.join("notebooks", "vulnerability_distribution.png")
    plt.savefig(plot1_path, dpi=300)
    plt.close()
    print(f"[+] Distribution bar chart successfully exported to {plot1_path}")

    # Chart 2: Latency Spikes Timeline Plot
    plt.figure(figsize=(12, 5))
    df_sorted = df.sort_values(by='Time')
    plt.plot(df_sorted['Time'], df_sorted['Status'], color='#38bdf8', marker='o', linestyle='-', linewidth=2, markersize=6)
    plt.title('Microservice Lifecycle Code Response Over Timeline Sequence', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Execution Timeline Stamp (IST)', fontsize=11, labelpad=10)
    plt.ylabel('HTTP Server Status Returns', fontsize=11, labelpad=10)
    plt.xticks(rotation=90)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    
    plot2_path = os.path.join("notebooks", "telemetry_timeline.png")
    plt.savefig(plot2_path, dpi=300)
    plt.close()
    print(f"[+] Operational latency tracking plot successfully exported to {plot2_path}")

if __name__ == "__main__":
    generate_analytics()
