import pandas as pd
import json
import io
import os # Make sure to import os if you use DATA_FOLDER or full_file_path later
from pydantic import BaseModel, Field
from typing import List, Dict
from langchain_core.tools import tool

# Define the base directory for data files (assuming you have this setup)
DATA_FOLDER = 'mangodata' # IMPORTANT: If you don't use this, remove it or adjust paths below

# --- Tool Argument Schemas ---
class FilePathInput(BaseModel):
    # Updated description to reflect it's a file name within a folder
    file_path: str = Field(description="The name of the CSV or Excel file (e.g., 'my_data.csv') to be analyzed, assumed to be in the 'mangodata' folder.")

# --- Tool Classes ---

class DataAnalysisTools:
    """
    A collection of tools for data analysis, specifically for handling CSV and Excel files.
    """
    def __init__(self):
        # This __init__ method is crucial for proper instance creation and method binding
        pass

    @tool(args_schema=FilePathInput)
    def extract_summary(file_path: str) -> str:
        """
        Extracts summary information from a CSV or Excel file.
        Assumes the file is located in the 'mangodata' folder.

        Args:
            file_path (str): The name of the CSV or Excel file (e.g., 'my_data.csv').

        Returns:
            str: A string representation of the summary information, or an error message.
        """
        full_file_path = os.path.join(DATA_FOLDER, file_path) # Using DATA_FOLDER
        try:
            def _extract_summary_from_df(df: pd.DataFrame) -> Dict:
                """
                Helper function to extract summary information from a Pandas DataFrame.
                """
                if df.empty:
                    raise ValueError("DataFrame is empty.")

                buffer = io.StringIO()
                df.info(buf=buffer)
                info_string = buffer.getvalue()

                missing_values = df.isnull().sum()
                missing_values_dict = {col: int(count) for col, count in missing_values.items() if count > 0}

                summary = {
                    "columns": list(df.columns),
                    "head": df.head().to_string(),
                    "info": info_string,
                    "description": df.describe().to_string(),
                    "missing_values": missing_values_dict,
                }
                return summary

            try:
                if full_file_path.lower().endswith(('.csv', '.txt')):
                    df = pd.read_csv(full_file_path)
                elif full_file_path.lower().endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(full_file_path)
                else:
                    return f"Error: Unsupported file format for {file_path}. Please provide a CSV or Excel file."
            except FileNotFoundError:
                return f"Error: File not found at {full_file_path}. Please ensure the file is uploaded and the name is correct."
            except Exception as e:
                return f"An error occurred while loading the data from {full_file_path}: {e}"

            summary_data = _extract_summary_from_df(df)
            return json.dumps(summary_data, indent=2)
        except Exception as e:
            return f"An error occurred in extract_summary for {file_path}: {e}"

    @tool(args_schema=FilePathInput)
    def extract_column_names(file_path: str) -> List[str]:
        """
        Extracts column names from a CSV or Excel file.
        Assumes the file is located in the 'mangodata' folder.

        Args:
            file_path (str): The name of the CSV or Excel file (e.g., 'my_data.csv').

        Returns:
            List[str]: A list of column names, or an error message.
        """
        full_file_path = os.path.join(DATA_FOLDER, file_path) # Using DATA_FOLDER
        try:
            if full_file_path.lower().endswith(('.csv', '.txt')):
                df = pd.read_csv(full_file_path)
            elif full_file_path.lower().endswith(('.xls', '.xlsx')):
                df = pd.read_excel(full_file_path)
            else:
                raise ValueError(f"Unsupported file format for {file_path}. Please provide a CSV or Excel file.")
            return list(df.columns)
        except FileNotFoundError:
            return f"Error: File not found at {full_file_path}. Please ensure the file is uploaded and the name is correct."
        except Exception as e:
            return f"An error occurred in extract_column_names for {file_path}: {e}"