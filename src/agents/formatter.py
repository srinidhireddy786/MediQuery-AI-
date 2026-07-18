from src.llm_client import call_llm
import pandas as pd

class ResponseFormatter:
    """
    Response Formatter Agent: Converts structured data (like SQL query results) 
    and RAG outputs into clear, conversational, and beautifully formatted responses.
    """
    def __init__(self):
        self.system_instruction = (
            "You are a Hospital Response Formatter.\n"
            "Your job is to take raw query outputs (like SQL database records) "
            "and format them into a polished, polite, and professional message for hospital staff.\n"
            "Rules:\n"
            "1. Present the data clearly. Use markdown tables for lists of items or comparative statistics.\n"
            "2. Keep the tone helpful and professional.\n"
            "3. If a SQL query result is empty, explain politely that no matching patient records were found.\n"
            "4. Summarize any key insights briefly."
        )

    def format_sql_response(self, query: str, sql: str, results: list, columns: list) -> str:
        """
        Formats SQL query results into a conversational text and a markdown table.
        """
        if not results:
            return f"No patient records were found matching the request: '{query}'."

        df = pd.DataFrame(results, columns=columns)

        # Show only first 10 rows
        display_df = df.head(10)
        markdown_table = display_df.to_markdown(index=False)

        # Handle scalar values like COUNT(*)
        if len(results) == 1 and len(columns) == 1:
            val = list(results[0].values())[0]
            col_name = columns[0]
            return f"According to patient records, the **{col_name.replace('_', ' ')}** is **{val}**."

        total_rows = len(df)

        prompt = f"""
    User Question:
    {query}

    Executed SQL:
    {sql}

    Total Rows Returned:
    {total_rows}

    Columns:
    {', '.join(columns)}

    Sample Rows (first 10 only):
    {display_df.to_dict(orient='records')}

    IMPORTANT:
    - The sample contains ONLY the first 10 rows.
    - Do NOT assume there are only 10 records.
    - Use the provided total row count ({total_rows}) in your summary.
    - Keep the summary within 2 sentences.
    - After the summary output exactly:
    [TABLE]
    """

        summary = call_llm(
            prompt=prompt,
            system_instruction=self.system_instruction,
            temperature=0.1,
        )
        print("=" * 60)
        print("SUMMARY FROM LLM")
        print(summary)
        print("=" * 60)

        if "[TABLE]" in summary:
            response = summary.replace("[TABLE]", "\n\n" + markdown_table)
        else:
            response = summary + "\n\n" + markdown_table

        if total_rows > 10:
            response += f"\n\n*Showing first 10 of {total_rows} records.*"

        return response

    def format_rag_response(self, query: str, answer: str, citations: list) -> str:
        """
        Formats a RAG answer. Adds a clear list of document citations at the bottom.
        """
        formatted = answer
        if citations:
            unique_sources = list(set([c["source"] for c in citations]))
            formatted += "\n\n**Sources & Reference Documents:**"
            for src in unique_sources:
                formatted += f"\n*   `{src}`"
        return formatted
