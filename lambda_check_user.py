import json
import logging
import boto3
from botocore.exceptions import ClientError

# =============================================================
# lambda_check_user.py
# Amazon Connect — Check User Lambda Function
# ACCNA-397 | Kemper SRE Automation Team
#
# Function Name : connect-offboarding-checkuser-ACCNA397-dev
# Action        : Searches for agent by Employee ID in Connect
# Returns       : USER_FOUND + userId  or  USER_NOT_FOUND
# =============================================================

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info(f"Event received: {json.dumps(event)}")

    # ── Validate payload ──────────────────────────────────────
    employee_id = event.get("employee_id", "").strip()
    instance_id = event.get("instance_id", "").strip()

    if not employee_id:
        return build_response("ERROR", "Missing required field: employee_id")
    if not instance_id:
        return build_response("ERROR", "Missing required field: instance_id")

    logger.info(f"Searching for Employee ID: {employee_id} in instance: {instance_id}")

    # ── Search user in Connect ────────────────────────────────
    connect = boto3.client("connect")

    try:
        paginator   = connect.get_paginator("list_users")
        page_count  = 0
        total_users = 0

        for page in paginator.paginate(InstanceId=instance_id):
            page_count  += 1
            users        = page.get("UserSummaryList", [])
            total_users += len(users)

            for user in users:
                username = user.get("Username", "")
                user_id  = user.get("Id", "")

                if username.lower() == str(employee_id).lower():
                    logger.info(f"User found — Username: {username} | UserId: {user_id}")
                    return build_response(
                        "USER_FOUND",
                        f"User {employee_id} found in Amazon Connect",
                        userId=user_id
                    )

        logger.info(f"User not found after scanning {total_users} users across {page_count} pages")
        return build_response(
            "USER_NOT_FOUND",
            f"User {employee_id} not found in Amazon Connect"
        )

    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        logger.error(f"ClientError: {code} — {msg}")
        return build_response("ERROR", f"AWS error: {code} — {msg}")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return build_response("ERROR", f"Unexpected error: {str(e)}")


def build_response(status, message, **kwargs):
    response = {"status": status, "message": message}
    response.update(kwargs)
    logger.info(f"Response: {json.dumps(response)}")
    return response
