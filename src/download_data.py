import os
import urllib.request
import pandas as pd

def main():
    urls = [
        "https://raw.githubusercontent.com/imranbdcse/healthcaredatasets/master/healthcare_dataset.csv",
        "https://raw.githubusercontent.com/imranbdcse/healthcaredatasets/main/healthcare_dataset.csv"
    ]
    dest_dir = r"C:\Users\Sriram reddy\.gemini\antigravity\scratch\healthcare_assistant\data\raw"
    dest_path = os.path.join(dest_dir, "healthcare_dataset.csv")
    
    os.makedirs(dest_dir, exist_ok=True)
    
    success = False
    for url in urls:
        print(f"Trying to download dataset from {url}...")
        try:
            urllib.request.urlretrieve(url, dest_path)
            print(f"Downloaded successfully to {dest_path}")
            
            # Verify the CSV
            df = pd.read_csv(dest_path)
            print("Dataset columns:")
            print(df.columns.tolist())
            print(f"Total rows: {len(df)}")
            print("\nFirst 3 rows:")
            print(df.head(3))
            success = True
            break
        except Exception as e:
            print(f"Failed download from {url}: {e}")
            
    if not success:
        print("Could not download the dataset from either branch URL.")

if __name__ == "__main__":
    main()
