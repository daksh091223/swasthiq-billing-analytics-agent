from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

PaymentMode = Literal["cash", "card", "upi"]
class LineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drug_name: str = Field(min_length=1)
    qty: int = Field(gt=0)
    unit_price_paise: int = Field(ge=0)

class BillingRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clinic_id: str = Field(min_length=1)
    visit_id: str = Field(min_length=1)
    timestamp: str = Field(min_length=1)
    doctor_id: str = Field(min_length=1)
    line_items: list[LineItem] = Field(min_length=1)
    payment_mode: PaymentMode
    amount_paid_paise: int
    discount_paise: int = Field(ge=0)
    is_refund: bool
