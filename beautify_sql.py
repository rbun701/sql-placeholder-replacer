import re

def custom_align_select_flexible_block(select_sql: str) -> str:
    """
    Formats a single SELECT block by aligning AS clauses and fixing commas.
    Works for single-line or multi-line SELECT content.
    """
    # Normalize spaces
    select_sql = select_sql.replace('\n', ' ')
    select_sql = re.sub(r'\s+', ' ', select_sql).strip()

    # Extract the part between SELECT and FROM
    match = re.search(r'\bSELECT\b(.*?)\bFROM\b', select_sql, re.IGNORECASE)
    if not match:
        return select_sql  # Not a standard SELECT-FROM structure

    select_clause = match.group(1).strip()
    before = select_sql[:match.start()].strip()
    after = select_sql[match.end():].strip()

    # Split expressions by commas while ignoring commas inside parentheses
    expressions = re.split(r',(?![^()]*\))', select_clause)

    parsed_lines = []
    max_expr_len = 0

    for expr in expressions:
        parts = re.split(r'\s+AS\s+', expr.strip(), flags=re.IGNORECASE)
        if len(parts) == 2:
            lhs, rhs = parts
            parsed_lines.append((lhs.strip(), rhs.strip()))
            max_expr_len = max(max_expr_len, len(lhs.strip()))
        else:
            parsed_lines.append((expr.strip(), None))
            max_expr_len = max(max_expr_len, len(expr.strip()))

    # Build aligned SELECT block
    aligned_lines = []
    for lhs, rhs in parsed_lines:
        if rhs:
            padding = " " * (max_expr_len - len(lhs))
            aligned_lines.append(f"  {lhs}{padding} AS {rhs},")
        else:
            aligned_lines.append(f"  {lhs},")

    if aligned_lines:
        aligned_lines[-1] = aligned_lines[-1].rstrip(',')

    return f"{before}\nSELECT\n" + "\n".join(aligned_lines) + f"\nFROM {after}"


def align_all_select_blocks_flexible(sql: str) -> str:
    """
    Finds and formats all SELECT blocks in the given SQL string.
    Replaces only well-formed SELECT-FROM patterns.
    """
    # Match each SELECT...FROM block, even nested ones
    pattern = re.compile(r'(SELECT\s+.*?\bFROM\b)', re.IGNORECASE | re.DOTALL)

    def formatter(match):
        block = match.group(1)
        try:
            return custom_align_select_flexible_block(block)
        except Exception:
            return block  # fail-safe

    return pattern.sub(formatter, sql)
