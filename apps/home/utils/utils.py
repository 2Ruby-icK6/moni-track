import pandas as pd
import json
import re
from django.http import Http404

def excel_to_json(input_excel, output_json, required_columns=None):
    try:
        df = pd.read_excel(input_excel, dtype=str, skiprows=3)
        df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()

        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise Http404(f"Missing required columns: {', '.join(missing_columns)}")

        def clean_value(value):
            if isinstance(value, str):
                value = value.strip()
                return None if value == "" else value
            return value

        def clean_numeric(value):
            if isinstance(value, str):
                value = re.sub(r"\.{2,}", ".", value)  # Remove multiple dots
                return value if re.match(r"^\d+(\.\d+)?$", value) else value
            return value

        def format_date(value):
            try:
                parsed_date = pd.to_datetime(value, errors='coerce')
                if pd.notna(parsed_date):
                    return parsed_date.strftime("%Y-%m-%d")
            except Exception:
                pass
            return value

        df = df.map(lambda x: clean_value(x) if isinstance(x, str) else x)
        df = df.applymap(lambda x: clean_numeric(x) if isinstance(x, str) else x)

        for col in df.columns:
            if "date" in col.lower():
                df[col] = df[col].apply(lambda x: format_date(x) if isinstance(x, str) else x)

        json_data = df.to_json(orient="records", indent=4)

        with open(output_json, "w", encoding="utf-8") as json_file:
            json_file.write(json_data)

    except ValueError as ve:
        raise Http404(f"Data Validation Error: {ve}")
    except FileNotFoundError:
        raise Http404("Input Excel file not found.")
    except json.JSONDecodeError:
        raise Http404("Failed to generate valid JSON output.")
    except Exception as e:
        raise Http404(f"Unexpected error: {e}")
