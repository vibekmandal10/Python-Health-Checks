#!/usr/bin/env python3

import json
import subprocess
import requests
import logging
import sys
import shutil
from datetime import datetime

from config import (
    APPLICATION_URL,
    CPU_THRESHOLD,
    MEMORY_THRESHOLD,
    DISK_THRESHOLD,
    HEALTH_DATA_FILE,
    LOG_FILE,
    PUBLIC_URLS_TO_CHECK,
    SERVICES_TO_CHECK,
    URLS_TO_CHECK
)


logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def run_command(command):
    """
    Execute Linux command and return output.
    """

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            logging.error(
                "Command failed: %s | Exit Code: %s",
                command,
                result.returncode
            )
            return None

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        logging.error("Command timeout: %s", command)
        return None

    except Exception as e:
        logging.exception("Command execution failed: %s", e)
        return None


def get_cpu_usage():
    """
    Get CPU usage using Linux top command.
    """

    output = run_command(
        "top -bn1 | grep 'Cpu(s)'"
    )

    if not output:
        return None

    try:
        idle = float(
            output.split("id,")[0].split()[-1]
        )

        cpu_usage = round(100 - idle, 2)

        return cpu_usage

    except Exception:
        logging.exception("Failed to parse CPU usage")
        return None


def get_memory_usage():
    """
    Get memory utilization.
    """

    output = run_command(
        "free -m"
    )

    if not output:
        return None

    try:
        lines = output.splitlines()

        memory_line = lines[1]

        values = memory_line.split()

        total = int(values[1])
        available = int(values[6])

        used = total - available

        percentage = round(
            (used / total) * 100,
            2
        )

        return percentage

    except Exception:
        logging.exception(
            "Failed to parse memory usage"
        )

        return None


def get_disk_usage():
    """
    Get root filesystem utilization.
    """

    try:

        total, used, free = shutil.disk_usage("/")

        percentage = round(
            (used / total) * 100,
            2
        )

        return percentage

    except Exception:
        logging.exception(
            "Failed to get disk usage"
        )

        return None


def get_load_average():
    """
    Get Linux load average.
    """

    try:

        load1, load5, load15 = (
            __import__("os").getloadavg()
        )

        return {
            "1_min": round(load1, 2),
            "5_min": round(load5, 2),
            "15_min": round(load15, 2)
        }

    except Exception:
        logging.exception(
            "Failed to get load average"
        )

        return None


def check_application():

    try:

        response = requests.get(
            APPLICATION_URL,
            timeout=10
        )

        if response.status_code == 200:

            logging.info(
                "Application health check successful"
            )

            return {
                "status": "UP",
                "http_code": response.status_code
            }

        else:

            logging.error(
                "Application returned HTTP %s",
                response.status_code
            )

            return {
                "status": "DOWN",
                "http_code": response.status_code
            }

    except requests.exceptions.Timeout:

        logging.error(
            "Application health check timed out"
        )

        return {
            "status": "DOWN",
            "http_code": "TIMEOUT"
        }

    except requests.exceptions.RequestException as e:

        logging.error(
            "Application health check failed: %s",
            e
        )

        return {
            "status": "DOWN",
            "http_code": "ERROR"
        }


def check_url(name, url):

    try:
        response = requests.get(url, timeout=10)
        status = "UP" if response.status_code < 400 else "DOWN"

        return {
            "name": name,
            "url": url,
            "status": status,
            "http_code": response.status_code
        }

    except requests.exceptions.RequestException as error:
        logging.error("URL health check failed for %s: %s", name, error)

        return {
            "name": name,
            "url": url,
            "status": "DOWN",
            "http_code": "ERROR",
            "error": str(error)
        }


def check_urls(urls):

    return {
        name: check_url(name, url)
        for name, url in urls.items()
    }


def check_service(service_name):

    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        service_state = result.stdout.strip() or result.stderr.strip()

        return {
            "status": "UP" if result.returncode == 0 else "DOWN",
            "state": service_state or "unknown"
        }

    except (OSError, subprocess.TimeoutExpired) as error:
        logging.error("Service check failed for %s: %s", service_name, error)

        return {
            "status": "UNKNOWN",
            "state": str(error)
        }


