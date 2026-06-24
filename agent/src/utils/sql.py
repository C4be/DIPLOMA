
def extract_sql(text: str) -> str:
    if "```sql" in text:
        return text.split("```sql")[1].split("```")[0].strip()
    if "```" in text:
        return text.split("```")[1].strip()
    return text.strip()