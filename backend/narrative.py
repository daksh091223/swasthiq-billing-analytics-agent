
import os
import re
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

TOKEN_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")


class NarrativeSection(BaseModel):
    heading: str
    text: str
    figure_ids: list[str] = Field(default_factory=list)


class NarrativeResponse(BaseModel):
    title: str
    sections: list[NarrativeSection]


FIGURES = {
    "total_billed": {
        "label": "Total billed",
        "path": "totals.billed_paise",
    },
    "total_collected": {
        "label": "Total collected",
        "path": "totals.collected_paise",
    },
    "outstanding": {
        "label": "Outstanding",
        "path": "totals.outstanding_paise",
    },
    "refunds": {
        "label": "Refunds",
        "path": "totals.refunds_paise",
    },
    "peak_hour": {
        "label": "Peak hour",
        "path": "analytics.peak_hour",
    },
    "processed_rows": {
        "label": "Processed rows",
        "path": "processed_rows",
    },
    "rejected_rows": {
        "label": "Rejected rows",
        "path": "rejected_rows",
    },
}


SYSTEM_PROMPT = """
You write a short end-of-day billing narrative from a deterministic report.

The report is the only source of truth.

Rules:
- Never calculate, modify, estimate, or invent financial numbers.
- Never introduce a number that is not represented by a figure token.
- When mentioning a report figure, use its exact token, such as {total_billed}.
- You may make simple qualitative observations only when directly supported by the report.
- Do not mention information outside the supplied report.
- Do not mention raw billing rows.
- Do not give recommendations unless they are directly framed as a data-quality observation.
- Keep the narrative concise and useful to a clinic operator.
- Use at most 3 sections.
- Do not put literal numeric values in the narrative text. Use figure tokens instead.
- Every figure token used must appear in figure_ids for that section.
- Available figure tokens:
  {total_billed}, {total_collected}, {outstanding}, {refunds},
  {peak_hour}, {processed_rows}, {rejected_rows}.
"""


def _report_for_prompt(report: dict) -> str:
    # Only expose deterministic report data. The model does not receive raw rows.
    return str({
        "status": report["status"],
        "processed_rows": report["processed_rows"],
        "rejected_rows": report["rejected_rows"],
        "totals": report["totals"],
        "analytics": {
            "peak_hour": report["analytics"]["peak_hour"],
            "revenue_by_hour": report["analytics"]["revenue_by_hour"],
            "top_medicines_by_quantity": report["analytics"]["top_medicines_by_quantity"][:5],
            "top_medicines_by_revenue": report["analytics"]["top_medicines_by_revenue"][:5],
        },
    })


def _get_figure_value(report: dict, figure_id: str):
    if figure_id == "rejected_rows":
        return len(report["rejected_rows"])

    value = report
    for key in FIGURES[figure_id]["path"].split("."):
        value = value[key]

    return value


def _format_figure(report: dict, figure_id: str) -> str:
    value = _get_figure_value(report, figure_id)

    if figure_id == "peak_hour":
        return "—" if value is None else f"{value:02d}:00 UTC"

    if figure_id in {"processed_rows", "rejected_rows"}:
        return str(value)

    return f"₹{value / 100:,.2f}"


def validate_narrative(narrative: NarrativeResponse, report: dict):
    allowed = set(FIGURES)

    for section in narrative.sections:
        token_ids = set(TOKEN_RE.findall(section.text))

        if not token_ids.issubset(allowed):
            unknown = token_ids - allowed
            raise ValueError(f"Unknown figure token(s): {', '.join(sorted(unknown))}")

        if not token_ids.issubset(set(section.figure_ids)):
            raise ValueError("Every figure token must be listed in figure_ids")

        for figure_id in section.figure_ids:
            if figure_id not in allowed:
                raise ValueError(f"Unknown figure id: {figure_id}")

        # Numeric literals are not allowed in model-authored narrative text.
        # This prevents the model from sneaking in an untraced number.
        if re.search(r"\b\d+(?:[.,]\d+)*\b", section.text):
            raise ValueError("Narrative contains an untraced numeric literal")

    return narrative


def render_narrative(narrative: NarrativeResponse, report: dict) -> NarrativeResponse:
    sections = []

    for section in narrative.sections:
        text = section.text
        for figure_id in section.figure_ids:
            text = text.replace(
                "{" + figure_id + "}",
                _format_figure(report, figure_id),
            )

        sections.append(
            NarrativeSection(
                heading=section.heading,
                text=text,
                figure_ids=section.figure_ids,
            )
        )

    return NarrativeResponse(title=narrative.title, sections=sections)


def trace_figures(narrative: NarrativeResponse, report: dict) -> list[dict]:
    used = []
    seen = set()

    for section in narrative.sections:
        for figure_id in section.figure_ids:
            if figure_id in seen:
                continue

            seen.add(figure_id)
            used.append({
                "id": figure_id,
                "label": FIGURES[figure_id]["label"],
                "source": FIGURES[figure_id]["path"],
                "value": _format_figure(report, figure_id),
            })

    return used


def generate_narrative(report: dict) -> dict:
    api_key = os.getenv("HF_TOKEN")

    if not api_key:
        raise RuntimeError("HF_TOKEN is not configured")

    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=api_key
    )
    model = os.getenv("OPENAI_MODEL", "openai/gpt-oss-120b:groq")

    response = client.responses.parse(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=_report_for_prompt(report),
        text_format=NarrativeResponse,
    )

    if not response.output_text:
        raise RuntimeError("LLM returned an empty narrative")

    parsed = None
    for output in response.output:
        if output.type != "message":
            continue

        for item in output.content:
            if item.type == "output_text" and item.parsed:
                parsed = item.parsed
                break

        if parsed:
            break

    if parsed is None:
        raise RuntimeError("LLM response could not be parsed")

    validate_narrative(parsed, report)
    rendered = render_narrative(parsed, report)

    return {
        "title": rendered.title,
        "sections": [
            section.model_dump()
            for section in rendered.sections
        ],
        "traced_figures": trace_figures(rendered, report),
        "model": model,
    }
