import json
import csv
from io import StringIO

RAW_KPI_DATA = """2025年VPO工作站KPI指标目标分解
		部门：北部区域				责任人:宋学军										单位：万元， %
		KPI序号	KPI指标	填写部门	分解部门	计算公式	口径	 1月 	 2月 	3月	4月	5月	6月	7月	8月	9月	10月	11月	12月
		1	核算达标率	北部区域	财务区域/财务部	结账时效50%，核算准确率50%	目标	 1.00 	 1.00 	100%	100%	100%	100%	100%	100%	100%	100%	100%	100%
								实际	 0.88 	 1.00 	88%	100%	100%	0	0	0	0	0	0	0
								差异	 -0.13 	 -   	-0.125	0	0
		1.1	结账时效	北部区域	财务部	实际达成结账时效公司个数/4	目标	 1.00 	100%	100%	100%	100%
								实际	 0.75 	100%	75%	100%	100%
								差异	 -0.25 	 -   	-25.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%
		1.2	核算准确率	北部区域	财务部	外部审计30%+内审30%+自查40%	目标	 1.00 	100%	100%	100%	100%
								实际	 1.00 	100%	100%	100%	100%
								差异	 -   	 -   	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%
		2	现金净流量	北部区域	财务区域	现金流量表	目标金额	" 7,827.00 "	 -37.42 	 -173.62 	" 4,091.65 "	 -435.82
								实际金额	 -688.00 	" 11,043.00 "	 -923.89 	" 9,824.00 "	" -3,709.10 "	 -   	 -   	 -   	 -   	 -   	 -   	 -
								差异	" -8,515.00 "		 -750.27 	" 5,732.35 "	" -3,273.28 "	 -   	 -   	 -   	 -   	 -   	 -   	 -
		3	管理费用率	北部区域	财务区域	管理费用/收入	目标	 1.00 	100%	100%	100%	100%
								实际	 0.88 	100%	88%	100%	100%
								差异	 -0.13 	 -   	-0.125	0	0
		3.1	招待费合规率	北部区域	财务部	招待费合规金额/招待费总金额	目标	 1.00 	100%	100%	100%	100%
								实际	 0.75 	100%	75%	100%	100%
								差异	 -0.25 	 -   	-25.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%
		3.2	差旅费合规率	北部区域	财务部	差旅费合规金额/差旅费总金额	目标	 1.00 	100%	100%	100%	100%
								实际	 1.00 	100%	100%	100%	100%
								差异	 -   	 -   	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%	0.0%
		4	资产负债率	北部区域	财务区域	负债/资产*100%	目标	 1.00 	100%	100%	100%	100%	100%	100%	100%	100%	100%	100%	100%
								实际	 0.88 	100%	88%	100%	100%	0	0	0	0	0	0	0
								差异	 -0.13 	 -   	-0.125	0	0
		5	利润总额	北部区域	财务区域	利润表	目标金额	" 7,827.00 "	 -37.42 	 -173.62 	" 4,091.65 "	 -435.82
								实际金额	 -688.00 	" 11,043.00 "	 -923.89 	" 9,824.00 "	" -3,709.10 "	 -   	 -   	 -   	 -   	 -   	 -   	 -
								差异	" -8,515.00 "		 -750.27 	" 5,732.35 "	" -3,273.28 "	 -   	 -   	 -   	 -   	 -   	 -   	 -
"""

def parse_value(value_str):
    """Converts a string value to float, handling percentages, commas, and placeholders."""
    if value_str is None:
        return None
    value_str = str(value_str).strip()
    if not value_str or value_str == '-':
        return None
    try:
        if '%' in value_str:
            return float(value_str.replace('%', '')) / 100.0
        return float(value_str.replace(',', '').replace('"', '').strip())
    except ValueError:
        return None # Or raise an error, or return a specific marker

def get_parent_id(kpi_id):
    """Determines the parent KPI ID from a given KPI ID."""
    if '.' not in kpi_id:
        return None
    return kpi_id.rpartition('.')[0]

