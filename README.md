# 🏥 MediQuery AI

### RAG-Based Healthcare Query Assistant Using Multi-Agent Architecture

MediQuery AI is an AI-powered healthcare assistant that enables hospital staff to query **structured patient records** and **unstructured hospital policy documents** using natural language. The system combines **Natural Language-to-SQL (NL2SQL)** and **Retrieval-Augmented Generation (RAG)** within a **Multi-Agent Architecture** to provide accurate and conversational responses.

---

## 📌 Features

- 🤖 Multi-Agent Architecture
- 🩺 Natural Language to SQL Querying
- 📚 Retrieval-Augmented Generation (RAG)
- 🔍 Semantic Search using FAISS
- 💬 Conversational Healthcare Assistant
- 📊 Database Statistics API
- 📝 Query Routing Logs
- ⚡ FastAPI Backend
- 🎨 Interactive Web Interface

---

## 🏗️ System Architecture

```
                    User Query
                        │
                        ▼
                 FastAPI Backend
                        │
                        ▼
               Orchestrator Agent
                  /           \
                 /             \
                ▼               ▼
          SQL Agent        RAG Agent
              │                │
              ▼                ▼
       SQLite Database   FAISS Vector Store
               \            /
                \          /
                 ▼        ▼
           Response Formatter
                    │
                    ▼
              Final Response
```

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend Development |
| FastAPI | REST API |
| SQLite | Patient Database |
| Pandas | Data Processing |
| LangChain | RAG Pipeline |
| FAISS | Vector Database |
| Ollama | Local LLM Runtime |
| Qwen2.5:3B | Language Model |
| nomic-embed-text | Embedding Model |
| HTML, CSS, JavaScript | Frontend |

---

## 📂 Project Structure

```
HEALTHCARE_AI/

├── data/
│   ├── raw/
│   └── healthcare.db
│
├── policies/
│   ├── admission_policy.md
│   ├── billing_policy.md
│   ├── discharge_policy.md
│   ├── emergency_policy.md
│   └── insurance_policy.md
│
├── src/
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── sql_agent.py
│   │   ├── rag_agent.py
│   │   └── formatter.py
│   │
│   ├── config.py
│   ├── database.py
│   ├── download_data.py
│   ├── load_database.py
│   ├── ingest_policies.py
│   ├── load_policies.py
│   ├── llm_client.py
│   └── main.py
│
├── static/
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── vector_store/
│   └── faiss_policy_index/
│
├── requirements.txt
├── test_evaluation.py
├── README.md
└── .env
```

---

## 📊 Dataset

The project uses a **synthetic healthcare dataset** containing approximately **10,000 patient records**.

The dataset includes:

- Patient Information
- Medical Conditions
- Medications
- Test Results
- Admission Details
- Doctor Information
- Hospital Details
- Insurance Information
- Billing Amount

---

## 🗄️ Database Design

The healthcare database is normalized into four tables:

- **Patients**
- **Doctors**
- **Hospitals**
- **Admissions**

Indexes are created on frequently queried fields to improve SQL query performance.

---

## 📚 RAG Knowledge Base

Hospital policy documents are processed using the following pipeline:

```
Policy Documents
        │
        ▼
Text Chunking
        │
        ▼
Embedding Generation
        │
        ▼
FAISS Vector Store
        │
        ▼
Semantic Retrieval
        │
        ▼
LLM Response
```

Embedding Model:

- **nomic-embed-text**

Vector Database:

- **FAISS**

---

## 🤖 Multi-Agent Workflow

### Orchestrator Agent

- Detects user intent
- Routes queries to the appropriate agent

### SQL Agent

- Converts natural language into SQL
- Executes queries on SQLite
- Returns formatted results

Example:

> How many diabetic patients were admitted last month?

---

### RAG Agent

- Retrieves relevant policy documents
- Generates grounded responses using retrieved context

Example:

> What is the hospital discharge policy?

---

### Response Formatter

Converts SQL results and retrieved document content into clear conversational responses.

---

## 🔗 API Endpoints

### POST `/api/query`

Processes healthcare queries.

### GET `/api/logs`

Returns routing logs and latency.

### GET `/api/db-stats`

Returns:

- Total Patients
- Total Admissions
- Total Doctors
- Total Hospitals
- Average Billing Amount

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/MediQuery-AI.git
cd MediQuery-AI
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Ollama models:

```bash
ollama pull qwen2.5:3b
```

```bash
ollama pull nomic-embed-text
```

---

## ▶️ Running the Project

Initialize the database:

```bash
python src/database.py
```

Load the healthcare dataset:

```bash
python src/load_database.py
```

Create the vector store:

```bash
python src/ingest_policies.py
```

Run the FastAPI server:

```bash
uvicorn src.main:app --reload
```

Open the application:

```
http://localhost:8000
```

---

## 🧪 Testing & Evaluation

The project includes `test_evaluation.py` for evaluating:

- SQL Query Accuracy
- RAG Retrieval Relevance
- Agent Routing Accuracy
- Response Latency

---

## 🚀 Deployment

The application can be deployed using:

- Docker + AWS EC2
- Docker + Azure VM
- Docker + Google Cloud VM

For cloud platforms such as **Render** or **Streamlit Community Cloud**, the LLM backend can be adapted to use hosted APIs (e.g., Gemini or Groq) instead of a local Ollama instance.

---

## 🔮 Future Enhancements

- Voice-based Healthcare Assistant
- Authentication & Role-Based Access
- PostgreSQL Support
- Cloud Vector Database
- Electronic Health Record (EHR) Integration
- Healthcare Analytics Dashboard

---

## 📄 License

This project was developed for educational and learning purposes using a synthetic healthcare dataset. No real patient information is used.

---

## 👨‍💻 Author

**Srinidhi Reddy**

B.Tech Computer Science (AI & ML)

CVR College of Engineering
