from src.llm_client import call_llm

class OrchestratorAgent:
    """
    Orchestrator Agent: Analyzes user natural language queries and routes them to 
    either the NLP-to-SQL Agent (for structured patient records) or the RAG Agent (for policy documents).
    """
    def __init__(self):
        self.system_instruction = """
        You are an Orchestrator Agent for a hospital AI assistant.

        Your task is to classify every user query into exactly ONE of these categories:

        SQL
        Use SQL if the user is asking about structured data stored in the hospital database.

        Examples:
        - How many patients have asthma?
        - Count diabetic patients.
        - Show all doctors.
        - List hospitals.
        - Show patient billing amounts.
        - Average billing amount.
        - Which patients have abnormal test results?
        - Which doctor treated the most patients?
        - List insurance providers.
        - How many insurance providers are there?
        - Show admissions in 2023.
        - Room numbers of admitted patients.

        RAG
        Use RAG if the user is asking about hospital documents, policies, procedures, guidelines, regulations or documentation.

        Examples:
        - What is the discharge policy?
        - How are rooms allocated?
        - Explain the insurance policy.
        - Is prior authorization required?
        - What is the visitor policy?
        - Explain EMTALA.
        - Emergency department procedure.
        - Surgery approval process.

        GENERAL
        Use GENERAL for greetings, casual conversation or questions unrelated to the hospital database or hospital policies.

        Examples:
        - Hello
        - How are you?
        - Who are you?
        - Tell me a joke.

        IMPORTANT:
        - Questions asking for counts, lists, names, averages, statistics, billing, admissions, doctors, hospitals, insurance providers or patient information ALWAYS belong to SQL.
        - The phrase "insurance providers" refers to database records → SQL.
        - The phrase "insurance policy" refers to hospital documentation → RAG.

        Return ONLY one word:
        SQL
        RAG
        GENERAL
        """

    def route_query(self, query: str) -> str:
        """
        Routes the user query to the appropriate agent. Returns 'SQL', 'RAG', or 'GENERAL'.
        """
        response = call_llm(
            prompt=f"User Query: {query}",
            system_instruction=self.system_instruction,
            temperature=0.0
        )
        # Parse output
        route = response.strip().upper()
        if "SQL" in route:
            return "SQL"
        elif "RAG" in route:
            return "RAG"
        else:
            return "GENERAL"
