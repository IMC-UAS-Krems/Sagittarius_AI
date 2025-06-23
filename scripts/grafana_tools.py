import os
import json
import requests
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# --- Grafana Configuration (Environment Variables) ---
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY")
FIWARE_DATASOURCE_NAME = os.getenv("FIWARE_DATASOURCE_NAME", "Fiware Orion Data Source") # IMPORTANT: Change this to your actual Grafana Data Source name for Fiware

class DashboardInput(BaseModel):
    title: str = Field(description="The title of the Grafana dashboard.")
    description: str = Field(description="A brief description for the dashboard.")
    panel_title: str = Field(description="The title of the graph panel within the dashboard.")
    fiware_entity_type: str = Field(description="The Fiware entity type to query (e.g., 'AirQualityObserved').")
    fiware_attribute: str = Field(description="The Fiware attribute to visualize (e.g., 'temperature', 'NO2').")
    time_field: str = Field(description="The time field in your Fiware data (e.g., 'dateObserved', 'TimeInstant').")
    interval: str = Field(description="The time interval for the graph (e.g., '1h', '5m', '1d').")

class GrafanaTools:
    """
    A collection of tools for interacting with the Grafana API to create dashboards.
    """
    def __init__(self):
        if not GRAFANA_API_KEY:
            print("WARNING: GRAFANA_API_KEY environment variable is not set. Grafana tools will not function.", file=os.sys.stderr)
        self.headers = {
            "Authorization": f"Bearer {GRAFANA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @tool(args_schema=DashboardInput)
    def create_grafana_dashboard(self, title: str, description: str, panel_title: str,
                                 fiware_entity_type: str, fiware_attribute: str,
                                 time_field: str, interval: str) -> str:
        """
        Creates a new Grafana dashboard with a single time series graph panel
        that queries data from a Fiware Orion Context Broker data source.

        Args:
            title (str): The title of the Grafana dashboard.
            description (str): A brief description for the dashboard.
            panel_title (str): The title of the graph panel within the dashboard.
            fiware_entity_type (str): The Fiware entity type to query (e.g., 'AirQualityObserved').
            fiware_attribute (str): The Fiware attribute to visualize (e.g., 'temperature', 'NO2').
            time_field (str): The time field in your Fiware data (e.g., 'dateObserved', 'TimeInstant').
            interval (str): The time interval for the graph (e.g., '1h', '5m', '1d').

        Returns:
            str: A message indicating success or failure, including the dashboard URL if successful.
        """
        if not GRAFANA_API_KEY:
            return "Error: Grafana API Key is not set. Cannot create dashboard."

        dashboard_model = {
            "dashboard": {
                "id": None,
                "uid": None,
                "title": title,
                "description": description,
                "tags": ["auto-generated", "fiware", fiware_entity_type],
                "timezone": "browser",
                "schemaVersion": 16,
                "version": 0,
                "panels": [
                    {
                        "id": 1,
                        "type": "graph",
                        "title": panel_title,
                        "gridPos": {"x": 0, "y": 0, "w": 24, "h": 12},
                        "targets": [
                            {
                                "refId": "A",
                                "datasource": {"type": "datasource", "uid": f"${{DS_{FIWARE_DATASOURCE_NAME.replace(' ', '_').upper()}}}"}, # Using template variable for datasource UID
                                "expr": f"SELECT {fiware_attribute} FROM {fiware_entity_type} WHERE {time_field} BETWEEN $__timeFrom() AND $__timeTo() GROUP BY time($__interval)",
                                "format": "time_series",
                                # This 'expr' is a placeholder and assumes a SQL-like query capability
                                # from your Fiware data source in Grafana.
                                # For SimpleJson, it would be different, e.g., {"query": "...", "refId": "A"}
                                # You might need to adjust this based on your actual Grafana data source for Fiware.
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "none",
                                "custom": {
                                    "drawStyle": "line",
                                    "fillOpacity": 10,
                                    "lineWidth": 1,
                                    "spanNulls": False
                                },
                                "color": { "mode": "palette" },
                                "mappings": [],
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        { "value": None, "color": "green" },
                                        { "value": 80, "color": "red" }
                                    ]
                                }
                            },
                            "overrides": []
                        },
                        "options": {
                            "legend": {
                                "calcs": [],
                                "displayMode": "list",
                                "placement": "bottom",
                                "showLegend": True
                            },
                            "tooltip": {
                                "mode": "single",
                                "sort": "none"
                            }
                        }
                    }
                ]
            },
            "folderId": 0, # Or a specific folder ID if you want to organize
            "overwrite": True # Set to True to update if a dashboard with the same title exists
        }

        # To dynamically get the datasource UID, you'd typically query Grafana's /api/datasources endpoint
        # For simplicity, we're using a template variable here. The user needs to ensure the data source exists.
        # A more robust solution would involve an initial API call to Grafana to get the UID.

        url = f"{GRAFANA_URL}/api/dashboards/db"
        print(f"Sending request to Grafana API: {url}")
        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(dashboard_model))
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            result = response.json()
            dashboard_url = f"{GRAFANA_URL}{result['url']}"
            return f"Grafana dashboard '{title}' created successfully! URL: {dashboard_url}"
        except requests.exceptions.RequestException as e:
            error_message = f"Error creating Grafana dashboard: {e}"
            if response is not None:
                try:
                    error_details = response.json()
                    error_message += f" - Details: {error_details.get('message', str(error_details))}"
                except json.JSONDecodeError:
                    error_message += f" - Response: {response.text}"
            print(error_message, file=os.sys.stderr)
            return error_message
        except Exception as e:
            return f"An unexpected error occurred: {e}"

# Example of how to use this tool directly (for testing)
if __name__ == "__main__":
    # Set environment variables for testing
    os.environ["GRAFANA_URL"] = "http://localhost:3000"
    os.environ["GRAFANA_API_KEY"] = "YOUR_GRAFANA_API_KEY" # Replace with your actual key
    os.environ["FIWARE_DATASOURCE_NAME"] = "Fiware Orion Data Source" # Replace with your actual DS name

    tools_instance = GrafanaTools()
    print(tools_instance.create_grafana_dashboard(
        title="Test Fiware Dashboard",
        description="Dashboard for testing Fiware data visualization.",
        panel_title="Temperature over Time",
        fiware_entity_type="RoomTemperature",
        fiware_attribute="temperature",
        time_field="TimeInstant",
        interval="1h"
    ))