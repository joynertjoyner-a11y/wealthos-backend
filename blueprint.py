from typing import Dict, Any, List

def generate_blueprint(profile: Dict[str, Any], parsed_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    income = float(profile.get("monthlyIncome", 0) or 0)

    fixed = round(income * 0.50, 2)
    variable = round(income * 0.25, 2)
    savings_target = round(income * 0.20, 2)
    net_cash_flow = round(income - fixed - variable - savings_target, 2)

    return {
        "monthlyBudget": {
            "income": income,
            "fixed": fixed,
            "variable": variable,
            "savingsTarget": savings_target,
            "netCashFlow": net_cash_flow,
        }
    }
