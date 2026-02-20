from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, conlist

class BudgetLineItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    amount: float = Field(..., ge=0)

class BudgetRequest(BaseModel):
    monthly_after_tax_income: float = Field(..., ge=0)

    fixed_expenses: List[BudgetLineItem] = Field(default_factory=list)
    variable_expenses: List[BudgetLineItem] = Field(default_factory=list)

    # Optional strategy knobs
    target_needs_pct: float = Field(default=0.50, ge=0, le=1)
    target_wants_pct: float = Field(default=0.30, ge=0, le=1)
    target_savings_pct: float = Field(default=0.20, ge=0, le=1)

    # Optional goals (monthly amounts)
    emergency_fund_goal: float = Field(default=0, ge=0)
    debt_extra_payment_goal: float = Field(default=0, ge=0)
    investing_goal: float = Field(default=0, ge=0)

def _sum_items(items: List[BudgetLineItem]) -> float:
    return round(sum(i.amount for i in items), 2)

def _top_items(items: List[BudgetLineItem], n: int = 5) -> List[Dict[str, Any]]:
    sorted_items = sorted(items, key=lambda x: x.amount, reverse=True)
    return [{"name": i.name, "amount": round(i.amount, 2)} for i in sorted_items[:n]]

def compute_budget(req: BudgetRequest) -> Dict[str, Any]:
    income = round(req.monthly_after_tax_income, 2)

    fixed_total = _sum_items(req.fixed_expenses)
    variable_total = _sum_items(req.variable_expenses)
    total_spend = round(fixed_total + variable_total, 2)

    net_cash_flow = round(income - total_spend, 2)

    # Targets (classic 50/30/20, adjustable)
    needs_target = round(income * req.target_needs_pct, 2)
    wants_target = round(income * req.target_wants_pct, 2)
    savings_target = round(income * req.target_savings_pct, 2)

    # Simple classification assumption:
    # - fixed_expenses = "needs"
    # - variable_expenses = "wants/variable" (some are needs, but MVP keeps it simple)
    needs_actual = fixed_total
    wants_actual = variable_total
    savings_actual = max(0.0, net_cash_flow)

    # Guidance logic
    recommendations: List[Dict[str, Any]] = []

    if req.target_needs_pct + req.target_wants_pct + req.target_savings_pct != 1:
        recommendations.append({
            "type": "warning",
            "message": "Your target percentages do not add up to 100%. Consider using 0.50 / 0.30 / 0.20."
        })

    # Needs/Wants comparisons
    if needs_actual > needs_target:
        recommendations.append({
            "type": "needs_over_target",
            "message": f"Fixed expenses are above target by ${round(needs_actual - needs_target, 2)}.",
            "next_steps": [
                "Review housing, utilities, insurance, debt payments for refinancing or reductions.",
                "Check subscriptions that are billed as 'fixed' (phone, streaming, memberships)."
            ]
        })

    if wants_actual > wants_target:
        recommendations.append({
            "type": "wants_over_target",
            "message": f"Variable spending is above target by ${round(wants_actual - wants_target, 2)}.",
            "next_steps": [
                "Cap discretionary categories (dining out, shopping, entertainment).",
                "Set weekly limits and turn on spending alerts."
            ],
            "top_variable_items": _top_items(req.variable_expenses, n=5)
        })

    # Cash flow recommendations
    if net_cash_flow < 0:
        deficit = abs(net_cash_flow)
        recommendations.append({
            "type": "deficit",
            "message": f"You are short by ${round(deficit, 2)} per month.",
            "next_steps": [
                "Cut variable expenses first (subscriptions, dining, discretionary).",
                "Then renegotiate fixed bills (insurance, phone/internet) or refinance high-interest debt.",
                "If still short, consider increasing income (overtime, side income)."
            ],
            "quick_math": {
                "needed_cut_per_week": round(deficit / 4.33, 2)
            }
        })
    else:
        recommendations.append({
            "type": "surplus",
            "message": f"You have ${net_cash_flow} left after expenses.",
            "next_steps": [
                "Automate transfers on payday: emergency fund → debt → investing (in that order, generally).",
                "Keep a small buffer in checking to prevent overdrafts."
            ]
        })

    # Goal allocation suggestion (if surplus exists)
    allocation_plan: Dict[str, Any] = {"emergency": 0, "debt_extra": 0, "investing": 0, "remaining_buffer": 0}
    if net_cash_flow > 0:
        remaining = net_cash_flow

        # Priority: emergency fund, then debt extra, then investing (MVP default order)
        em = min(req.emergency_fund_goal, remaining)
        remaining = round(remaining - em, 2)

        debt = min(req.debt_extra_payment_goal, remaining)
        remaining = round(remaining - debt, 2)

        inv = min(req.investing_goal, remaining)
        remaining = round(remaining - inv, 2)

        allocation_plan = {
            "emergency": round(em, 2),
            "debt_extra": round(debt, 2),
            "investing": round(inv, 2),
            "remaining_buffer": round(remaining, 2),
        }

    return {
        "income": income,
        "totals": {
            "fixed_total": fixed_total,
            "variable_total": variable_total,
            "total_spend": total_spend,
        },
        "net_cash_flow": net_cash_flow,
        "targets": {
            "needs_target": needs_target,
            "wants_target": wants_target,
            "savings_target": savings_target,
            "target_pcts": {
                "needs": req.target_needs_pct,
                "wants": req.target_wants_pct,
                "savings": req.target_savings_pct,
            }
        },
        "actuals": {
            "needs_actual": round(needs_actual, 2),
            "wants_actual": round(wants_actual, 2),
            "savings_actual": round(savings_actual, 2),
        },
        "allocation_plan": allocation_plan,
        "recommendations": recommendations,
        "disclaimer": "Educational output only; not financial, tax, or legal advice."
    }
