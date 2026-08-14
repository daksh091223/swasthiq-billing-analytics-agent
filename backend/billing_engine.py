from collections import defaultdict
from datetime import datetime, timezone
from pydantic import ValidationError
from models import BillingRecord

PAYMENT_MODES = ("cash", "card", "upi")


def parse_timestamp(timestamp: str) -> datetime:
    value = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    if value.tzinfo is None:
        raise ValueError("timestamp must include a UTC timezone")

    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("timestamp must be in UTC")

    return value


def gross_value(record: BillingRecord) -> int:
    return sum(
        item.qty * item.unit_price_paise
        for item in record.line_items
    )


def validate_business_rules(record: BillingRecord) -> None:
    gross = gross_value(record)

    if record.discount_paise > gross:
        raise ValueError("discount_paise cannot exceed gross line-item value")

    if record.is_refund and record.amount_paid_paise >= 0:
        raise ValueError("refund amount_paid_paise must be negative")

    if not record.is_refund and record.amount_paid_paise < 0:
        raise ValueError("non-refund amount_paid_paise cannot be negative")

    if not record.is_refund and record.amount_paid_paise > gross - record.discount_paise:
        raise ValueError("amount_paid_paise cannot exceed billed value")


def validate_row(raw_row, row_number: int):
    if not isinstance(raw_row, dict):
        return None, {
            "row_number": row_number,
            "visit_id": None,
            "code": "INVALID_BILLING_ROW",
            "field": "row",
            "message": "Row must be a JSON object",
        }

    try:
        record = BillingRecord.model_validate(raw_row)
        parse_timestamp(record.timestamp)
        validate_business_rules(record)
        return record, None

    except ValidationError as error:
        first = error.errors()[0]
        field = ".".join(str(part) for part in first["loc"])

        return None, {
            "row_number": row_number,
            "visit_id": raw_row.get("visit_id"),
            "code": "INVALID_BILLING_ROW",
            "field": field,
            "message": first["msg"],
        }

    except ValueError as error:
        return None, {
            "row_number": row_number,
            "visit_id": raw_row.get("visit_id"),
            "code": "INVALID_BILLING_ROW",
            "field": "timestamp" if "timestamp" in str(error) else "billing_record",
            "message": str(error),
        }


def build_eod_report(rows: list) -> dict:
    billed = defaultdict(int)
    collected = defaultdict(int)
    refunds = defaultdict(int)

    revenue_by_hour = defaultdict(int)
    medicine_quantity = defaultdict(int)
    medicine_revenue = defaultdict(int)

    rejected_rows = []
    processed_rows = 0
    seen_visit_ids = set()
    clinic_id = None

    for row_number, raw_row in enumerate(rows, start=1):
        record, error = validate_row(raw_row, row_number)

        if error:
            rejected_rows.append(error)
            continue

        if clinic_id is None:
            clinic_id = record.clinic_id
        elif record.clinic_id != clinic_id:
            rejected_rows.append({
                "row_number": row_number,
                "visit_id": record.visit_id,
                "code": "INVALID_BILLING_ROW",
                "field": "clinic_id",
                "message": "All rows in a billing log must belong to the same clinic",
            })
            continue

        if record.visit_id in seen_visit_ids:
            rejected_rows.append({
                "row_number": row_number,
                "visit_id": record.visit_id,
                "code": "INVALID_BILLING_ROW",
                "field": "visit_id",
                "message": "visit_id must be unique within the billing log",
            })
            continue

        seen_visit_ids.add(record.visit_id)
        processed_rows += 1

        if record.is_refund:
            refunds[record.payment_mode] += abs(record.amount_paid_paise)
            continue

        billed_amount = gross_value(record) - record.discount_paise
        mode = record.payment_mode

        billed[mode] += billed_amount
        collected[mode] += record.amount_paid_paise

        hour = parse_timestamp(record.timestamp).hour
        revenue_by_hour[hour] += billed_amount

        for item in record.line_items:
            medicine_quantity[item.drug_name] += item.qty
            medicine_revenue[item.drug_name] += (
                item.qty * item.unit_price_paise
            )

    total_billed = sum(billed.values())
    total_collected = sum(collected.values())
    total_refunds = sum(refunds.values())

    reconciliation = {
        mode: {
            "billed_paise": billed[mode],
            "collected_paise": collected[mode],
            "outstanding_paise": billed[mode] - collected[mode],
            "refunds_paise": refunds[mode],
        }
        for mode in PAYMENT_MODES
    }

    peak_hour = (
        max(revenue_by_hour, key=lambda hour: (revenue_by_hour[hour], -hour))
        if revenue_by_hour
        else None
    )

    return {
        "status": "partial" if rejected_rows else "complete",
        "processed_rows": processed_rows,
        "rejected_rows": rejected_rows,
        "reconciliation": reconciliation,
        "totals": {
            "billed_paise": total_billed,
            "collected_paise": total_collected,
            "outstanding_paise": total_billed - total_collected,
            "refunds_paise": total_refunds,
        },
        "analytics": {
            "revenue_by_hour": [
                {
                    "hour": hour,
                    "revenue_paise": revenue_by_hour[hour],
                }
                for hour in sorted(revenue_by_hour)
            ],
            "peak_hour": peak_hour,
            "top_medicines_by_quantity": [
                {
                    "drug_name": name,
                    "quantity": quantity,
                }
                for name, quantity in sorted(
                    medicine_quantity.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            ],
            "top_medicines_by_revenue": [
                {
                    "drug_name": name,
                    "revenue_paise": revenue,
                }
                for name, revenue in sorted(
                    medicine_revenue.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            ],
        },
    }
