import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import time

from src import config
from src.agents.orchestrator import OrchestratorAgent
from src.agents.sql_agent import SQLAgent
from src.agents.rag_agent import RAGAgent
from src.agents.formatter import ResponseFormatter
from src.llm_client import call_llm

app = FastAPI(title="RAG-Based Healthcare Query Assistant")

# Initialize agents
orchestrator = OrchestratorAgent()
sql_agent = SQLAgent()
rag_agent = RAGAgent()
formatter = ResponseFormatter()

# Request/Response Models
class QueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []

class QueryResponse(BaseModel):
    query: str
    route: str
    response: str
    sql: Optional[str] = None
    citations: Optional[List[Dict]] = []
    latency_ms: float
    timestamp: str

# In-memory simple log storage for displaying routing decisions in the UI
routing_logs = []

@app.post("/api/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    start_time = time.time()
    query = request.query.strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    print(f"Received query: '{query}'")
    
    # 1. Detect Intent using Orchestrator
    try:
        route = orchestrator.route_query(query)
    except Exception as e:
        print(f"Orchestrator error: {e}")
        route = "GENERAL"  # Fallback
        
    print(f"Orchestrator routed query to: {route}")
    
    sql_stmt = None
    citations = []
    response_text = ""
    
    # 2. Route and execute
    try:
        if route == "SQL":
            result = sql_agent.query(query)
            sql_stmt = result["sql"]
            if result["success"]:
                response_text = formatter.format_sql_response(
                    query=query,
                    sql=sql_stmt,
                    results=result["results"],
                    columns=result["columns"]
                )
            else:
                response_text = (
                    f"I encountered an error trying to query the database.\n"
                    f"**Generated SQL:** `{sql_stmt}`\n"
                    f"**Error Details:** `{result['error']}`"
                )
        elif route == "RAG":
            result = rag_agent.query(query)
            response_text = formatter.format_rag_response(
                query=query,
                answer=result["answer"],
                citations=result["citations"]
            )
            citations = result["citations"]
        else:
            # GENERAL conversational route
            system_instruction = (
                "You are the RAG-Based Healthcare Query Assistant. "
                "Respond to the user's greeting or question politely, helpfully, and concisely. "
                "Remind them that you can help query patient records (using SQL) and policy documents (using RAG)."
            )
            response_text = call_llm(
                prompt=query,
                system_instruction=system_instruction,
                temperature=0.7
            )
    except Exception as e:
        print(f"Execution error on route {route}: {e}")
        response_text = f"An unexpected error occurred: {str(e)}. Please try again."
        
    latency = (time.time() - start_time) * 1000
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Log the decision
    log_entry = {
        "timestamp": timestamp,
        "query": query,
        "route": route,
        "latency_ms": round(latency, 2),
        "success": True if response_text else False
    }
    routing_logs.append(log_entry)
    
    return QueryResponse(
        query=query,
        route=route,
        response=response_text,
        sql=sql_stmt,
        citations=citations,
        latency_ms=round(latency, 2),
        timestamp=timestamp
    )

@app.get("/api/logs")
def get_routing_logs():
    return routing_logs

@app.get("/api/db-stats")
def get_db_stats():
    """
    Returns high-level stats from the SQLite database to populate dashboard counters.
    """
    if not os.path.exists(config.DB_PATH):
        return {"error": "Database not initialized"}
        
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    try:
        cursor.execute("SELECT COUNT(*) FROM patients;")
        stats["total_patients"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM admissions;")
        stats["total_admissions"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors;")
        stats["total_doctors"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM hospitals;")
        stats["total_hospitals"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT ROUND(AVG(billing_amount), 2) FROM admissions;")
        stats["avg_billing"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT DISTINCT medical_condition FROM admissions LIMIT 6;")
        stats["conditions"] = [r[0] for r in cursor.fetchall()]
        
    except Exception as e:
        print(f"Stats query error: {e}")
        stats = {"error": str(e)}
    finally:
        conn.close()
        
    return stats

# Serve frontend static files
static_path = os.path.join(config.BASE_DIR, "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

@app.get("/")
def read_root():
    static_index = os.path.join(config.BASE_DIR, "static", "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    return {"message": "Healthcare Assistant Backend is running. Frontend static directory not initialized."}
