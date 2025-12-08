from graphviz import Digraph

def build_non_cloud_security_diagram(output_filename="non_cloud_security"):
    # --- THEME ---
    BG_COLOR = "#000000"          # black background
    TEXT_COLOR = "#FFFFFF"        # white text
    EDGE_COLOR = "#AAAAAA"        # light grey edges
    BAD_RED = "#FF0000"           # true red for bad choice
    BUFFER_GREY = "#444444"       # neutral/buffer
    BUFFER_LIGHT = "#777777"      # lighter grey / secondary buffer

    dot = Digraph("NonCloudSecurity", format="png")

    # Global graph style
    dot.attr(
        bgcolor=BG_COLOR,
        rankdir="TB",
        splines="ortho",
        nodesep="0.5",
        ranksep="0.7"
    )
    dot.attr(
        "node",
        shape="box",
        style="rounded,filled",
        fontsize="11",
        fontname="Helvetica",
        fontcolor=TEXT_COLOR,
        color=TEXT_COLOR # node border color (white)
    )
    dot.attr(
        "edge",
        color=EDGE_COLOR,
        fontcolor=TEXT_COLOR
    )

    # 1. Client / Load Test (Locust) - neutral/buffer
    dot.node(
        "client",
        "Client / Load Test\n(Locust)",
        fillcolor=BUFFER_GREY
    )

    # 2. Public IP / Single Server - highlight as bad (red)
    dot.node(
        "single_server",
        "Public IP / Single Server\n"
        "- FastAPI (app.py)\n"
        "- Postgres (recommendations table)",
        fillcolor=BAD_RED,
        penwidth="2"
    )

    # 3. Local Logs & Metrics - buffer color
    dot.node(
        "logs",
        "Local Logs & Metrics\n"
        "- app logs\n"
        "- Postgres logs\n"
        "- system_metrics.csv\n"
        "  (monitor_system.py)",
        fillcolor=BUFFER_GREY
    )

    # 4. Manual Review - lighter buffer
    dot.node(
        "manual_review",
        "Manual Review\n"
        "- Human scans logs when\n"
        "  something looks wrong",
        fillcolor=BUFFER_LIGHT
    )

    # Edges (vertical chain)
    dot.edge("client", "single_server")
    dot.edge("single_server", "logs")
    dot.edge("logs", "manual_review")

    dot.render(output_filename, cleanup=True)
    print(f"Diagram written to {output_filename}.png")

if __name__ == "__main__":
    build_non_cloud_security_diagram()