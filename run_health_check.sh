#!/bin/bash

LOG_FILE="logs/health_check.log"

PYTHON="/usr/bin/python3"

BASE_DIR=$(pwd)

echo "====================================" >> "$LOG_FILE"
echo "$(date) - Health check started" >> "$LOG_FILE"

cd "$BASE_DIR" || {

    echo "$(date) - ERROR: Cannot change directory" >> "$LOG_FILE"

    exit 1
}


$PYTHON health_check.py

HEALTH_EXIT_CODE=$?


if [ $HEALTH_EXIT_CODE -eq 0 ]; then

    echo "$(date) - Health check completed successfully" \
        >> "$LOG_FILE"

elif [ $HEALTH_EXIT_CODE -eq 2 ]; then

    echo "$(date) - WARNING: Health check found issues" \
        >> "$LOG_FILE"

else

    echo "$(date) - ERROR: Health check script failed" \
        >> "$LOG_FILE"

    exit 1

fi


$PYTHON generate_report.py

REPORT_EXIT_CODE=$?


if [ $REPORT_EXIT_CODE -ne 0 ]; then

    echo "$(date) - ERROR: Report generation failed" \
        >> "$LOG_FILE"

    exit 1

fi


# $PYTHON send_email.py

# EMAIL_EXIT_CODE=$?


# if [ $EMAIL_EXIT_CODE -ne 0 ]; then

#     echo "$(date) - ERROR: Email sending failed" \
#         >> "$LOG_FILE"

#     exit 1

# fi


# echo "$(date) - Health check completed successfully" \
#     >> "$LOG_FILE"

# exit 0