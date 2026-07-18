import sys
import os

# Add src directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, ingest_csv, DB_PATH

def main():
    csv_path = r"C:\Users\Sriram reddy\.gemini\antigravity\scratch\healthcare_assistant\data\raw\healthcare_dataset.csv"
    print("Initializing Database...")
    init_db(DB_PATH)
    
    print(f"Ingesting CSV data from {csv_path}...")
    ingest_csv(csv_path, DB_PATH)
    
    print("Database preparation and ingestion completed successfully!")

if __name__ == "__main__":
    main()
