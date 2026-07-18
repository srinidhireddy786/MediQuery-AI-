import os
import sqlite3
import pandas as pd
from datetime import datetime

# Define database path
DB_PATH = r"C:\Users\Sriram reddy\.gemini\antigravity\scratch\healthcare_assistant\data\healthcare.db"

def init_db(db_path=DB_PATH):
    """
    Initializes the SQLite database and creates the normalized tables and indexes.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Create Patients table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        blood_type TEXT NOT NULL
    );
    """)
    
    # Create Doctors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)
    
    # Create Hospitals table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hospitals (
        hospital_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)
    
    # Create Admissions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admissions (
        admission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        hospital_id INTEGER NOT NULL,
        admission_date DATE NOT NULL,
        discharge_date DATE NOT NULL,
        room_number INTEGER NOT NULL,
        admission_type TEXT NOT NULL,
        medical_condition TEXT NOT NULL,
        medication TEXT NOT NULL,
        test_results TEXT NOT NULL,
        insurance_provider TEXT NOT NULL,
        billing_amount REAL NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
        FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
    );
    """)
    
    # Create indexes for efficient querying
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_admissions_patient_id ON admissions(patient_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_admissions_admission_date ON admissions(admission_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_admissions_medical_condition ON admissions(medical_condition);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_admissions_insurance_provider ON admissions(insurance_provider);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_admissions_test_results ON admissions(test_results);")
    
    conn.commit()
    conn.close()
    print("Database tables and indexes initialized successfully.")

def validate_and_clean_data(df):
    """
    Validates the dataframe for missing values, types, and logic consistency.
    """
    print("Validating data quality...")
    
    # 1. Check for missing values
    missing_counts = df.isnull().sum()
    print(f"Missing values count per column:\n{missing_counts}")
    
    # Fill or drop if necessary (dataset is synthetic, usually complete, but we add checks)
    df = df.dropna().copy()
    
    # 2. Standardize column names (remove leading/trailing spaces)
    df.columns = [col.strip() for col in df.columns]
    
    # 3. Parse and validate dates
    df['Date of Admission'] = pd.to_datetime(df['Date of Admission']).dt.date
    df['Discharge Date'] = pd.to_datetime(df['Discharge Date']).dt.date
    
    # Check date logical consistency
    invalid_dates = df[df['Discharge Date'] < df['Date of Admission']]
    if not invalid_dates.empty:
        print(f"WARNING: Found {len(invalid_dates)} records where Discharge Date is before Admission Date.")
        # Fix: Swap or filter out. For consistency, let's keep valid ones.
        df = df[df['Discharge Date'] >= df['Date of Admission']].copy()
    
    # 4. Standardize string types
    df['Name'] = df['Name'].str.strip()
    df['Doctor'] = df['Doctor'].str.strip()
    df['Hospital'] = df['Hospital'].str.strip()
    df['Medical Condition'] = df['Medical Condition'].str.strip()
    df['Medication'] = df['Medication'].str.strip()
    df['Insurance Provider'] = df['Insurance Provider'].str.strip()
    df['Admission Type'] = df['Admission Type'].str.strip()
    df['Test Results'] = df['Test Results'].str.strip()
    df['Blood Type'] = df['Blood Type'].str.strip()
    df['Gender'] = df['Gender'].str.strip()
    
    # 5. Correct types
    df['Age'] = df['Age'].astype(int)
    df['Room Number'] = df['Room Number'].astype(int)
    df['Billing Amount'] = df['Billing Amount'].astype(float)
    
    print(f"Data validation complete. Valid rows: {len(df)}")
    return df

def ingest_csv(csv_path, db_path=DB_PATH):
    """
    Ingests raw CSV data, normalizes it, and inserts it into SQLite.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at {csv_path}")
        
    df = pd.read_csv(csv_path)
    df = validate_and_clean_data(df)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    print("Ingesting doctors...")
    unique_doctors = df['Doctor'].unique()
    for doc in unique_doctors:
        cursor.execute("INSERT OR IGNORE INTO doctors (name) VALUES (?);", (doc,))
        
    print("Ingesting hospitals...")
    unique_hospitals = df['Hospital'].unique()
    for hosp in unique_hospitals:
        cursor.execute("INSERT OR IGNORE INTO hospitals (name) VALUES (?);", (hosp,))
        
    conn.commit()
    
    # Retrieve mapping lists to reduce query overhead during ingestion
    cursor.execute("SELECT doctor_id, name FROM doctors;")
    doctor_map = {name: doc_id for doc_id, name in cursor.fetchall()}
    
    cursor.execute("SELECT hospital_id, name FROM hospitals;")
    hospital_map = {name: hosp_id for hosp_id, name in cursor.fetchall()}
    
    # Process and Ingest Patients & Admissions
    print("Ingesting patients and admissions...")
    patient_map = {} # Maps (name, age, gender, blood_type) -> patient_id
    
    for idx, row in df.iterrows():
        p_key = (row['Name'], row['Age'], row['Gender'], row['Blood Type'])
        
        if p_key not in patient_map:
            # Check if patient already exists in DB
            cursor.execute("""
            SELECT patient_id FROM patients 
            WHERE name = ? AND age = ? AND gender = ? AND blood_type = ?;
            """, p_key)
            res = cursor.fetchone()
            if res:
                patient_id = res[0]
            else:
                cursor.execute("""
                INSERT INTO patients (name, age, gender, blood_type) 
                VALUES (?, ?, ?, ?);
                """, p_key)
                patient_id = cursor.lastrowid
            patient_map[p_key] = patient_id
        else:
            patient_id = patient_map[p_key]
            
        doc_id = doctor_map[row['Doctor']]
        hosp_id = hospital_map[row['Hospital']]
        
        # Insert admission
        cursor.execute("""
        INSERT INTO admissions (
            patient_id, doctor_id, hospital_id, admission_date, discharge_date,
            room_number, admission_type, medical_condition, medication,
            test_results, insurance_provider, billing_amount
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            patient_id, doc_id, hosp_id,
            str(row['Date of Admission']), str(row['Discharge Date']),
            row['Room Number'], row['Admission Type'], row['Medical Condition'],
            row['Medication'], row['Test Results'], row['Insurance Provider'],
            row['Billing Amount']
        ))
        
        if idx > 0 and idx % 2000 == 0:
            print(f"Processed {idx} records...")
            conn.commit()
            
    conn.commit()
    
    # Query summary count
    cursor.execute("SELECT COUNT(*) FROM patients;")
    p_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM admissions;")
    a_count = cursor.fetchone()[0]
    
    conn.close()
    print(f"Ingestion successful! Loaded {p_count} patients and {a_count} admissions.")

if __name__ == "__main__":
    init_db()
