#!/usr/bin/env python3

import html
import json

from config import HEALTH_DATA_FILE, REPORT_FILE


def display(value):

    if value is None:
        return "Unavailable"

    return html.escape(str(value))


def generate_report(data):

    status = data["status"]
    load = data.get("load") or {}
    application = data.get("application", {})
    url_checks = {"Application": application}
    url_checks.update(data.get("url_checks", {}))

    html = f"""
<html>

<head>

<title>System Health Report</title>

<style>

body {{
    font-family: Arial;
    margin: 40px;
}}

table {{
    border-collapse: collapse;
    width: 70%;
}}

th, td {{
    border: 1px solid #ccc;
    padding: 10px;
}}

th {{
    background-color: #eee;
}}

</style>

</head>

<body>

<h1>System Health Report</h1>

<p>
Generated: {data["timestamp"]}
</p>

<h2>Overall Status: {status}</h2>

<table>

<tr>
<th>Metric</th>
<th>Value</th>
</tr>

<tr>
<td>CPU Usage</td>
<td>{display(data.get("cpu"))}%</td>
</tr>

<tr>
<td>Memory Usage</td>
<td>{display(data.get("memory"))}%</td>
</tr>

<tr>
<td>Disk Usage</td>
<td>{display(data.get("disk"))}%</td>
</tr>

<tr>
<td>Load Average - 1 min</td>
<td>{display(load.get("1_min"))}</td>
</tr>

<tr>
<td>Load Average - 5 min</td>
<td>{display(load.get("5_min"))}</td>
</tr>

<tr>
<td>Load Average - 15 min</td>
<td>{display(load.get("15_min"))}</td>
</tr>

</table>

<h2>Services</h2>

<table>
<tr><th>Service</th><th>Status</th><th>State</th></tr>
{''.join(f'<tr><td>{display(name)}</td><td>{display(service.get("status"))}</td><td>{display(service.get("state"))}</td></tr>' for name, service in data.get("services", {}).items()) or '<tr><td colspan="3">No services configured</td></tr>'}
</table>

<h2>Docker Containers</h2>

<table>
<tr><th>Container</th><th>Image</th><th>Status</th><th>Health</th></tr>
{''.join(f'<tr><td>{display(container.get("name"))}</td><td>{display(container.get("image"))}</td><td>{display(container.get("status"))}</td><td>{display(container.get("health"))}</td></tr>' for container in data.get("docker", {}).get("containers", [])) or '<tr><td colspan="4">No containers found</td></tr>'}
</table>

<p>Docker available: {display(data.get("docker", {}).get("available"))}</p>

<h2>URL Checks</h2>

<table>
<tr><th>Name</th><th>URL</th><th>Status</th><th>HTTP Code</th></tr>
{''.join(f'<tr><td>{display(name)}</td><td>{display(check.get("url"))}</td><td>{display(check.get("status"))}</td><td>{display(check.get("http_code"))}</td></tr>' for name, check in url_checks.items()) or '<tr><td colspan="4">No URLs configured</td></tr>'}
</table>

<h2>Problems</h2>

<ul>
"""

    if data["problems"]:

        for problem in data["problems"]:

            html += f"<li>{display(problem)}</li>"

    else:

        html += "<li>No problems detected</li>"

    html += """

</ul>

</body>

</html>
"""

    with open(
        REPORT_FILE,
        "w"
    ) as file:

        file.write(html)


def main():

    with open(HEALTH_DATA_FILE) as file:
        data = json.load(file)

    generate_report(data)


if __name__ == "__main__":
    main()