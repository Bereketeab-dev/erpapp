# construction_pmis/custom_scripts/project.py
import frappe

def calculate_total_budget_server(doc, method):
    """
    Calculates the total budget amount from the project budget lines
    and sets it on the project document.
    Called on before_save for Project doctype.
    """
    total_budget = 0
    if doc.get("custom_project_budget_lines"):
        for line in doc.get("custom_project_budget_lines"):
            total_budget += flt(line.get("budget_amount"))

    doc.custom_total_budget_amount = total_budget
    # Note: No need to call doc.save() here as this is a before_save event.
    # The save operation will happen automatically after this hook.
    # Also, no need to refresh field as this is server-side.

def update_project_actual_costs(doc, method):
    """
    Placeholder for logic to update actual costs on the project budget lines.
    This would be triggered by transactions like Purchase Invoices, Stock Entries (for material),
    Timesheets (for labor), etc.
    """
    # This function will be more complex and will require identifying
    # relevant transactions linked to this project and its cost codes/categories.
    # For example, on submission of a Purchase Invoice linked to this project:
    # 1. Get the items from the Purchase Invoice.
    # 2. For each item, identify its cost category (e.g., Material).
    # 3. Find the corresponding Project Budget Line (matching project, category, and possibly cost code).
    # 4. Update the `actual_amount` on that budget line.
    # 5. Recalculate total actuals and variance on the Project doctype.
    pass
