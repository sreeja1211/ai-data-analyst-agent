from server.tools import (
    load_csv_file,
    describe_data,
    filter_rows,
    group_summary,
    plot_chart,
)

rows = load_csv_file("sample_sales.csv")

print("--- describe_data ---")
info = describe_data(rows)
print("Rows:", info["rows"], "| Columns:", info["columns"])
for col in info["column_info"]:
    print(col)

print("\n--- filter_rows: revenue > 150000 ---")
for r in filter_rows(rows, "revenue", ">", 150000):
    print(r)

print("\n--- group_summary: revenue by region ---")
for r in group_summary(rows, "region", "revenue", "sum"):
    print(r)

print("\n--- plot_chart data: bar, revenue by region ---")
print(plot_chart(rows, "bar", "region", "revenue", "sum"))