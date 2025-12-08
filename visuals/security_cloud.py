from graphviz import Digraph

def build_cloud_security_diagram(output_filename="cloud_security"):
    # --- THEME ---
    BG_COLOR = "#000000"          # black background
    TEXT_COLOR = "#FFFFFF"        # white text
    EDGE_COLOR = "#AAAAAA"        # light grey edges
    GOOD_GOLD = "#C99522"         # gold-yellow for cloud-positive components
    BUFFER_GREY = "#444444"       # neutral/buffer

    dot = Digraph("CloudSecurity", format="png")

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
        color=TEXT_COLOR  # white borders
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

    # 2. API Gateway (HTTPS endpoint) - gold (positive cloud)
    dot.node(
        "api_gw",
        "API Gateway (HTTPS endpoint)\n"
        "- Throttling limits\n"
        "- Integrated with WAF",
        fillcolor=GOOD_GOLD,
        penwidth="2"
    )

    # 3. AWS WAF Web ACL - also gold as active protection
    dot.node(
        "waf",
        "AWS WAF Web ACL\n"
        "- Managed rules (SQLi/XSS, bad bots)\n"
        "- Rate-based rule (per-IP)",
        fillcolor=GOOD_GOLD
    )

    # 4. Lambda: rec-get-recommendations - grey buffer (readable)
    dot.node(
        "lambda_fn",
        "Lambda: rec-get-recommendations\n"
        "- Uses IAM role with\n"
        "  DynamoDB read-only",
        fillcolor=BUFFER_GREY
    )

    # 5. DynamoDB: rec-recommendations - grey buffer (readable)
    dot.node(
        "dynamodb",
        "DynamoDB: rec-recommendations\n"
        "- Encrypted at rest\n"
        "- Precomputed recs from\n"
        "  training pipeline",
        fillcolor=BUFFER_GREY
    )

    # Edges (vertical chain)
    dot.edge("client", "api_gw")
    dot.edge("api_gw", "waf")
    dot.edge("waf", "lambda_fn")
    dot.edge("lambda_fn", "dynamodb")

    dot.render(output_filename, cleanup=True)
    print(f"Diagram written to {output_filename}.png")

if __name__ == "__main__":
    build_cloud_security_diagram()