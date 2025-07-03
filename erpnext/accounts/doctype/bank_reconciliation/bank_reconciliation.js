// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bank Reconciliation', {
    refresh: function(frm) {
        // Add custom buttons if the document is in the right state
        if (frm.doc.docstatus === 0) { // Draft or Processing
            frm.add_custom_button(__('Fetch ERP Transactions'), function() {
                frm.call('get_unreconciled_erp_transactions')
                    .then(r => {
                        frm.refresh_field('erp_ledger_transactions');
                        frm.refresh_field('bank_statement_transactions'); // In case auto-matching runs after fetch
                        frm.trigger('calculate_totals_and_difference_client_side');
                    });
            }).addClass('btn-primary');

            if (frm.doc.bank_statement_file) {
                frm.add_custom_button(__('Import Bank Statement'), function() {
                    frm.call('import_bank_statement', { file_url: frm.doc.bank_statement_file })
                        .then(r => {
                            frm.refresh_field('bank_statement_transactions');
                            frm.trigger('calculate_totals_and_difference_client_side');
                        });
                }).addClass('btn-primary');
            }

            frm.add_custom_button(__('Attempt Auto-Match'), function() {
                frm.call('auto_match_transactions')
                    .then(r => {
                        frm.refresh_field('erp_ledger_transactions');
                        frm.refresh_field('bank_statement_transactions');
                        frm.trigger('calculate_totals_and_difference_client_side');
                    });
            }).addClass('btn-info');
        }

        // Set status indicator colors (optional, but good UX)
        if (frm.doc.status) {
            frm.page.set_indicator(frm.doc.status, {
                "Draft": "grey",
                "Processing": "orange",
                "Reconciled": "green",
                "Cancelled": "red"
            }[frm.doc.status]);
        }

        // Make child tables read-only after submit
        if (frm.doc.docstatus === 1) { // Submitted
            frm.fields_dict['bank_statement_transactions'].grid.grid_buttons.hide();
            frm.fields_dict['erp_ledger_transactions'].grid.grid_buttons.hide();
            // frm.set_df_property('bank_statement_transactions', 'read_only', 1); // Alternative
            // frm.set_df_property('erp_ledger_transactions', 'read_only', 1);
        }

        // Add button in Bank Statement Transactions child table to create ERP Entry
        if (frm.doc.docstatus === 0 && frm.fields_dict['bank_statement_transactions']) {
            frm.fields_dict['bank_statement_transactions'].grid.add_custom_button(__('Create ERP Entry'), (row_doc) => {
                if (row_doc.is_reconciled) {
                    frappe.msgprint(__("This transaction is already reconciled."));
                    return;
                }
                // Open a dialog to get details for the new ERP entry
                let d = new frappe.ui.Dialog({
                    title: __('Create ERP Entry for: {0}', [row_doc.description]),
                    fields: [
                        {
                            label: 'Posting Date',
                            fieldname: 'posting_date',
                            fieldtype: 'Date',
                            default: row_doc.transaction_date,
                            reqd: 1
                        },
                        {
                            label: 'Other Account (Expense/Income)',
                            fieldname: 'other_account',
                            fieldtype: 'Link',
                            options: 'Account',
                            reqd: 1,
                            get_query: function() {
                                return {
                                    filters: {
                                        "company": frm.doc.company,
                                        "is_group": 0,
                                        // Filter for expense/income accounts, not bank/asset accounts
                                        "account_type": ["in", ["Expense Account", "Income Account", "Tax"]]
                                    }
                                };
                            }
                        },
                        {
                            label: 'Party Type',
                            fieldname: 'party_type',
                            fieldtype: 'Link',
                            options: 'DocType',
                            get_query: function() {
                                return {
                                    filters: {
                                        "name": ["in", ["Customer", "Supplier", "Employee"]]
                                    }
                                }
                            }
                        },
                        {
                            label: 'Party',
                            fieldname: 'party',
                            fieldtype: 'Dynamic Link',
                            options: 'party_type'
                        },
                        {
                            label: 'Cost Center',
                            fieldname: 'cost_center',
                            fieldtype: 'Link',
                            options: 'Cost Center',
                            get_query: function() {
                                return { filters: { "company": frm.doc.company } };
                            }
                        },
                        {
                            label: 'Remark',
                            fieldname: 'remark',
                            fieldtype: 'Small Text',
                            default: `Entry for: ${row_doc.description}`
                        }
                    ],
                    primary_action_label: __('Create Entry'),
                    primary_action(values) {
                        frappe.call({
                            method: 'erpnext.accounts.doctype.bank_reconciliation.bank_reconciliation.create_erp_entry_for_bank_transaction',
                            doc: frm.doc, // Pass the whole doc to have access to it server-side
                            args: {
                                bank_transaction_line_name: row_doc.name, // Pass the child table row name
                                new_entry_details: values
                            },
                            callback: function(r) {
                                if (r.message) {
                                    // The server method should return the updated parent doc
                                    // frm.doc = r.message; // This might not be enough, full refresh is safer
                                    // frm.refresh(); // Or specific fields
                                    frm.reload_doc(); // Reload to get all changes from server
                                    frappe.msgprint(__("ERP Entry created and matched."));
                                }
                            }
                        });
                        d.hide();
                    }
                });
                d.show();
            });
        }
    },

    setup: function(frm) {
        // Setup filtering for bank_account based on company
        frm.set_query("bank_account", function() {
            return {
                filters: {
                    "company": frm.doc.company,
                    "account_type": "Bank" // Ensure it's a bank type account
                }
            };
        });

        // Client-side calculation trigger (can be called after server updates)
        frm.cscript.calculate_totals_and_difference_client_side = function() {
            let erp_opening_balance = flt(frm.doc.erp_opening_balance);
            let erp_calculated_closing_balance = erp_opening_balance;
            let total_matched_debits = 0;
            let total_matched_credits = 0;
            let items_to_clear_in_bank = 0;
            let items_to_clear_in_erp = 0;

            if (frm.doc.bank_statement_transactions) {
                frm.doc.bank_statement_transactions.forEach(function(d) {
                    if (!d.is_reconciled) {
                        items_to_clear_in_bank += 1;
                    }
                });
            }

            if (frm.doc.erp_ledger_transactions) {
                frm.doc.erp_ledger_transactions.forEach(function(d) {
                    if (d.is_reconciled) {
                        erp_calculated_closing_balance += (flt(d.debit_amount) - flt(d.credit_amount));
                        total_matched_debits += flt(d.debit_amount); // from bank perspective this is withdrawal
                        total_matched_credits += flt(d.credit_amount); // from bank perspective this is deposit
                    } else {
                        items_to_clear_in_erp += 1;
                    }
                });
            }

            frm.set_value('total_matched_debits', total_matched_debits);
            frm.set_value('total_matched_credits', total_matched_credits);
            frm.set_value('items_to_clear_in_bank', items_to_clear_in_bank);
            frm.set_value('items_to_clear_in_erp', items_to_clear_in_erp);
            frm.set_value('erp_calculated_closing_balance', erp_calculated_closing_balance);
            frm.set_value('difference', flt(frm.doc.bank_statement_closing_balance) - erp_calculated_closing_balance);

            frm.refresh_fields(['total_matched_debits', 'total_matched_credits', 'items_to_clear_in_bank', 'items_to_clear_in_erp', 'erp_calculated_closing_balance', 'difference']);
        };
    },

    bank_account: function(frm) {
        if (frm.doc.bank_account) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Bank Account",
                    name: frm.doc.bank_account
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("account_currency", r.message.account_currency);
                        // Trigger server-side calculation of opening balance if statement_from_date is also set
                        if (frm.doc.statement_from_date) {
                            frm.trigger("statement_from_date"); // This will call the on_change logic on server
                        }
                    }
                }
            });
        } else {
            frm.set_value("account_currency", null);
            frm.set_value("erp_opening_balance", 0);
            frm.trigger('calculate_totals_and_difference_client_side');
        }
    },

    statement_from_date: function(frm) {
        // This will trigger the on_change on the server, which should call set_erp_opening_balance
        // The server-side on_change should then update erp_opening_balance.
        // We might need to explicitly call calculate_totals_and_difference_client_side after server returns.
        // For now, relying on server to update and then a refresh might be needed, or server returns full doc.
        if (frm.doc.bank_account && frm.doc.statement_from_date) {
             // No direct call here, as on_change on python side should handle it when doc is saved or specific field is focused out.
             // If immediate update is needed without save, a specific frm.call to set_erp_opening_balance might be better.
             // For now, let's assume user tabs out or saves, or we add a button.
        }
        frm.trigger('calculate_totals_and_difference_client_side'); // Recalculate with potentially new opening balance
    },

    bank_statement_closing_balance: function(frm) {
        frm.trigger('calculate_totals_and_difference_client_side');
    },

    // Child table triggers for recalculation if amounts are manually changed (though mostly they are read-only or set by system)
    // These are more for robustness if manual edits to matched amounts were allowed, which they typically aren't post-match.
    // bank_statement_transactions_on_form_rendered: function(frm) {
    //     // Potentially add listeners or formatters
    // },
    // erp_ledger_transactions_on_form_rendered: function(frm) {
    //     // Potentially add listeners or formatters
    // },

    // Manual Matching Logic (Example - could be more sophisticated)
    // This would involve selecting one row from bank_statement_transactions and one from erp_ledger_transactions
    // and then clicking a "Match Selected" button.
    // This requires more complex UI interaction than simple buttons.
    // For now, relying on Auto-Match and Create ERP Entry.

    // A client-side recalculation of totals when child table rows are modified (e.g., is_reconciled flag changes)
    // This is important if matching is done purely on client-side before saving.
    // However, our auto_match and create_erp_entry are server-side and refresh the doc.

    // Example for is_reconciled changing in child table (if manual checkbox was allowed)
    // This is not the primary mechanism in the current design, but shows how to hook into child table changes.
    // bank_statement_transactions_is_reconciled: function(frm, cdt, cdn) {
    //     let row = locals[cdt][cdn];
    //     // Add logic if manual reconciliation changes totals
    //     frm.trigger('calculate_totals_and_difference_client_side');
    // },
    // erp_ledger_transactions_is_reconciled: function(frm, cdt, cdn) {
    //     let row = locals[cdt][cdn];
    //     // Add logic
    //     frm.trigger('calculate_totals_and_difference_client_side');
    // }
});

