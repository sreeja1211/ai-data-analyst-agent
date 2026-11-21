import csv
import io
import operator
import statistics

OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
}
AGGS = {"sum", "mean", "median", "min", "max", "count"}
CHARTS = {"bar", "line", "pie", "hist"}


def _convert(value):
    """Turn a CSV text cell into int, float, text, or None (if empty)."""
    value = value.strip()
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def load_csv_text(text):
    """Read CSV text and return a list of rows (each row is a dict)."""
    reader = csv.DictReader(io.StringIO(text))
    return [{k: _convert(v or "") for k, v in row.items()} for row in reader]


def load_csv_file(path):
    """Read a CSV file from disk."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        return load_csv_text(f.read())


def _check_column(rows, col):
    columns = list(rows[0].keys())
    if col not in columns:
        raise ValueError(f"Column '{col}' not found. Available columns: {columns}")


def _numbers(rows, col):
    return [r[col] for r in rows if isinstance(r[col], (int, float))]


def describe_data(rows):
    """Overview of the dataset: size, column types, missing values, basic stats."""
    columns = []
    for col in rows[0].keys():
        values = [r[col] for r in rows]
        nums = _numbers(rows, col)
        info = {"name": col, "missing": sum(v is None for v in values)}
        if nums:
            info["type"] = "number"
            info["min"] = min(nums)
            info["max"] = max(nums)
            info["mean"] = round(statistics.mean(nums), 2)
            info["median"] = statistics.median(nums)
        else:
            info["type"] = "text"
            info["unique"] = len({v for v in values if v is not None})
        columns.append(info)
    return {
        "rows": len(rows),
        "columns": len(columns),
        "column_info": columns,
        "preview": rows[:5],
    }


def filter_rows(rows, column, op, value):
    """Keep rows where column <op> value. op: ==, !=, >, <, >=, <=, contains."""
    _check_column(rows, column)
    result = []
    for r in rows:
        cell = r[column]
        if cell is None:
            continue
        if op == "contains":
            if str(value).lower() in str(cell).lower():
                result.append(r)
        elif op in OPS:
            if isinstance(cell, (int, float)):
                if OPS[op](cell, float(value)):
                    result.append(r)
            elif OPS[op](str(cell), str(value)):
                result.append(r)
        else:
            raise ValueError(f"Operator '{op}' not allowed. Use: {list(OPS) + ['contains']}")
    return result


def group_summary(rows, group_by, column, agg="sum"):
    """Group rows by one column and aggregate another column."""
    _check_column(rows, group_by)
    _check_column(rows, column)
    if agg not in AGGS:
        raise ValueError(f"Aggregation '{agg}' not allowed. Use: {sorted(AGGS)}")

    groups = {}
    for r in rows:
        groups.setdefault(r[group_by], []).append(r[column])

    result = []
    for key, cells in groups.items():
        nums = [c for c in cells if isinstance(c, (int, float))]
        if agg == "count":
            value = len([c for c in cells if c is not None])
        elif not nums:
            continue
        elif agg == "sum":
            value = sum(nums)
        elif agg == "mean":
            value = round(statistics.mean(nums), 2)
        elif agg == "median":
            value = statistics.median(nums)
        elif agg == "min":
            value = min(nums)
        else:
            value = max(nums)
        result.append({group_by: key, column: value})

    return sorted(result, key=lambda item: item[column], reverse=True)


def plot_chart(rows, chart_type, x, y=None, agg="sum"):
    """Return chart data (labels and values). The website draws the chart."""
    if chart_type not in CHARTS:
        raise ValueError(f"Chart '{chart_type}' not allowed. Use: {sorted(CHARTS)}")
    _check_column(rows, x)

    if chart_type == "hist":
        nums = _numbers(rows, x)
        low, high = min(nums), max(nums)
        bins = 10
        width = (high - low) / bins or 1
        counts = [0] * bins
        for n in nums:
            index = min(int((n - low) / width), bins - 1)
            counts[index] += 1
        labels = [f"{low + i * width:.1f}-{low + (i + 1) * width:.1f}" for i in range(bins)]
        return {"type": "bar", "title": f"Distribution of {x}", "labels": labels, "values": counts}

    _check_column(rows, y)
    summary = group_summary(rows, x, y, agg)
    return {
        "type": chart_type,
        "title": f"{agg} of {y} by {x}",
        "labels": [str(item[x]) for item in summary],
        "values": [item[y] for item in summary],
    }