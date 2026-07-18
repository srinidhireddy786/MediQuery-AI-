import sqlite3
import pandas as pd
from src import config
from src.llm_client import call_llm

class SQLAgent:
    """
    NLP-to-SQL Agent: Translates natural language questions into SQL queries,
    runs them on the database, and returns the query output and SQL statement.
    """
    def __init__(self, db_path=config.DB_PATH):
        self.db_path = db_path
        self.schema_info = (
            "Database: SQLite3\n"
            "Tables Schema:\n"
            "1. patients (\n"
            "   patient_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "   name TEXT NOT NULL,\n"
            "   age INTEGER NOT NULL,\n"
            "   gender TEXT NOT NULL, -- e.g., 'Male', 'Female'\n"
            "   blood_type TEXT NOT NULL -- e.g., 'A+', 'O-', 'AB+', 'B+' etc.\n"
            ")\n"
            "2. doctors (\n"
            "   doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "   name TEXT NOT NULL UNIQUE\n"
            ")\n"
            "3. hospitals (\n"
            "   hospital_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "   name TEXT NOT NULL UNIQUE\n"
            ")\n"
            "4. admissions (\n"
            "   admission_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "   patient_id INTEGER NOT NULL, -- Foreign Key to patients(patient_id)\n"
            "   doctor_id INTEGER NOT NULL,  -- Foreign Key to doctors(doctor_id)\n"
            "   hospital_id INTEGER NOT NULL, -- Foreign Key to hospitals(hospital_id)\n"
            "   admission_date DATE NOT NULL, -- format: 'YYYY-MM-DD'\n"
            "   discharge_date DATE NOT NULL, -- format: 'YYYY-MM-DD'\n"
            "   room_number INTEGER NOT NULL,\n"
            "   admission_type TEXT NOT NULL, -- e.g., 'Emergency', 'Elective', 'Urgent'\n"
            "   medical_condition TEXT NOT NULL, -- e.g., 'Diabetes', 'Obesity', 'Cancer', 'Asthma', 'Heart Disease', 'Hypertension'\n"
            "   medication TEXT NOT NULL, -- e.g., 'Aspirin', 'Ibuprofen', 'Lipitor', 'Penicillin', 'Paracetamol'\n"
            "   test_results TEXT NOT NULL, -- e.g., 'Normal', 'Abnormal', 'Inconclusive'\n"
            "   insurance_provider TEXT NOT NULL, -- e.g., 'Medicare', 'Blue Cross', 'Aetna', 'Cigna', 'UnitedHealthcare'\n"
            "   billing_amount REAL NOT NULL,\n"
            "   FOREIGN KEY (patient_id) REFERENCES patients(patient_id),\n"
            "   FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),\n"
            "   FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)\n"
            ")\n\n"
            "Joins:\n"
            "- Join admissions with patients on admissions.patient_id = patients.patient_id\n"
            "- Join admissions with doctors on admissions.doctor_id = doctors.doctor_id\n"
            "- Join admissions with hospitals on admissions.hospital_id = hospitals.hospital_id\n\n"
            "Rules:\n"
            "1. Output ONLY the raw SQL query. Do not wrap in markdown quotes, no triple backticks, no explaining text.\n"
            "2. Ensure dates are compared as text (e.g. admission_date >= '2024-01-01' and admission_date <= '2024-01-31').\n"
            "3. Limit results to a maximum of 50 rows unless an aggregation (COUNT, AVG) is requested.\n"
            "4. Be case-insensitive or exact according to values (e.g. medical_condition = 'Diabetes')."
        )
        self.system_instruction = (
            "You are an expert NLP-to-SQL Agent. Convert the user's medical or patient query into a syntactically correct SQLite query based on the schema.\n"
            f"{self.schema_info}"
        )

    def generate_sql(self, query: str) -> str:
        """
        Translates natural language to SQL using LLM.
        """
        response = call_llm(
            prompt=f"""
            You are an expert SQLite SQL generator.

            Database Schema

            patients(
                patient_id,
                name,
                age,
                gender,
                blood_type
            )

            doctors(
                doctor_id,
                name
            )

            hospitals(
                hospital_id,
                name
            )

            admissions(
                admission_id,
                patient_id,
                doctor_id,
                hospital_id,
                admission_date,
                discharge_date,
                room_number,
                admission_type,
                medical_condition,
                medication,
                test_results,
                insurance_provider,
                billing_amount
            )

            Relationships

            admissions.patient_id = patients.patient_id
            admissions.doctor_id = doctors.doctor_id
            admissions.hospital_id = hospitals.hospital_id

            IMPORTANT RULES
            - When the user asks "Which medication...", return only the medication column.
            - Use exact categorical values from the schema examples (e.g., Diabetes, Cancer, Asthma).
            - For medical conditions, preserve capitalization.
            - When filtering by year, use: admission_date BETWEEN 'YYYY-01-01' AND 'YYYY-12-31'
            - If the question starts with "Which patients...", return DISTINCT patients.
            - Use COUNT(DISTINCT admissions.patient_id) for questions about patients "How many patients..."
            - Always qualify columns when multiple tables are joined (example: admissions.patient_id, patients.name).
            - Use COUNT(*) only for counting admissions.
            - Use '=' instead of LIKE for categorical columns and match the exact case of values provided in the schema examples.
            - If the user mentions a disease/condition (diabetes, cancer, asthma, obesity, hypertension, heart disease), ALWAYS filter using admissions.medical_condition.
            - Never use blood_type, gender, or any other patient attribute for disease-related questions.
            - medical_condition EXISTS ONLY in admissions.
            - Never query medical_condition from patients.
            - Whenever the question asks about diseases, join patients with admissions.
            - When the user asks for "abnormal test results", filter using admissions.test_results = 'Abnormal'.
            - Do not use !=, IS NOT NULL, or empty checks for categorical values.
            - Return ONLY SQLite SQL.
            - No explanation.
            - No markdown.
            - Only SELECT statements.
            Example:
            User: How many diabetic patients were admitted?
            SQL must use:
            WHERE admissions.medical_condition = 'diabetes'

            User Question:
            {query}
            """,
            system_instruction=None,
            temperature=0
        )
        print("=" * 60)
        print("USER QUERY:")
        print(query)
        print()
        print("LLM RAW RESPONSE:")
        print(response)
        print("=" * 60)
        
        # Clean up output in case the LLM returned markdown code blocks
        sql = response.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        return sql.strip()

    def execute_sql(self, sql: str) -> tuple[pd.DataFrame, str | None]:
        """
        Executes SQL query on the database. Returns a pandas DataFrame of the result
        and an error message if the query failed.
        """
        conn = sqlite3.connect(self.db_path)
        error_msg = None
        df = pd.DataFrame()
        try:
            df = pd.read_sql_query(sql, conn)
        except Exception as e:
            error_msg = str(e)
            print(f"SQL Execution Error: {error_msg}")
        finally:
            conn.close()
        return df, error_msg

    def query(self, nl_query: str) -> dict:
        """
        Main interface: Generates SQL, executes it, and returns a structured output.
        Includes self-correction logic if the SQL fails.
        """
        sql = self.generate_sql(nl_query)
        df, error = self.execute_sql(sql)
        
        # Simple self-correction loop (1 retry)
        if error :
            print("Attempting SQL self-correction...")
            correction_prompt = f"""
            The following SQLite query failed.

            SQL

            {sql}

            SQLite Error

            {error}

            Database schema

            {self.schema_info}

            Return ONLY the corrected SQL.

            Do not explain anything.
            """ 
            corrected_sql = call_llm(
                prompt=correction_prompt,
                system_instruction=self.system_instruction,
                temperature=0.0
            )
            # Clean markdown formatting if any
            corrected_sql = corrected_sql.strip()
            if corrected_sql.startswith("```sql"):
                corrected_sql = corrected_sql[6:]
            if corrected_sql.endswith("```"):
                corrected_sql = corrected_sql[:-3]
            corrected_sql = corrected_sql.strip()
            
            df, error = self.execute_sql(corrected_sql)
            if not error:
                sql = corrected_sql
                
        return {
            "query": nl_query,
            "sql": sql,
            "success": error is None,
            "error": error,
            "results": df.to_dict(orient="records") if not df.empty else [],
            "columns": df.columns.tolist() if not df.empty else []
        }
