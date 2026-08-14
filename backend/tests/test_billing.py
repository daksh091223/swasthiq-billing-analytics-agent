from billing_engine import build_eod_report

def make_record(
    visit_id="V1",
    payment_mode="cash",
    amount=100,
    discount=0,
    refund=False,
    hour=13,
):
    return {
        "clinic_id": "C1",
        "visit_id": visit_id,
        "timestamp": f"2026-07-27T{hour:02d}:20:00Z",
        "doctor_id": "D1",
        "line_items": [
            {
                "drug_name": "PARACETAMOL",
                "qty": 2,
                "unit_price_paise": 50,
            }
        ],
        "payment_mode": payment_mode,
        "amount_paid_paise": -50 if refund else amount,
        "discount_paise": discount,
        "is_refund": refund,
    }


def test_reconciliation():
    report = build_eod_report([make_record()])

    assert report["totals"] == {
        "billed_paise": 100,
        "collected_paise": 100,
        "outstanding_paise": 0,
        "refunds_paise": 0,
    }


def test_discount():
    report = build_eod_report([
        make_record(amount=90, discount=10)
    ])

    assert report["totals"]["billed_paise"] == 90
    assert report["totals"]["outstanding_paise"] == 0


def test_refund_is_separate():
    report = build_eod_report([
        make_record(refund=True)
    ])

    assert report["totals"]["billed_paise"] == 0
    assert report["totals"]["collected_paise"] == 0
    assert report["totals"]["outstanding_paise"] == 0
    assert report["totals"]["refunds_paise"] == 50


def test_payment_modes():
    rows = [
        make_record(payment_mode="cash", amount=100),
        make_record(
            visit_id="V2",
            payment_mode="card",
            amount=80,
        ),
        make_record(
            visit_id="V3",
            payment_mode="upi",
            amount=70,
        ),
    ]

    report = build_eod_report(rows)

    assert report["reconciliation"]["cash"]["billed_paise"] == 100
    assert report["reconciliation"]["card"]["billed_paise"] == 100
    assert report["reconciliation"]["upi"]["billed_paise"] == 100


def test_partial_rejection():
    bad = make_record(visit_id="BAD")
    del bad["payment_mode"]

    report = build_eod_report([
        make_record(amount=100),
        bad,
        make_record(visit_id="V3", amount=200),
    ])

    assert report["status"] == "partial"
    assert report["processed_rows"] == 2
    assert len(report["rejected_rows"]) == 1
    assert report["rejected_rows"][0]["row_number"] == 2
    assert report["rejected_rows"][0]["field"] == "payment_mode"
    assert report["totals"]["billed_paise"] == 200


def test_empty_input():
    report = build_eod_report([])

    assert report["status"] == "complete"
    assert report["processed_rows"] == 0
    assert report["rejected_rows"] == []
    assert report["totals"]["billed_paise"] == 0
    assert report["analytics"]["peak_hour"] is None


def test_hourly_revenue_and_peak():
    report = build_eod_report([
        make_record(amount=100, hour=10),
        make_record(visit_id="V2", amount=200, hour=13),
    ])

    assert report["analytics"]["peak_hour"] == 13
    assert report["analytics"]["revenue_by_hour"] == [
        {"hour": 10, "revenue_paise": 100},
        {"hour": 13, "revenue_paise": 200},
    ]


def test_medicine_rankings():
    row = make_record()
    row["line_items"] = [
        {
            "drug_name": "A",
            "qty": 3,
            "unit_price_paise": 100,
        },
        {
            "drug_name": "B",
            "qty": 10,
            "unit_price_paise": 20,
        },
    ]
    row["amount_paid_paise"] = 500

    report = build_eod_report([row])

    assert report["analytics"]["top_medicines_by_quantity"][0] == {
        "drug_name": "B",
        "quantity": 10,
    }

    assert report["analytics"]["top_medicines_by_revenue"][0] == {
        "drug_name": "A",
        "revenue_paise": 300,
    }


def test_refunds_excluded_from_sales_analytics():
    report = build_eod_report([
        make_record(amount=100),
        make_record(
            visit_id="R1",
            refund=True,
            hour=18,
        ),
    ])

    assert report["totals"]["billed_paise"] == 100
    assert report["totals"]["refunds_paise"] == 50
    assert report["analytics"]["revenue_by_hour"] == [
        {"hour": 13, "revenue_paise": 100}
    ]


def test_invalid_timestamp_is_rejected():
    row = make_record()
    row["timestamp"] = "not-a-timestamp"

    report = build_eod_report([row])

    assert report["status"] == "partial"
    assert report["rejected_rows"][0]["field"] == "timestamp"


def test_business_rule_violation_is_rejected():
    row = make_record(amount=150)

    report = build_eod_report([row])

    assert report["status"] == "partial"
    assert report["processed_rows"] == 0
    assert len(report["rejected_rows"]) == 1


def test_reconciliation_invariant():
    report = build_eod_report([
        make_record(amount=90, discount=10),
        make_record(visit_id="V2", payment_mode="upi", amount=100),
    ])

    totals = report["totals"]

    assert totals["outstanding_paise"] == (
        totals["billed_paise"] - totals["collected_paise"]
    )

    hourly_total = sum(
        item["revenue_paise"]
        for item in report["analytics"]["revenue_by_hour"]
    )

    assert hourly_total == totals["billed_paise"]