from typing import Any

MAX_ALLOWED_VALUES = 10

def format_table_context(context: dict[str, Any]) -> str:

    lines = [
        f"Table: {context['table_name']}",
        "",
        "Columns:",
        "",
    ]

    for col_name, col_info in context["columns"].items():

        line = f"- {col_name} "

        if "values" in col_info:
            values = ", ".join(map(str, col_info["values"][:MAX_ALLOWED_VALUES]))
            line += f"\n  Values: {values}"

        lines.append(line)

    return "\n".join(lines)