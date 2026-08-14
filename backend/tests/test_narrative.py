import pytest

from narrative import NarrativeResponse, NarrativeSection, render_narrative, trace_figures, validate_narrative


def report():
    return {
        "status": "partial",
        "processed_rows": 18,
        "rejected_rows": [{"row_number": 19}],
        "totals": {
            "billed_paise": 319000,
            "collected_paise": 317200,
            "outstanding_paise": 1800,
            "refunds_paise": 0,
        },
        "analytics": {
            "peak_hour": 13,
            "revenue_by_hour": [],
            "top_medicines_by_quantity": [
                {"drug_name": "PARACETAMOL", "quantity": 142},
                {"drug_name": "AMOXICILLIN", "quantity": 88},
            ],
            "top_medicines_by_revenue": [
                {"drug_name": "ATORVASTATIN", "revenue_paise": 648000},
                {"drug_name": "AMOXICILLIN", "revenue_paise": 594000},
            ],
        },
    }


def test_narrative_tokens_are_rendered_from_report():
    narrative = NarrativeResponse(
        title="EOD Summary",
        sections=[
            NarrativeSection(
                heading="Financial position",
                text="The clinic billed {total_billed} and collected {total_collected}.",
                figure_ids=["total_billed", "total_collected"],
            )
        ],
    )

    validate_narrative(narrative, report())
    rendered = render_narrative(narrative, report())

    assert rendered.sections[0].text == (
        "The clinic billed ₹3,190.00 and collected ₹3,172.00."
    )


def test_untraced_number_is_rejected():
    narrative = NarrativeResponse(
        title="Bad",
        sections=[
            NarrativeSection(
                heading="Summary",
                text="The clinic billed 3190 today.",
                figure_ids=[],
            )
        ],
    )

    with pytest.raises(ValueError):
        validate_narrative(narrative, report())


def test_missing_figure_trace_is_normalized_server_side():
    narrative = NarrativeResponse(
        title="Summary",
        sections=[
            NarrativeSection(
                heading="Summary",
                text="The clinic billed {total_billed}.",
                figure_ids=[],
            )
        ],
    )

    validate_narrative(narrative, report())

    assert narrative.sections[0].figure_ids == ["total_billed"]


def test_trace_figures_points_to_deterministic_fields():
    narrative = NarrativeResponse(
        title="Summary",
        sections=[
            NarrativeSection(
                heading="Summary",
                text="Outstanding was {outstanding}.",
                figure_ids=["outstanding"],
            )
        ],
    )

    rendered = render_narrative(narrative, report())
    traces = trace_figures(rendered, report())

    assert traces == [{
        "id": "outstanding",
        "label": "Outstanding",
        "source": "totals.outstanding_paise",
        "value": "₹18.00",
    }]


def test_medicine_figures_render_and_trace():
    narrative = NarrativeResponse(
        title="Summary",
        sections=[
            NarrativeSection(
                heading="Medicine movers",
                text="Top by quantity: {top_medicine_quantity}. Top by revenue: {top_medicine_revenue}.",
                figure_ids=["top_medicine_quantity", "top_medicine_revenue"],
            )
        ],
    )

    validate_narrative(narrative, report())
    rendered = render_narrative(narrative, report())
    traces = trace_figures(rendered, report())

    assert rendered.sections[0].text == (
        "Top by quantity: PARACETAMOL (142 units). "
        "Top by revenue: ATORVASTATIN (₹6,480.00)."
    )

    assert traces == [
        {
            "id": "top_medicine_quantity",
            "label": "Top medicine by quantity",
            "source": "analytics.top_medicines_by_quantity[0]",
            "value": "PARACETAMOL (142 units)",
        },
        {
            "id": "top_medicine_revenue",
            "label": "Top medicine by revenue",
            "source": "analytics.top_medicines_by_revenue[0]",
            "value": "ATORVASTATIN (₹6,480.00)",
        },
    ]
