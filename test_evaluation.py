import sys
import os
import time
import pandas as pd

# Add src to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import config
from src.agents.orchestrator import OrchestratorAgent
from src.agents.sql_agent import SQLAgent
from src.agents.rag_agent import RAGAgent

def run_evaluation():
    print("==================================================")
    print("MediQuery AI - SYSTEM TESTING & EVALUATION")
    print("==================================================")
    
    # Initialize agents
    print("Initializing agents...")
    orchestrator = OrchestratorAgent()
    sql_agent = SQLAgent()
    rag_agent = RAGAgent()
    
    # Define test suite
    test_cases = [
        # SQL Database Queries
        {
            "query": "How many diabetic patients were admitted last month?",
            "expected_route": "SQL",
            "check_fn": lambda res: res.get("success") == True and "SELECT" in res.get("sql", "").upper()
        },
        {
            "query": "Which patients have abnormal test results?",
            "expected_route": "SQL",
            "check_fn": lambda res: res.get("success") == True and "abnormal" in res.get("sql", "").lower()
        },
        {
            "query": "Show the average billing amount by insurance provider.",
            "expected_route": "SQL",
            "check_fn": lambda res: res.get("success") == True and "AVG" in res.get("sql", "").upper()
        },
        # RAG Policy Queries
        {
            "query": "What is the hospital discharge policy?",
            "expected_route": "RAG",
            "check_fn": lambda res: len(res.get("citations", [])) > 0 or "discharge" in res.get("answer", "").lower()
        },
        {
            "query": "Is prior insurance approval required for surgery?",
            "expected_route": "RAG",
            "check_fn": lambda res: len(res.get("citations", [])) > 0 or "prior" in res.get("answer", "").lower()
        },
        # General & Out-of-Domain Queries
        {
            "query": "Hi, who are you and what can you do?",
            "expected_route": "GENERAL",
            "check_fn": lambda res: len(res.get("response", "")) > 0
        },
        {
            "query": "Who won the World Cup in 2022?",
            "expected_route": "GENERAL",
            "check_fn": lambda res: len(res.get("response", "")) > 0
        }
    ]
    
    results = []
    
    for i, tc in enumerate(test_cases):
        query = tc["query"]
        expected = tc["expected_route"]
        print(f"\nTest {i+1}: '{query}'")
        
        # 1. Test Orchestrator Routing
        t0 = time.time()
        try:
            actual_route = orchestrator.route_query(query)
            route_time = (time.time() - t0) * 1000
            print(f"  Routed to: {actual_route} (Latency: {route_time:.2f}ms)")
        except Exception as e:
            print(f"  Routing error: {e}")
            actual_route = "ERROR"
            route_time = 0
            
        route_ok = actual_route == expected
        
        # 2. Test Route Execution
        t0 = time.time()
        exec_ok = False
        exec_details = {}
        
        try:
            if actual_route == "SQL":
                exec_details = sql_agent.query(query)
                exec_ok = tc["check_fn"](exec_details)
            elif actual_route == "RAG":
                exec_details = rag_agent.query(query)
                exec_ok = tc["check_fn"](exec_details)
            elif actual_route == "GENERAL":
                # General conversation fallback
                from src.llm_client import call_llm
                response = call_llm(query, "You are a helpful hospital assistant.", temperature=0.7)
                exec_details = {"response": response}
                exec_ok = tc["check_fn"](exec_details)
            else:
                exec_details = {"error": "Invalid route"}
                exec_ok = False
        except Exception as e:
            print(f"  Execution error: {e}")
            exec_details = {"error": str(e)}
            exec_ok = False
            
        exec_time = (time.time() - t0) * 1000
        total_time = route_time + exec_time
        
        status = "PASS" if (route_ok and exec_ok) else "FAIL"
        
        print(f"  Execution: {'SUCCESS' if exec_ok else 'FAILED'} (Total Latency: {total_time:.2f}ms)")
        print(f"  Status: {status}")
        
        results.append({
            "test_num": i+1,
            "query": query,
            "expected_route": expected,
            "actual_route": actual_route,
            "route_ok": "Yes" if route_ok else "No",
            "exec_ok": "Yes" if exec_ok else "No",
            "latency_ms": round(total_time, 2),
            "status": status
        })
        
    print("\n\n" + "="*50)
    print("EVALUATION SUMMARY REPORT")
    print("==================================================")
    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False))
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    accuracy = (passed / total) * 100
    
    print("\nMetrics:")
    print(f"  Total Test Cases: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  System Accuracy: {accuracy:.1f}%")
    print(f"  Average Latency: {df_results['latency_ms'].mean():.2f} ms")
    print("==================================================")

if __name__ == "__main__":
    # Check if vector store is initialized, if not notify
    if not os.path.exists(config.VECTOR_STORE_PATH):
        print(f"WARNING: Vector store at {config.VECTOR_STORE_PATH} not found.")
        print("Please run 'python src/load_policies.py' first to vectorize policy documents.")
        
    # Check if database is initialized
    if not os.path.exists(config.DB_PATH):
        print(f"WARNING: SQLite Database at {config.DB_PATH} not found.")
        print("Please run 'python src/load_database.py' first to ingest patient records.")
        
    run_evaluation()
