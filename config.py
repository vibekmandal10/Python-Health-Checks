SMTP_SERVER = "smtp.company.com"
SMTP_PORT = 587

SMTP_USERNAME = "monitoring@company.com"
SMTP_PASSWORD = "YOUR_PASSWORD"

FROM_EMAIL = "monitoring@company.com"
TO_EMAIL = "sre-team@company.com"

APPLICATION_URL = "http://localhost:8080/health"
SERVICES_TO_CHECK = ("nginx", "jenkins","docker")
URLS_TO_CHECK = {
	"Jenkins": "http://localhost:8080/login",
	"Nginx": "http://localhost/",
}
PUBLIC_URLS_TO_CHECK = {}

CPU_THRESHOLD = 0
MEMORY_THRESHOLD = 0
DISK_THRESHOLD = 0

LOG_FILE = "logs/health_check.log"
HEALTH_DATA_FILE = "reports/health_data.json"
REPORT_FILE = "reports/health_report.html"
