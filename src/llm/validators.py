from datetime import datetime, timezone
import re


def validate_url(url: str | None) -> bool:
    if not url:
        return False
    pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')
    return bool(pattern.match(url))


def validate_startup(record: dict) -> tuple[bool, list[str]]:
    errors = []

    if not record.get("source", {}).get("url"):
        errors.append("Missing source URL")
    elif not validate_url(record["source"]["url"]):
        errors.append(f"Invalid source URL: {record['source']['url']}")

    if not record.get("content", {}).get("entityName"):
        errors.append("Missing entity name")

    if not record.get("collectedAt"):
        errors.append("Missing collectedAt timestamp")

    emp = record.get("content", {}).get("data", {}).get("employeeCount")
    if emp is not None and not isinstance(emp, int):
        errors.append(f"employeeCount must be integer, got: {type(emp)}")

    return len(errors) == 0, errors


def sanitize_record(record: dict) -> dict:
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [clean(i) for i in value]
        if value == "" or value == "N/A" or value == "n/a" or value == "None":
            return None
        return value

    record = clean(record)
    emp = record.get("content", {}).get("data", {}).get("employeeCount")
    if emp is not None and isinstance(emp, str) and emp.isdigit():
        record["content"]["data"]["employeeCount"] = int(emp)
    year = record.get("content", {}).get("data", {}).get("foundedYear")
    if year is not None and isinstance(year, str) and year.isdigit():
        record["content"]["data"]["foundedYear"] = int(year)
    return record