def main():
    # Skip header lines
    lines = RAW_KPI_DATA.strip().split('\n')
    data_lines = lines[3:] # Assuming the actual data starts from the 4th line

    # Use csv reader to handle tab-separated values
    # Pass the raw lines directly, csv.reader should handle tab delimiters.
    reader = csv.reader(data_lines, delimiter='\t')

    kpis = {}
    last_kpi_id = None
    last_kpi_name = None
    last_fill_dept = None
    last_decompose_dept = None
    last_formula = None

    for row_idx, row in enumerate(reader):
        # Min expected columns for a valid data line to attempt parsing
        # Max possible index accessed: first_data_index + 1 + 12. If first_data_index is 8, this is 21.
        MIN_EXPECTED_COLUMNS = 6 # KPI ID, Name, Dept1, Dept2, Formula, MetricType

        # Skip rows that are too short to possibly contain meaningful data
        if len(row) < MIN_EXPECTED_COLUMNS:
            continue

        # Pad short rows to avoid index errors, up to a max reasonable length
        # (e.g. 8 leading empty + metric_type + 12 months = 21)
        # Let's use a slightly larger padding for safety with first_data_index logic
        # Max useful index is metric_type_idx + 12. If metric_type_idx is ~8, then 8+12=20.
        # So padding up to 25 should be very safe.
        while len(row) < 25: # Increased padding
            row.append(None)

        safe_get = lambda r, i: r[i].strip() if (i < len(r) and r[i]) else None

        # KPI ID is in row[2] due to consistent leading tabs in the raw data.
        # Header: \t\tKPI序号...
        # Data:   \t\t1...
        kpi_id_candidate_from_row = safe_get(row, 2)
        is_primary_line = bool(kpi_id_candidate_from_row)

        if is_primary_line:
            kpi_id_str = kpi_id_candidate_from_row
            kpi_name_str = safe_get(row, 3)
            fill_dept_str = safe_get(row, 4)
            decompose_dept_str = safe_get(row, 5)
            formula_str = safe_get(row, 6)
            metric_type_str = safe_get(row, 7) # 口径 for primary lines
            monthly_values_start_idx = 8      # Data for primary lines

            # Update last known primary line details
            last_kpi_id = kpi_id_str
            last_kpi_name = kpi_name_str
            last_fill_dept = fill_dept_str
            last_decompose_dept = decompose_dept_str
            last_formula = formula_str
        else: # Secondary line (e.g., "实际" data for the last KPI)
            kpi_id_str = last_kpi_id
            kpi_name_str = last_kpi_name
            fill_dept_str = last_fill_dept
            decompose_dept_str = last_decompose_dept
            formula_str = last_formula

            # For secondary lines like `\t\t\t\t\t\t\t\t实际...` (8 tabs before '实际')
            # '实际' (metric_type_str) will be at row[8].
            # Find the first non-empty cell starting from expected data columns.
            # Known: first 2 cols are empty from global tabs.
            # KPI ID would be col 2, Name col 3 etc for primary.
            # Metric type for secondary appears after these, e.g. col 8.
            first_data_index = -1
            # Search for metric_type starting from index 2, as row[0], row[1] are always empty due to `\t\t` prefix
            for i in range(2, len(row)):
                if row[i] and row[i].strip(): # Found the first piece of text
                    first_data_index = i
                    break

            if first_data_index != -1:
                metric_type_str = safe_get(row, first_data_index)
                monthly_values_start_idx = first_data_index + 1
            else:
                metric_type_str = None
                monthly_values_start_idx = -1 # Invalid state

        if not kpi_id_str or not metric_type_str or monthly_values_start_idx == -1: # Essential fields must be present
            continue

        if "差异" in metric_type_str: # Ignore '差异' rows
            continue

        if kpi_id_str not in kpis:
            kpis[kpi_id_str] = {
                "id": kpi_id_str,
                "name": kpi_name_str,
                "fill_department": fill_dept_str,
                "decompose_department": decompose_dept_str,
                "formula": formula_str,
                "is_cost_metric": False, # Default as per requirement
                "monthly_targets": [None] * 12,
                "monthly_actuals": [None] * 12,
                "children": []
            }

        if "目标" in metric_type_str: # Catches '目标' and '目标金额'
            kpis[kpi_id_str]["monthly_targets"] = [parse_value(safe_get(row, i)) for i in range(monthly_values_start_idx, monthly_values_start_idx + 12)]
        elif "实际" in metric_type_str: # Catches '实际' and '实际金额'
            kpis[kpi_id_str]["monthly_actuals"] = [parse_value(safe_get(row, i)) for i in range(monthly_values_start_idx, monthly_values_start_idx + 12)]

    # Build hierarchical structure
    structured_kpis = []
    # kpi_map = {kpi_data["id"]: kpi_data for kpi_data in kpis.values()} # This line is fine
    # Ensure kpis dictionary is not empty before proceeding
    if not kpis:
        # print("No KPIs were parsed. Check CSV parsing and row processing logic.", file=sys.stderr)
        # Adding a dummy print for now, as stderr is not captured by the tool
        # print("Debug: kpis dictionary is empty after loop.")
        pass


    kpi_map = {kpi_data["id"]: kpi_data for kpi_data in kpis.values()}


    for kpi_id, kpi_data in sorted(kpi_map.items()): # Sort to ensure parents are processed first
        parent_id = get_parent_id(kpi_id)
        if parent_id and parent_id in kpi_map:
            # Ensure parent_id's entry exists and has a 'children' list
            if kpi_map[parent_id].get("children") is None:
                 kpi_map[parent_id]["children"] = [] # Should have been initialized
            kpi_map[parent_id]["children"].append(kpi_data)
        else:
            structured_kpis.append(kpi_data)

    print(json.dumps(structured_kpis, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