// Custom function to handle matching if we add a manual "Match Selected" button
// frappe.ui.form.BankReconciliation = {
//     match_selected_transactions: function(frm) {
//         const selected_bank_txns = frm.fields_dict.bank_statement_transactions.grid.get_selected_children();
//         const selected_erp_txns = frm.fields_dict.erp_ledger_transactions.grid.get_selected_children();

//         if (selected_bank_txns.length === 0 || selected_erp_txns.length === 0) {
//             frappe.msgprint(__("Please select at least one transaction from both tables to match."));
//             return;
//         }

//         // Basic 1-to-1 matching based on selection for simplicity
//         if (selected_bank_txns.length !== selected_erp_txns.length && (selected_bank_txns.length > 1 && selected_erp_txns.length > 1) ) {
//             // Allow many-to-one or one-to-many if one of them is a single selection
//             if (selected_bank_txns.length !== 1 && selected_erp_txns.length !== 1) {
//                  frappe.msgprint(__("For manual matching of multiple transactions, please select one transaction from one table and one or more from the other, or ensure an equal number of selections for 1-to-1 matching."));
//                  return;
//             }
//         }

//         // Call a server-side method to perform the match and update clearance dates
//         frappe.call({
//             method: 'erpnext.accounts.doctype.bank_reconciliation.bank_reconciliation.manually_match_transactions',
//             doc: frm.doc,
//             args: {
//                 bank_transaction_names: selected_bank_txns.map(doc => doc.name),
//                 erp_transaction_names: selected_erp_txns.map(doc => doc.name)
//             },
//             callback: function(r) {
//                 if (r.message) {
//                     frm.reload_doc(); // Reload to get all changes
//                     frappe.msgprint(__("Selected transactions matched."));
//                 }
//             }
//         });
//     }
// };
// Then add a button:
// frm.add_custom_button(__('Match Selected'), function() {
//     frappe.ui.form.BankReconciliation.match_selected_transactions(frm);
// }).addClass('btn-success');
