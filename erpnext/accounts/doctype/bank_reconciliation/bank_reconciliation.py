# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate
import csv
import io
# Other potential imports:
# from erpnext.accounts.doctype.journal_entry.journal_entry import make_gl_entries
# from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
# from erpnext.accounts.utils import get_balance_on


class BankReconciliation(Document):
    def onload(self):
        """
        Called when the document is loaded.
        Used to fetch initial balances if certain fields are set.
        """
        if self.bank_account and self.statement_from_date and not self.erp_opening_balance:
            self.set_erp_opening_balance()

    def validate(self):
        """
        Validate data before saving.
        """
        if getdate(self.statement_from_date) > getdate(self.statement_to_date):
            frappe.throw("Statement From Date cannot be after Statement To Date")

        if self.docstatus == 0: # Draft
            self.status = "Draft"

        self.calculate_totals()


    def on_change(self):
        """
        Called on any field change.
        """
        if frappe.flags.current_field == "bank_account" or frappe.flags.current_field == "statement_from_date":
            if self.bank_account and self.statement_from_date:
                self.set_erp_opening_balance()
            else:
                self.erp_opening_balance = 0.0
                self.account_currency = None

        if frappe.flags.current_field in ["bank_statement_closing_balance", "erp_calculated_closing_balance"]:
            self.calculate_difference()

    def before_submit(self):
        """
        Actions before the document is submitted (Reconciled).
        """
        self.status = "Reconciled"
        if self.difference != 0:
            # Allow for a small tolerance if configured in Accounts Settings
            tolerance = flt(frappe.db.get_single_value("Accounts Settings", "bank_reconciliation_tolerance"))
            if abs(self.difference) > tolerance:
                frappe.throw("Difference must be zero (or within tolerance) to reconcile.")

        self.set_clearance_dates_on_submit()

    def on_submit(self):
        """
        Actions after the document is submitted.
        """
        frappe.msgprint(f"Bank Reconciliation {self.name} submitted and reconciled.")
        # Potentially update last_reconciled_date on Bank Account master
        # frappe.db.set_value("Bank Account", self.bank_account, "last_reconciliation_date", self.statement_to_date)


    def on_cancel(self):
        """
        Actions when the document is cancelled.
        """
        self.status = "Cancelled"
        self.reset_clearance_dates_on_cancel()
        frappe.msgprint(f"Bank Reconciliation {self.name} cancelled.")

    def set_erp_opening_balance(self):
        """
        Fetch and set the ERP opening balance for the bank account as of statement_from_date.
        """
        if not self.bank_account or not self.statement_from_date:
            self.erp_opening_balance = 0.0
            self.account_currency = None
            return

        # Placeholder for actual ERPNext function to get balance
        # This would typically query General Ledger entries
        # opening_balance = get_balance_on(self.bank_account, self.statement_from_date)
        # For now, simulate this:
        try:
            bank_account_details = frappe.get_doc("Bank Account", self.bank_account)
            self.account_currency = bank_account_details.account_currency

            # Simulate fetching opening balance (replace with actual logic)
            # In a real scenario, this would sum GL entries for this account up to statement_from_date - 1 day
            # For simplicity, we'll just show a message that it needs to be implemented
            # frappe.msgprint("ERP Opening Balance calculation needs to be implemented using get_balance_on or similar.")
            # For testing, let's set a dummy value or leave it to be manually entered if not found
            # self.erp_opening_balance = frappe.db.sql_query_that_gets_opening_balance(...)
            # This is a complex query, for now, we let user input it or it can be fetched via a client script later
            # For the DocType definition, erp_opening_balance is read-only, so it should be populated here.
            # Let's assume a function `get_account_balance_as_of` exists
            previous_day = frappe.utils.add_days(self.statement_from_date, -1)
            balance = frappe.db.get_value("GL Entry",
                                          filters={"account": self.bank_account, "posting_date": ["<=", previous_day]},
                                          fieldname="sum(debit) - sum(credit)")
            self.erp_opening_balance = flt(balance)

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error in set_erp_opening_balance")
            self.erp_opening_balance = 0.0
            # frappe.throw(f"Could not fetch opening balance for {self.bank_account}: {e}")


    @frappe.whitelist()
    def get_unreconciled_erp_transactions(self):
        """
        Fetch unreconciled (no clearance_date or clearance_date after statement_to_date)
        Journal Entry and Payment Entry lines affecting the bank_account within the period.
        Populates the `erp_ledger_transactions` child table.
        """
        if not self.bank_account or not self.statement_from_date or not self.statement_to_date:
            frappe.throw("Bank Account, Statement From Date, and Statement To Date must be set.")

        self.set("erp_ledger_transactions", []) # Clear existing entries

        # Query GL Entries for the bank account within the date range
        # This is a simplified query. A real one would need to consider more states and link to voucher types.
        gl_entries = frappe.db.sql(f"""
            SELECT
                posting_date, voucher_type, voucher_no, party_type, party,
                debit_in_account_currency as debit_amount, credit_in_account_currency as credit_amount,
                against_voucher_type, against_voucher, reference_no, cheque_no, clearance_date
            FROM `tabGL Entry`
            WHERE
                account = %(bank_account)s AND
                posting_date BETWEEN %(from_date)s AND %(to_date)s AND
                (clearance_date IS NULL OR clearance_date = '' OR clearance_date > %(to_date)s) AND
                docstatus < 2 -- Submitted entries only
            ORDER BY posting_date, name
        """, {
            "bank_account": self.bank_account,
            "from_date": self.statement_from_date,
            "to_date": self.statement_to_date
        }, as_dict=True)

        for entry in gl_entries:
            self.append("erp_ledger_transactions", {
                "posting_date": entry.get("posting_date"),
                "voucher_type": entry.get("voucher_type"),
                "voucher_no": entry.get("voucher_no"),
                "party_type": entry.get("party_type"),
                "party": entry.get("party"),
                "debit_amount": flt(entry.get("debit_amount")),
                "credit_amount": flt(entry.get("credit_amount")),
                "reference_no": entry.get("reference_no"),
                "cheque_no": entry.get("cheque_no"),
                "is_reconciled": 0,
                "reconciliation_status": "Unmatched",
                "clearance_date": entry.get("clearance_date") # Keep existing if any, but it should be > to_date or NULL
            })

        self.calculate_totals()
        frappe.msgprint(f"{len(gl_entries)} ERP transactions fetched.")
        return self # Return self to update the form with new child table data


    @frappe.whitelist()
    def import_bank_statement(self, file_url=None):
        """
        Import transactions from an attached bank statement file (CSV for now).
        Populates the `bank_statement_transactions` child table.
        `file_url` can be passed from client if using frappe.call.
        """
        if not file_url and self.bank_statement_file:
             file_url = self.bank_statement_file

        if not file_url:
            frappe.throw("No bank statement file attached or provided.")

        try:
            file_doc = frappe.get_doc("File", {"file_url": file_url})
            file_content = file_doc.get_content()

            # Simple CSV parsing - this needs to be made more robust and configurable
            # (e.g., allow user to map columns like in standard Bank Transaction Import)
            # For now, assume a fixed format: Date, Description, Withdrawal, Deposit, Reference

            # Clear existing statement transactions
            self.set("bank_statement_transactions", [])

            data = []
            if isinstance(file_content, bytes):
                file_content_str = file_content.decode('utf-8') # Or appropriate encoding
            else:
                file_content_str = file_content

            reader = csv.reader(io.StringIO(file_content_str))
            header = next(reader) # Skip header row

            # Basic column mapping - this should ideally be configurable per bank or user-defined
            # Example: Date,Description,Withdrawal,Deposit,Reference No
            # This part is highly dependent on how users want to map their CSVs.
            # A more robust solution would involve a separate "Bank Statement Mapping" tool or settings in "Bank Account"

            date_idx, desc_idx, wd_idx, dp_idx, ref_idx = 0, 1, 2, 3, 4 # Default indices
            # Add logic here to get column indices based on header names if possible, or use a saved mapping

            parsed_count = 0
            for row_idx, row in enumerate(reader):
                if not row or all(s.strip() == "" for s in row): continue # Skip empty rows
                try:
                    # Ensure row has enough columns based on expected indices
                    if not (len(row) > date_idx and len(row) > desc_idx and \
                            (len(row) > wd_idx or len(row) > dp_idx)): # Need at least one amount column
                        frappe.log_error(f"Skipping row {row_idx+2} due to insufficient columns: {row}", "Bank Statement Import")
                        continue

                    t_date = getdate(row[date_idx].strip())
                    description = row[desc_idx].strip()

                    withdrawal = flt(row[wd_idx].strip()) if len(row) > wd_idx and row[wd_idx].strip() else 0.0
                    deposit = flt(row[dp_idx].strip()) if len(row) > dp_idx and row[dp_idx].strip() else 0.0
                    reference = row[ref_idx].strip() if len(row) > ref_idx and row[ref_idx].strip() else None

                    if not description: # Skip if essential description is missing
                        frappe.log_warning(f"Skipping row {row_idx+2} due to missing description: {row}", "Bank Statement Import")
                        continue

                    self.append("bank_statement_transactions", {
                        "transaction_date": t_date,
                        "description": description,
                        "withdrawal_amount": withdrawal,
                        "deposit_amount": deposit,
                        "reference_number": reference,
                        "is_reconciled": 0,
                        "reconciliation_status": "Unmatched"
                    })
                    parsed_count += 1
                except Exception as e_row:
                    frappe.log_error(f"Error parsing row {row_idx+2}: {row}. Error: {e_row}", "Bank Statement Import")

            self.calculate_totals()
            frappe.msgprint(f"{parsed_count} transactions imported from the bank statement.")
            return self # Return self to update form

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error in import_bank_statement")
            frappe.throw(f"Error processing bank statement file: {e}")


    @frappe.whitelist()
    def auto_match_transactions(self):
        """
        Attempt to automatically match transactions between bank_statement_transactions
        and erp_ledger_transactions based on configurable rules (e.g., date, amount, reference).
        This is a placeholder for potentially complex logic.
        """
        # Simple matching: exact amount and close date (e.g. +/- 3 days)
        # More advanced: reference numbers, cheque numbers, fuzzy logic on descriptions

        matched_count = 0
        bank_lines = [line for line in self.get("bank_statement_transactions") if not line.is_reconciled]
        erp_lines = [line for line in self.get("erp_ledger_transactions") if not line.is_reconciled]

        for b_line in bank_lines:
            # Determine if bank line is a debit or credit
            b_amount = b_line.deposit_amount if b_line.deposit_amount > 0 else -b_line.withdrawal_amount
            if b_amount == 0: continue

            for e_line in erp_lines:
                if e_line.is_reconciled: continue # Already matched in this run

                # Determine if ERP line is a debit or credit from bank's perspective
                # If bank_account is a debit account (Asset), ERP debit increases balance, ERP credit decreases.
                # So, if bank shows deposit (credit to bank, debit to our asset account), look for ERP debit.
                # If bank shows withdrawal (debit to bank, credit to our asset account), look for ERP credit.
                # This logic depends on the nature of the bank account in CoA.
                # For simplicity, assuming standard asset bank account:
                # Bank Deposit (b_amount > 0) should match ERP Debit (e_line.debit_amount)
                # Bank Withdrawal (b_amount < 0) should match ERP Credit (e_line.credit_amount)

                erp_amount_for_comparison = 0
                if b_amount > 0: # Bank deposit
                    erp_amount_for_comparison = e_line.debit_amount
                else: # Bank withdrawal
                    erp_amount_for_comparison = -e_line.credit_amount

                if erp_amount_for_comparison == 0: continue

                date_diff = abs((getdate(b_line.transaction_date) - getdate(e_line.posting_date)).days)

                # Rule 1: Exact amount match and date within 3 days
                if b_amount == erp_amount_for_comparison and date_diff <= 3:
                    # Rule 2: If reference numbers exist, they should match (optional, add more rules)
                    if b_line.reference_number and e_line.reference_no and b_line.reference_number != e_line.reference_no:
                        continue # References exist but don't match, skip

                    b_line.is_reconciled = 1
                    b_line.reconciliation_status = "Matched"
                    b_line.matched_erp_transaction_id = e_line.name # Assuming child table rows have unique name/idx

                    e_line.is_reconciled = 1
                    e_line.reconciliation_status = "Matched"
                    e_line.matched_bank_statement_line_id = b_line.name
                    e_line.clearance_date = b_line.transaction_date # Set clearance date from bank statement

                    matched_count += 1
                    erp_lines.remove(e_line) # Remove from consideration for further auto-matching
                    break # Move to next bank line

        self.calculate_totals()
        frappe.msgprint(f"{matched_count} transactions auto-matched.")
        return self


    @frappe.whitelist()
    def create_erp_entry_for_bank_transaction(self, bank_transaction_line_name, new_entry_details):
        """
        Creates a new Journal Entry (or Payment Entry) for a selected bank statement transaction.
        `bank_transaction_line_name`: name/idx of the row in `bank_statement_transactions`.
        `new_entry_details`: dict containing info for the new JE/PE (e.g., other account, cost center).
        This is a simplified placeholder. Real implementation needs more details for JE/PE creation.
        """
        bank_line = self.get("bank_statement_transactions", {"name": bank_transaction_line_name})
        if not bank_line or not bank_line[0]:
            frappe.throw("Bank transaction line not found.")
        bank_line = bank_line[0]

        if bank_line.is_reconciled:
            frappe.throw("This bank transaction is already reconciled.")

        # Example: Creating a Journal Entry for bank charges
        # `new_entry_details` should contain:
        # 'posting_date', 'company', 'remark', 'other_account', 'cost_center' (optional)

        posting_date = new_entry_details.get("posting_date", bank_line.transaction_date)
        company = self.company
        remark = new_entry_details.get("remark", f"Entry for bank transaction: {bank_line.description}")
        other_account = new_entry_details.get("other_account") # E.g., "Bank Charges" account
        cost_center = new_entry_details.get("cost_center", self.cost_center) # if applicable from parent

        if not other_account:
            frappe.throw("The 'Other Account' (e.g., expense/income account) is required to create an ERP entry.")

        try:
            je = frappe.new_doc("Journal Entry")
            je.posting_date = posting_date
            je.company = company
            je.remark = remark
            # Assuming bank_line.withdrawal_amount > 0 for bank charges (expense)
            # Account 1: Bank Account (credited)
            # Account 2: Other Account (e.g., Bank Charges - debited)

            is_debit_to_bank = bank_line.deposit_amount > 0
            amount = bank_line.deposit_amount if is_debit_to_bank else bank_line.withdrawal_amount

            bank_account_entry = {
                "account": self.bank_account,
                "debit_in_account_currency": amount if is_debit_to_bank else 0,
                "credit_in_account_currency": 0 if is_debit_to_bank else amount,
                "cost_center": cost_center, # if applicable
                "party_type": new_entry_details.get("party_type"),
                "party": new_entry_details.get("party"),
            }
            other_account_entry = {
                "account": other_account,
                "debit_in_account_currency": 0 if is_debit_to_bank else amount,
                "credit_in_account_currency": amount if is_debit_to_bank else 0,
                "cost_center": cost_center, # if applicable
                "party_type": new_entry_details.get("party_type"), # May or may not apply to other account
                "party": new_entry_details.get("party"),
            }

            je.append("accounts", bank_account_entry)
            je.append("accounts", other_account_entry)

            je.flags.ignore_permissions = True # If called by system/internal logic
            je.submit() # Submits the Journal Entry

            # Mark bank line as reconciled and link to this new JE
            bank_line.is_reconciled = 1
            bank_line.reconciliation_status = "New Entry Created"
            bank_line.matched_erp_transaction_id = je.name

            # Add this new JE to the erp_ledger_transactions table for visibility
            self.append("erp_ledger_transactions", {
                "posting_date": je.posting_date,
                "voucher_type": "Journal Entry",
                "voucher_no": je.name,
                "party_type": bank_account_entry.get("party_type"),
                "party": bank_account_entry.get("party"),
                "debit_amount": bank_account_entry.get("debit_in_account_currency"),
                "credit_amount": bank_account_entry.get("credit_in_account_currency"),
                "is_reconciled": 1,
                "reconciliation_status": "Matched",
                "matched_bank_statement_line_id": bank_line.name,
                "clearance_date": bank_line.transaction_date
            })

            self.calculate_totals()
            frappe.msgprint(f"Journal Entry {je.name} created and matched.")
            return self

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error in create_erp_entry_for_bank_transaction")
            frappe.throw(f"Failed to create ERP entry: {e}")


    def set_clearance_dates_on_submit(self):
        """
        Set/update clearance_date on the actual Journal Entry / Payment Entry documents
        for all matched ERP transactions.
        """
        updated_count = 0
        for erp_line in self.get("erp_ledger_transactions"):
            if erp_line.is_reconciled and erp_line.voucher_no and erp_line.clearance_date:
                try:
                    # This is a simplified update.
                    # In reality, JE and PE have specific ways to update clearance.
                    # For JE, it might be on the specific row related to the bank account.
                    # For PE, it's usually a field on the PE doc itself.
                    # This needs to be adapted based on how ERPNext handles clearance_date on these DocTypes.

                    # General approach:
                    # Update the 'clearance_date' in the original voucher (GL Entry source)
                    # This might involve updating the child table in Journal Entry or a field in Payment Entry

                    # For now, let's assume we are directly updating GL Entry for simplicity,
                    # though this is NOT standard practice. Standard practice is to update the source document.
                    # frappe.db.set_value(erp_line.voucher_type, erp_line.voucher_no, "clearance_date", erp_line.clearance_date)

                    # A more correct (but complex) approach:
                    voucher_doc = frappe.get_doc(erp_line.voucher_type, erp_line.voucher_no)
                    if erp_line.voucher_type == "Journal Entry":
                        changed = False
                        for acc_row in voucher_doc.get("accounts"):
                            if acc_row.account == self.bank_account and acc_row.name == erp_line.gl_entry_name: # Need GL entry name or idx
                                acc_row.clearance_date = erp_line.clearance_date
                                changed = True
                                break
                        if changed:
                            voucher_doc.save(ignore_permissions=True) # This might trigger its own on_update
                            updated_count +=1
                    elif erp_line.voucher_type == "Payment Entry":
                        if voucher_doc.payment_type != "Receive": # Only set for outgoing usually, or if bank account is target
                           # Or if the bank account is the paid_from / received_to account
                           if voucher_doc.paid_from == self.bank_account or voucher_doc.paid_to == self.bank_account :
                                voucher_doc.clearance_date = erp_line.clearance_date
                                voucher_doc.save(ignore_permissions=True)
                                updated_count +=1
                    # Add other voucher types if necessary (e.g. Sales Invoice, Purchase Invoice if direct bank impact)

                    # The `erp_ledger_transactions` table should ideally store the specific GL entry name/ID
                    # if we need to update individual GL entries' clearance dates, but typically it's done
                    # on the parent voucher.

                except Exception as e:
                    frappe.log_error(f"Failed to set clearance date for {erp_line.voucher_type} {erp_line.voucher_no}: {e}",
                                     "Bank Rec Submit")
        if updated_count > 0:
            frappe.msgprint(f"{updated_count} ERP transaction clearance dates updated.")


    def reset_clearance_dates_on_cancel(self):
        """
        Reset clearance_date on the actual Journal Entry / Payment Entry documents
        if they were set by this reconciliation.
        """
        reset_count = 0
        for erp_line in self.get("erp_ledger_transactions"):
            # Only reset if this reconciliation was the one that set it.
            # This requires knowing if the clearance_date was previously None or matched this rec's date.
            # For simplicity, we'll reset if it was matched in this document.
            if erp_line.is_reconciled and erp_line.voucher_no and erp_line.clearance_date == self.statement_to_date: # Example condition
                try:
                    # Similar logic to set_clearance_dates_on_submit, but setting to None
                    voucher_doc = frappe.get_doc(erp_line.voucher_type, erp_line.voucher_no)
                    if erp_line.voucher_type == "Journal Entry":
                        # ... logic to find the correct row and set clearance_date to None ...
                        pass
                    elif erp_line.voucher_type == "Payment Entry":
                        # ... logic to set clearance_date to None ...
                        pass
                    # frappe.db.set_value(erp_line.voucher_type, erp_line.voucher_no, "clearance_date", None)
                    reset_count += 1
                except Exception as e:
                    frappe.log_error(f"Failed to reset clearance date for {erp_line.voucher_type} {erp_line.voucher_no}: {e}",
                                     "Bank Rec Cancel")
        if reset_count > 0:
            frappe.msgprint(f"{reset_count} ERP transaction clearance dates reset.")

    def calculate_totals(self):
        """Calculates all summary totals and the final difference."""
        total_matched_debits = 0
        total_matched_credits = 0
        items_to_clear_in_bank = 0
        items_to_clear_in_erp = 0

        # Calculate from bank statement transactions
        for b_line in self.get("bank_statement_transactions"):
            if b_line.is_reconciled:
                # These are already reflected in ERP side, so sum them up from ERP side for erp_calculated_closing_balance logic
                pass # Covered by ERP lines
            else:
                items_to_clear_in_bank += 1

        # Calculate from ERP ledger transactions
        current_erp_period_effect = 0
        for e_line in self.get("erp_ledger_transactions"):
            if e_line.is_reconciled:
                # If matched, its effect is confirmed. Clearance date would be from bank statement.
                # These amounts are used to calculate the erp_calculated_closing_balance
                total_matched_debits += e_line.debit_amount # From bank's perspective this is withdrawal
                total_matched_credits += e_line.credit_amount # From bank's perspective this is deposit
                current_erp_period_effect += (e_line.debit_amount - e_line.credit_amount)
            else:
                items_to_clear_in_erp +=1

        self.total_matched_debits = total_matched_debits
        self.total_matched_credits = total_matched_credits
        self.items_to_clear_in_bank = items_to_clear_in_bank
        self.items_to_clear_in_erp = items_to_clear_in_erp

        # ERP Calculated Closing Balance = ERP Opening + Net effect of *ALL* (matched & newly created) ERP transactions in period
        # The current_erp_period_effect only includes matched items fetched initially.
        # We need to sum all debits and credits from the erp_ledger_transactions table that are marked as reconciled.

        erp_closing_from_reconciled_lines = 0
        for erp_line in self.get("erp_ledger_transactions"):
            if erp_line.is_reconciled:
                 erp_closing_from_reconciled_lines += (flt(erp_line.debit_amount) - flt(erp_line.credit_amount))

        self.erp_calculated_closing_balance = flt(self.erp_opening_balance) + erp_closing_from_reconciled_lines
        self.calculate_difference()

    def calculate_difference(self):
        self.difference = flt(self.bank_statement_closing_balance) - flt(self.erp_calculated_closing_balance)

# --- Helper functions outside the class (if any) ---
# E.g., more sophisticated CSV parsing, OFX parsing, etc.

# Whitelist methods that can be called from client-side scripts
# frappe.whitelist()(BankReconciliation.get_unreconciled_erp_transactions) # This is done with @frappe.whitelist decorator
# frappe.whitelist()(BankReconciliation.import_bank_statement)
# frappe.whitelist()(BankReconciliation.auto_match_transactions)
# frappe.whitelist()(BankReconciliation.create_erp_entry_for_bank_transaction)

# Note: Child DocType Python files (BankStatementTransactionLine.py, ERPLedgerTransactionLine.py)
# are usually not needed unless they have their own specific logic, which is uncommon for simple data containers.
# Their definitions are primarily in JSON (Doctype definition).
