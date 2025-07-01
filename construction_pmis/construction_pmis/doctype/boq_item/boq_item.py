# Copyright (c) 2024, Jules and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BOQItem(Document):
    def validate(self):
        self.calculate_total_cost()

    def on_update(self):
        self.calculate_total_cost()

    def calculate_total_cost(self):
        if self.quantity and self.unit_rate:
            self.total_cost = float(self.quantity) * float(self.unit_rate)
        else:
            self.total_cost = 0

    # Potentially, methods for revision control could go here later
    # def revise_boq_item(self):
    #     # Logic to create a new version or update revision number
    #     pass

# It's good practice to also add a before_save hook that calls calculate_total_cost
# This can be done in hooks.py or directly here if preferred for self-contained logic.
# For now, validate and on_update should cover most cases.

# Example of autonaming by project and sequence (if not using item_code as name)
# def autoname(self):
#     if not self.item_code:
#         # Fallback or error if item_code is mandatory for naming
#         frappe.throw("Item Code is required to name the BOQ Item.")
#     self.name = f"{self.project}-BOQ-{self.item_code}"

# To make item_code unique per project, a custom validation would be needed:
# def validate_unique_item_code_per_project(self):
#     if self.is_new(): # Check only for new documents or if project/item_code changed
#         exists = frappe.db.exists("BOQ Item", {
#             "project": self.project,
#             "item_code": self.item_code,
#             "name": ["!=", self.name] # Exclude self if updating
#         })
#         if exists:
#             frappe.throw(f"BOQ Item with Code '{self.item_code}' already exists for Project '{self.project}'.")
#
# Call this in validate:
# self.validate_unique_item_code_per_project()
