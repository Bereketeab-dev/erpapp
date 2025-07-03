// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bank Reconciliation Statement"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("company"),
            "reqd": 1
        },
        {
            "fieldname": "bank_account",
            "label": __("Bank Account"),
            "fieldtype": "Link",
            "options": "Bank Account",
            "reqd": 1,
            "get_query": function() {
                var company = frappe.query_report.get_filter_value('company');
                return {
                    filters: {
                        "company": company,
                        "account_type": "Bank"
                    }
                };
            }
        },
        {
            "fieldname": "reconciliation_date",
            "label": __("Reconciliation Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        }
    ],
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.id == "balance_as_per_bank_statement" || column.id == "balance_as_per_erp") {
            return "<span style='font-weight:bold;'>" + value + "</span>";
        }
        if (data && (data.is_header_row || data.is_total_row)) {
             return "<span style='font-weight:bold;'>" + value + "</span>";
        }
        return value;
    }
};
