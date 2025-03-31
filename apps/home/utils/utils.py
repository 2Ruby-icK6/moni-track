import pandas as pd
import json
import re
from django.http import Http404
from datetime import date

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
                return None if value.upper() in ("NULL", "NONE", "") else value
            return value

        def clean_numeric(value):
            if isinstance(value, str):
                clean_value = re.sub(r",(?=\d{3}(\D|$))", "", value)  # Remove commas only in numeric values
                clean_value = re.sub(r"\.{2,}", ".", clean_value)  # Remove multiple dots
                return clean_value if re.match(r"^\d+(\.\d+)?$", clean_value) else value  # Preserve original if not a number
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

def format_date_or_text(value):
    """Formats a value as a date (if it's a date object) or returns it as text."""
    if value:  # Ensure the value is not empty
        if isinstance(value, date):  # Use date instead of datetime.date
            return value.strftime('%Y-%m-%d')  # Format the date object
        return str(value)  # Convert other types to string
    return None  # Keep it empty instead of "N/A" for Excel formatting

def get_or_create_foreign_key(mapping, model, value, field_name):
    """Helper function to get or create a foreign key object."""
    if value not in mapping:
        # Create new entry in the model if it doesn't exist
        obj, created = model.objects.get_or_create(**{field_name: value})
        mapping[value] = obj  # Update mapping with the newly created object
    return mapping[value]