def check_docker_containers():

    container_ids = run_command("docker ps -aq")

    if container_ids is None:
        return {"available": False, "containers": []}

    containers = []

    for container_id in container_ids.splitlines():
        try:
            result = subprocess.run(
                ["docker", "inspect", container_id],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "docker inspect failed")

            details = json.loads(result.stdout)[0]
            state = details.get("State", {})
            health = (state.get("Health") or {}).get(
                "Status",
                "not configured"
            )

            containers.append({
                "id": details.get("Id", container_id)[:12],
                "name": details.get("Name", "").lstrip("/"),
                "image": details.get("Config", {}).get("Image", "unknown"),
                "status": state.get("Status", "unknown").upper(),
                "health": health.upper()
            })

        except (OSError, subprocess.TimeoutExpired, ValueError, IndexError, RuntimeError) as error:
            logging.error("Docker inspect failed for %s: %s", container_id, error)
            containers.append({
                "id": container_id[:12],
                "name": container_id[:12],
                "image": "unknown",
                "status": "UNKNOWN",
                "health": "UNKNOWN",
                "error": str(error)
            })

    return {"available": True, "containers": containers}


def evaluate_status(
    cpu,
    memory,
    disk,
    application,
    services,
    docker,
    url_checks
):

    problems = []

    if cpu is not None and cpu > CPU_THRESHOLD:
        problems.append(
            f"High CPU usage: {cpu}%"
        )

    if memory is not None and memory > MEMORY_THRESHOLD:
        problems.append(
            f"High memory usage: {memory}%"
        )

    if disk is not None and disk > DISK_THRESHOLD:
        problems.append(
            f"High disk usage: {disk}%"
        )

    if application["status"] != "UP":
        problems.append(
            "Application is DOWN"
        )

    for service_name, service in services.items():
        if service["status"] != "UP":
            problems.append(f"Service {service_name} is {service['status']}")

    if not docker["available"]:
        problems.append("Docker is unavailable")
    elif not docker["containers"]:
        problems.append("No Docker containers found")
    else:
        for container in docker["containers"]:
            if container["status"] != "RUNNING":
                problems.append(
                    f"Docker container {container['name']} is {container['status']}"
                )
            if container["health"] in (
                "UNHEALTHY",
                "STARTING",
                "UNKNOWN",
                "NOT CONFIGURED"
            ):
                problems.append(
                    f"Docker container {container['name']} health is {container['health']}"
                )

    for name, url_check in url_checks.items():
        if url_check["status"] != "UP":
            problems.append(f"URL check {name} is DOWN")

    if problems:
        return "CRITICAL", problems

    return "HEALTHY", []


def main():

    logging.info(
        "========== Health Check Started =========="
    )

    try:

        cpu = get_cpu_usage()

        memory = get_memory_usage()

        disk = get_disk_usage()

        load = get_load_average()

        application = check_application()
        services = {
            service_name: check_service(service_name)
            for service_name in SERVICES_TO_CHECK
        }
        docker = check_docker_containers()
        configured_urls = dict(URLS_TO_CHECK)
        configured_urls.update(PUBLIC_URLS_TO_CHECK)
        url_checks = check_urls(configured_urls)

        status, problems = evaluate_status(
            cpu,
            memory,
            disk,
            application,
            services,
            docker,
            url_checks
        )

        result = {
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "load": load,
            "application": application,
            "services": services,
            "docker": docker,
            "url_checks": url_checks,
            "status": status,
            "problems": problems
        }

        with open(HEALTH_DATA_FILE, "w") as file:
            json.dump(result, file, indent=2)

        logging.info(
            "Health check completed: %s",
            status
        )

        print(result)

        if status == "CRITICAL":

            logging.error(
                "Health check detected problems: %s",
                problems
            )

            sys.exit(2)

        sys.exit(0)

    except Exception as e:

        logging.exception(
            "Unexpected error: %s",
            e
        )

        sys.exit(1)


if __name__ == "__main__":
    main()