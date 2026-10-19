import json
import logging
import boto3
from botocore.exceptions import ClientError

# =============================================================
# lambda_delete_user.py
# Amazon Connect — Delete User Lambda Function
# ACCNA-397 | Kemper SRE Automation Team
#
# Function Name : connect-offboarding-deleteuser-ACCNA397-dev
# Action        : Deletes agent from Connect using agent_id (UUID)
# Input         : agent_id comes from check_user Lambda response
# Returns       : SUCCESS  or  ERROR
# =============================================================

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info(f"Event received: {json.dumps(event)}")

    # ── Validate payload ──────────────────────────────────────
    employee_id = event.get("employee_id", "").strip()
    agent_id    = event.get("agent_id", "").strip()
    instance_id = event.get("instance_id", "").strip()

    if not employee_id:
        return build_response("ERROR", "Missing required field: employee_id")
    if not agent_id:
        return build_response("ERROR", "Missing required field: agent_id")
    if not instance_id:
        return build_response("ERROR", "Missing required field: instance_id")

    logger.info(f"Deleting user — EmployeeId: {employee_id} | AgentId: {agent_id} | Instance: {instance_id}")

    # ── Delete user from Connect ──────────────────────────────
    connect = boto3.client("connect")

    try:
        connect.delete_user(
            InstanceId=instance_id,
            UserId=agent_id
        )

        logger.info(f"User deleted successfully — AgentId: {agent_id} | EmployeeId: {employee_id}")
        return build_response(
            "SUCCESS",
            f"User {employee_id} successfully deleted from Amazon Connect",
            userId=agent_id
        )

    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        logger.error(f"ClientError: {code} — {msg}")

        if code == "ResourceNotFoundException":
            return build_response(
                "ERROR",
                f"User {agent_id} not found in Connect — may already be deleted"
            )
        return build_response("ERROR", f"AWS error: {code} — {msg}")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return build_response("ERROR", f"Unexpected error: {str(e)}")


def build_response(status, message, **kwargs):
    response = {"status": status, "message": message}
    response.update(kwargs)
    logger.info(f"Response: {json.dumps(response)}")
    return response
