import os
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
from langchain.tools import tool
from datetime import datetime
import re
from collections import Counter

# Environment configuration
API_BRIDGE_URL = os.getenv("API_BRIDGE_URL", "http://host.docker.internal:8000")
ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.getenv("GRAFANA_PASSWORD", "admin")
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "smart_data_service")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/data")

class SmartGrafanaDashboardTool:
    
    @staticmethod
    def discover_available_entities() -> Dict[str, Any]:
        """
        Dynamically discovers all available entity types from FIWARE/API Bridge
        This is the smart part - no hardcoding!
        """
        discovered_entities = {}
        
        try:
            # Try to get all entity types from Orion Context Broker
            headers = {
                "Fiware-Service": FIWARE_SERVICE,
                "Fiware-ServicePath": FIWARE_SERVICE_PATH,
                "Accept": "application/json"
            }
            
            # Get all entities to discover types
            response = requests.get(
                f"{ORION_URL}/v2/entities",
                headers=headers,
                params={"limit": 1000, "options": "keyValues,count"}
            )
            
            if response.status_code == 200:
                entities = response.json()
                
                # Extract unique entity types and their attributes
                for entity in entities:
                    entity_type = entity.get("type", "Unknown")
                    
                    if entity_type not in discovered_entities:
                        discovered_entities[entity_type] = {
                            "count": 0,
                            "attributes": set(),
                            "sample_data": {},
                            "data_types": {}
                        }
                    
                    discovered_entities[entity_type]["count"] += 1
                    
                    # Discover attributes and their types
                    for key, value in entity.items():
                        if key not in ["id", "type"]:
                            discovered_entities[entity_type]["attributes"].add(key)
                            
                            # Infer data type from value
                            if isinstance(value, (int, float)):
                                discovered_entities[entity_type]["data_types"][key] = "number"
                            elif isinstance(value, bool):
                                discovered_entities[entity_type]["data_types"][key] = "boolean"
                            elif isinstance(value, dict):
                                if "coordinates" in value or "lat" in value or "lon" in value:
                                    discovered_entities[entity_type]["data_types"][key] = "location"
                                else:
                                    discovered_entities[entity_type]["data_types"][key] = "object"
                            elif "date" in key.lower() or "time" in key.lower():
                                discovered_entities[entity_type]["data_types"][key] = "timestamp"
                            else:
                                discovered_entities[entity_type]["data_types"][key] = "string"
                            
                            # Keep sample data for analysis
                            if key not in discovered_entities[entity_type]["sample_data"]:
                                discovered_entities[entity_type]["sample_data"][key] = value
                
                # Convert sets to lists for JSON serialization
                for entity_type in discovered_entities:
                    discovered_entities[entity_type]["attributes"] = list(
                        discovered_entities[entity_type]["attributes"]
                    )
            
        except Exception as e:
            print(f"Error discovering entities from Orion: {e}")
            
        # If Orion discovery fails, try API Bridge discovery
        if not discovered_entities:
            discovered_entities = SmartGrafanaDashboardTool.discover_from_api_bridge()
        
        return discovered_entities
    
    @staticmethod
    def discover_from_api_bridge() -> Dict[str, Any]:
        """
        Fallback discovery method using the API bridge
        Tries common entity type names to discover what's available
        """
        discovered = {}
        
        # Common entity patterns to try (can be extended)
        common_patterns = [
            "Parking", "Product", "Weather", "Traffic", "Air", "Water",
            "Energy", "Waste", "Light", "Patient", "Vehicle", "Building",
            "Device", "Sensor", "Alert", "Event", "User", "Zone", "Street"
        ]
        
        for pattern in common_patterns:
            for suffix in ["", "Spot", "Observed", "Container", "Consumption", "Quality", "Flow"]:
                entity_type = f"{pattern}{suffix}"
                
                try:
                    url = f"{API_BRIDGE_URL}/data?type={entity_type}"
                    response = requests.get(url, timeout=2)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data and isinstance(data, list) and len(data) > 0:
                            # Analyze the data structure
                            sample = data[0]
                            
                            discovered[entity_type] = {
                                "count": len(data),
                                "attributes": list(sample.keys()),
                                "sample_data": sample,
                                "data_types": SmartGrafanaDashboardTool.infer_data_types(sample)
                            }
                            
                except:
                    continue
        
        return discovered
    
    @staticmethod
    def infer_data_types(sample_data: Dict) -> Dict[str, str]:
        """
        Intelligently infer data types from sample data
        """
        data_types = {}
        
        for key, value in sample_data.items():
            if isinstance(value, bool):
                data_types[key] = "boolean"
            elif isinstance(value, (int, float)):
                data_types[key] = "number"
            elif isinstance(value, dict):
                if any(k in str(value).lower() for k in ["lat", "lon", "coord"]):
                    data_types[key] = "location"
                else:
                    data_types[key] = "object"
            elif any(term in key.lower() for term in ["date", "time", "created", "modified", "observed"]):
                data_types[key] = "timestamp"
            else:
                data_types[key] = "string"
        
        return data_types
    
    @staticmethod
    def analyze_prompt_intent(prompt: str, available_entities: Dict) -> Dict[str, Any]:
        """
        Smart NLP-like analysis of user prompt to understand intent
        without relying on hardcoded keywords
        """
        prompt_lower = prompt.lower()
        words = prompt_lower.split()
        
        # Score each available entity based on prompt relevance
        entity_scores = {}
        
        for entity_type, entity_info in available_entities.items():
            score = 0
            entity_lower = entity_type.lower()
            
            # Direct entity name match
            if entity_lower in prompt_lower:
                score += 10
            
            # Partial word matches
            for word in words:
                if word in entity_lower:
                    score += 5
                elif entity_lower in word:
                    score += 3
            
            # Attribute matches
            for attr in entity_info.get("attributes", []):
                attr_lower = attr.lower()
                if attr_lower in prompt_lower:
                    score += 3
                for word in words:
                    if word in attr_lower or attr_lower in word:
                        score += 1
            
            # Semantic similarity (basic implementation)
            # Check for related concepts
            if "parking" in prompt_lower and "spot" in entity_lower:
                score += 5
            if "available" in prompt_lower and any(a in str(entity_info["attributes"]).lower() 
                                                  for a in ["available", "free", "occupied"]):
                score += 3
            if "monitor" in prompt_lower or "track" in prompt_lower:
                score += 1  # Everything can be monitored
            
            if score > 0:
                entity_scores[entity_type] = score
        
        # Sort entities by score and select top matches
        sorted_entities = sorted(entity_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Determine visualization preferences from prompt
        viz_preferences = SmartGrafanaDashboardTool.detect_visualization_preferences(prompt)
        
        return {
            "matched_entities": [e[0] for e in sorted_entities[:5]],  # Top 5 matches
            "entity_scores": dict(sorted_entities),
            "visualization_preferences": viz_preferences,
            "time_range": SmartGrafanaDashboardTool.extract_time_range(prompt)
        }
    
    @staticmethod
    def detect_visualization_preferences(prompt: str) -> Dict[str, Any]:
        """
        Detect what kind of visualizations user might want based on prompt
        """
        prompt_lower = prompt.lower()
        preferences = {
            "show_trends": any(word in prompt_lower for word in ["trend", "over time", "history", "timeline"]),
            "show_current": any(word in prompt_lower for word in ["current", "now", "real-time", "live"]),
            "show_comparison": any(word in prompt_lower for word in ["compare", "versus", "difference"]),
            "show_distribution": any(word in prompt_lower for word in ["distribution", "spread", "range"]),
            "show_alerts": any(word in prompt_lower for word in ["alert", "warning", "critical", "threshold"])
        }
        return preferences
    
    @staticmethod
    def extract_time_range(prompt: str) -> str:
        """
        Extract time range preferences from prompt
        """
        prompt_lower = prompt.lower()
        
        if "today" in prompt_lower:
            return "now-24h"
        elif "week" in prompt_lower:
            return "now-7d"
        elif "month" in prompt_lower:
            return "now-30d"
        elif "year" in prompt_lower:
            return "now-1y"
        elif "hour" in prompt_lower:
            return "now-1h"
        else:
            return "now-6h"  # Default
    
    @staticmethod
    def smart_panel_generator(
        entity_type: str,
        entity_info: Dict,
        panel_id: int,
        position: Dict,
        viz_preferences: Dict
    ) -> Dict:
        """
        Intelligently generate panel based on data characteristics
        """
        attributes = entity_info.get("attributes", [])
        data_types = entity_info.get("data_types", {})
        
        # Determine best visualization based on data types
        numeric_attrs = [a for a in attributes if data_types.get(a) == "number"]
        time_attrs = [a for a in attributes if data_types.get(a) == "timestamp"]
        
        # Smart visualization selection
        if viz_preferences.get("show_trends") and time_attrs and numeric_attrs:
            viz_type = "timeseries"
        elif len(numeric_attrs) > 3:
            viz_type = "barchart"
        elif len(numeric_attrs) == 1:
            viz_type = "stat"
        elif any("level" in a.lower() or "percentage" in a.lower() for a in numeric_attrs):
            viz_type = "gauge"
        elif entity_info.get("count", 0) > 10:
            viz_type = "table"
        else:
            viz_type = "bargauge"
        
        # Create intelligent panel title
        title = SmartGrafanaDashboardTool.generate_smart_title(entity_type, attributes, viz_preferences)
        
        # Build panel configuration
        panel = {
            "id": panel_id,
            "title": title,
            "type": viz_type,
            "gridPos": position,
            "datasource": {
                "type": "yesoreyeram-infinity-datasource",
                "uid": "aerbbnh0xrwu8f"
            }
        }
        
        # Configure data source intelligently
        target = {
            "refId": "A",
            "datasource": {
                "type": "yesoreyeram-infinity-datasource",
                "uid": "aerbbnh0xrwu8f"
            },
            "type": "json",
            "source": "url",
            "url": f"{API_BRIDGE_URL}/data?type={entity_type}",
            "url_options": {"method": "GET", "data": ""},
            "filters": [],
            "global_query_id": "",
            "root_selector": ""
        }
        
        # Smart column selection
        if numeric_attrs or time_attrs:
            target["columns"] = []
            
            # Prioritize important attributes
            priority_attrs = SmartGrafanaDashboardTool.prioritize_attributes(
                attributes, data_types, entity_type
            )
            
            for attr in priority_attrs[:5]:  # Limit to 5 most relevant
                target["columns"].append({
                    "selector": attr,
                    "text": SmartGrafanaDashboardTool.humanize_attribute_name(attr),
                    "type": data_types.get(attr, "string")
                })
        
        # Set appropriate format
        target["format"] = "timeseries" if viz_type == "timeseries" else "dataframe"
        
        panel["targets"] = [target]
        panel["fieldConfig"] = SmartGrafanaDashboardTool.get_smart_field_config(viz_type, entity_info)
        panel["options"] = SmartGrafanaDashboardTool.get_smart_options(viz_type, entity_info)
        
        return panel
    
    @staticmethod
    def generate_smart_title(entity_type: str, attributes: List[str], viz_preferences: Dict) -> str:
        """
        Generate intelligent panel title based on context
        """
        # Remove common suffixes
        clean_type = entity_type.replace("Observed", "").replace("Container", "")
        
        # Add context based on attributes
        if any("available" in a.lower() for a in attributes):
            return f"{clean_type} Availability"
        elif any("level" in a.lower() for a in attributes):
            return f"{clean_type} Levels"
        elif viz_preferences.get("show_trends"):
            return f"{clean_type} Trends"
        elif viz_preferences.get("show_current"):
            return f"Current {clean_type} Status"
        else:
            return f"{clean_type} Monitoring"
    
    @staticmethod
    def prioritize_attributes(attributes: List[str], data_types: Dict, entity_type: str) -> List[str]:
        """
        Intelligently prioritize which attributes to display
        """
        priority_score = {}
        
        for attr in attributes:
            score = 0
            attr_lower = attr.lower()
            
            # High priority keywords
            high_priority = ["total", "available", "level", "status", "value", "count", "rate"]
            for keyword in high_priority:
                if keyword in attr_lower:
                    score += 10
            
            # Medium priority - numeric data
            if data_types.get(attr) == "number":
                score += 5
            
            # Lower priority - metadata
            if attr_lower in ["id", "type", "created", "modified"]:
                score -= 5
            
            priority_score[attr] = score
        
        # Sort by priority
        sorted_attrs = sorted(priority_score.items(), key=lambda x: x[1], reverse=True)
        return [a[0] for a in sorted_attrs]
    
    @staticmethod
    def humanize_attribute_name(attr: str) -> str:
        """
        Convert attribute names to human-readable format
        """
        # Handle camelCase
        result = re.sub('([a-z])([A-Z])', r'\1 \2', attr)
        # Handle snake_case
        result = result.replace('_', ' ')
        # Capitalize properly
        return result.title()
    
    @staticmethod
    def get_smart_field_config(viz_type: str, entity_info: Dict) -> Dict:
        """
        Generate smart field configuration based on data characteristics
        """
        config = {
            "defaults": {
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [{"color": "green"}]
                }
            },
            "overrides": []
        }
        
        # Smart threshold detection
        sample_data = entity_info.get("sample_data", {})
        for key, value in sample_data.items():
            if isinstance(value, (int, float)):
                if "percentage" in key.lower() or "level" in key.lower():
                    config["defaults"]["thresholds"]["steps"] = [
                        {"color": "green", "value": 0},
                        {"color": "yellow", "value": 50},
                        {"color": "red", "value": 80}
                    ]
                    break
        
        # Visualization-specific configs
        if viz_type == "timeseries":
            config["defaults"]["color"] = {"mode": "palette-classic"}
            config["defaults"]["custom"] = {
                "drawStyle": "line",
                "lineInterpolation": "smooth",
                "lineWidth": 2,
                "fillOpacity": 10,
                "showPoints": "auto"
            }
        elif viz_type in ["gauge", "stat"]:
            config["defaults"]["color"] = {"mode": "thresholds"}
        
        return config
    
    @staticmethod
    def get_smart_options(viz_type: str, entity_info: Dict) -> Dict:
        """
        Generate smart visualization options
        """
        if viz_type == "timeseries":
            return {
                "legend": {"displayMode": "list", "placement": "bottom", "showLegend": True},
                "tooltip": {"mode": "multi", "sort": "desc"}
            }
        elif viz_type == "gauge":
            return {
                "orientation": "auto",
                "showThresholdLabels": True,
                "showThresholdMarkers": True,
                "reduceOptions": {"calcs": ["lastNotNull"], "values": False}
            }
        elif viz_type == "stat":
            return {
                "orientation": "auto",
                "textMode": "auto",
                "colorMode": "value",
                "graphMode": "area",
                "reduceOptions": {"calcs": ["lastNotNull"], "values": False}
            }
        elif viz_type == "barchart":
            return {
                "orientation": "auto",
                "barWidth": 0.9,
                "groupWidth": 0.7,
                "legend": {"displayMode": "list", "placement": "right"}
            }
        elif viz_type == "table":
            return {
                "showHeader": True,
                "sortBy": [],
                "filterable": True
            }
        else:  # bargauge
            return {
                "displayMode": "gradient",
                "orientation": "horizontal",
                "reduceOptions": {"calcs": ["lastNotNull"], "values": False}
            }
    
    @tool
    @staticmethod
    def create_smart_dashboard(prompt: str, auto_deploy: bool = False) -> str:
        """
        Creates an intelligent Grafana dashboard by discovering available data
        and matching it to user intent without hardcoded mappings.
        
        Args:
            prompt: Natural language description of desired dashboard
            auto_deploy: Whether to automatically deploy to Grafana
        
        Returns:
            JSON string with dashboard configuration and metadata
        
        Example prompts:
        - "Show me what data is available about parking"
        - "I want to monitor everything that's currently active"
        - "Create a dashboard for all available sensors"
        - "Display availability of resources"
        """
        
        print("🔍 Discovering available data sources...")
        available_entities = SmartGrafanaDashboardTool.discover_available_entities()
        
        if not available_entities:
            return json.dumps({
                "error": "No data sources discovered",
                "suggestion": "Please check your FIWARE/API Bridge connection"
            })
        
        print(f"✅ Discovered {len(available_entities)} entity types")
        
        # Analyze user intent
        print("🧠 Analyzing your request...")
        intent_analysis = SmartGrafanaDashboardTool.analyze_prompt_intent(prompt, available_entities)
        
        selected_entities = intent_analysis["matched_entities"]
        if not selected_entities:
            # If no specific match, show top available entities
            selected_entities = list(available_entities.keys())[:4]
        
        print(f"📊 Creating dashboard with {len(selected_entities)} data sources")
        
        # Generate dashboard
        panels = []
        panel_id = 1
        
        # Smart grid layout
        for i, entity_type in enumerate(selected_entities):
            if entity_type not in available_entities:
                continue
            
            entity_info = available_entities[entity_type]
            
            # Calculate position (adaptive grid)
            if len(selected_entities) <= 2:
                # Large panels for 1-2 entities
                position = {"x": i * 12, "y": 0, "w": 12, "h": 10}
            elif len(selected_entities) <= 4:
                # 2x2 grid for 3-4 entities
                position = {
                    "x": (i % 2) * 12,
                    "y": (i // 2) * 8,
                    "w": 12,
                    "h": 8
                }
            else:
                # 3 column layout for 5+ entities
                position = {
                    "x": (i % 3) * 8,
                    "y": (i // 3) * 6,
                    "w": 8,
                    "h": 6
                }
            
            panel = SmartGrafanaDashboardTool.smart_panel_generator(
                entity_type=entity_type,
                entity_info=entity_info,
                panel_id=panel_id,
                position=position,
                viz_preferences=intent_analysis["visualization_preferences"]
            )
            
            panels.append(panel)
            panel_id += 1
        
        # Generate dashboard title from prompt
        title = f"Smart Dashboard - {' '.join(prompt.split()[:5])}"
        
        dashboard = {
            "annotations": {
                "list": [{
                    "builtIn": 1,
                    "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }]
            },
            "description": f"AI-generated dashboard: {prompt}",
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "id": None,
            "links": [],
            "panels": panels,
            "schemaVersion": 41,
            "tags": ["ai-generated", "smart", "fiware"],
            "templating": {"list": []},
            "time": {"from": intent_analysis["time_range"], "to": "now"},
            "timepicker": {},
            "timezone": "browser",
            "title": title,
            "uid": None,
            "version": 1
        }
        
        # Save to file
        filename = f"smart_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        result = {
            "status": "success",
            "filename": filename,
            "title": title,
            "discovered_entities": len(available_entities),
            "selected_entities": selected_entities,
            "panel_count": len(panels),
            "intent_analysis": intent_analysis,
            "dashboard_json": dashboard
        }
        
        # Auto-deploy if requested
        if auto_deploy:
            deployment = SmartGrafanaDashboardTool.deploy_to_grafana(dashboard)
            result["deployment"] = deployment
        
        return json.dumps(result, indent=2)
    
    @staticmethod
    def deploy_to_grafana(dashboard: Dict) -> Dict:
        """
        Deploy dashboard to Grafana
        """
        try:
            payload = {
                "dashboard": dashboard,
                "overwrite": True,
                "message": "Smart AI-generated dashboard"
            }
            
            response = requests.post(
                f"{GRAFANA_URL}/api/dashboards/db",
                json=payload,
                auth=(GRAFANA_USER, GRAFANA_PASSWORD),
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "deployed",
                    "url": f"{GRAFANA_URL}/d/{result.get('uid')}/",
                    "uid": result.get("uid")
                }
            else:
                return {"status": "failed", "error": response.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @tool
    @staticmethod
    def discover_and_list_data() -> str:
        """
        Discovers all available data sources and their characteristics.
        Useful for understanding what data is available before creating dashboards.
        
        Returns:
            JSON string with discovered entities and their properties
        """
        entities = SmartGrafanaDashboardTool.discover_available_entities()
        
        summary = {
            "total_entity_types": len(entities),
            "entities": {}
        }
        
        for entity_type, info in entities.items():
            summary["entities"][entity_type] = {
                "record_count": info.get("count", 0),
                "attributes": info.get("attributes", []),
                "data_types": info.get("data_types", {}),
                "sample_values": {
                    k: str(v)[:50] for k, v in info.get("sample_data", {}).items()
                }
            }
        
        return json.dumps(summary, indent=2)


# Example usage
def example_usage():
    """
    Examples of using the smart dashboard tool
    """
    # Example 1: Let the AI figure out what's available
    result = SmartGrafanaDashboardTool.create_smart_dashboard(
        "I want to see all available parking information"
    )
    print("Smart Dashboard Result:")
    print(result)
    
    # Example 2: Discover what data exists
    discovery = SmartGrafanaDashboardTool.discover_and_list_data()
    print("\nDiscovered Data Sources:")
    print(discovery)
    
    # Example 3: Very vague prompt - AI figures it out
    result2 = SmartGrafanaDashboardTool.create_smart_dashboard(
        "Show me everything that's being monitored",
        auto_deploy=False
    )
    print("\nVague Prompt Result:")
    print(result2)

if __name__ == "__main__":
    example_usage()