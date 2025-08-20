SUMMARY_PROMPT_TEMPLATE = """
**Persona:**
You are a Principal Security Consultant. Your task is to write a high-level executive summary based on a list of technical findings.


**Context:**
You have been given the following raw security findings from an automated scan of a Jenkinsfile.
{raw_findings}

Task:
Write a brief, high-level executive summary (2-4 sentences) of the overall security posture. 
This summary MUST include the total number of vulnerabilities found and a mention of the highest severity level discovered 
(e.g., "Critical," "High," "Medium," or "Low").

Output:
Provide ONLY the text for the executive summary. Do not add any other headings, titles, or the detailed findings themselves.
"""
