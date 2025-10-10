from grafanalib.core import Dashboard, Row, Graph, Target
from grafanalib.core import YAxes, YAxis, Legend

dashboard = Dashboard(
    title="My First Dashboard",
    description="A simple dashboard created with grafanalib."
).add_row(
    Row(panels=[
        Graph(
            title="CPU Usage",
            dataSource="Prometheus",  # Replace with your data source name
            targets=[
                Target(expr='sum(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)',
                       legendFormat="{{instance}} Idle CPU")
            ],
            yAxes=YAxes(
                YAxis(format="percent"),
                YAxis(format="percent")
            ),
            legend=Legend(show=True, alignAsTable=True)
        )
    ])
)