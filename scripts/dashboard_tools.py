from typing import List
from langchain_core.tools import tool

class DashboardGenerationTools:
    """
    A collection of tools for generating dashboard template components.
    """
    @tool
    def pie_chart(data: List[str]) -> str:
        """A function to write a template for a pie chart"""
        traces = ", ".join(data)
        return f"""Pie:
    label is pie
    type is pie_chart
    source is first
    traces -> {traces}
    pie_chart_type is pie"""

    @tool
    def bar_chart(data: List[str]) -> str:
        """A function to write a template for a bar chart."""
        traces = ", ".join(data)
        return f"""Bar:
    label is bar
    type is bar_chart
    source is first
    traces -> dateObserved, {traces}"""

    @tool
    def time_series(data: List[str]) -> str:
        """A function to write a template for a time series"""
        traces = ", ".join(data)
        return f"""TS:
    label is ts
    type is timeseries
    source is first
    traces -> dateObserved, {traces}"""

    @tool
    def application(app_type: str, dashboard: str, layout: str, roles: List[str], panels: List[str]) -> str:
        """Generates the application section of the template."""
        roles_str = ", ".join(roles)
        panels_str = ", ".join(panels)
        return f"""application:
    type is {app_type}
    dashboard is {dashboard}
    layout is {layout}
    roles -> {roles_str}
    panels -> {panels_str}"""

    @tool
    def map_chart(data: List[str]) -> str:
        """Generates the Map section of the template."""
        data_str = ", ".join(data)
        return f"""Map:
    label is map
    type is geomap
    source is first
    data -> {data_str}"""

    @tool
    def service(title: str, version: str, scope: str) -> str:
        """Generates the service section of the template."""
        return f"""service:
    title is {title} dashboard
    version is {version}
    scope is {scope}"""

    @tool
    def xy_chart(data: List[str]) -> str:
        """Generates the XY section of the template."""
        traces = ", ".join(data)
        return f"""XY:
    label is xy
    type is xy_chart
    source is first
    traces -> {traces}"""

    @tool
    def host(uri: str, port: int, env_type: str) -> str:
        """Generates the local section of the template."""
        return f"""local:
    uri is {uri}
    port is {port}
    type is {env_type}"""

    @tool
    def first(source_type: str, provider: str, uri: str, query: str) -> str:
        """Generates the first section of the template, describing the data source."""
        return f"""first:
    type is {source_type}
    provider is {provider}
    uri is {uri}
    query is {query}"""