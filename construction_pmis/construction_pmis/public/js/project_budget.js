// Client script for Project Doctype to calculate total budget

frappe.ui.form.on('Project', {
    custom_project_budget_lines_on_form_rendered: function(frm) {
        calculate_total_budget(frm);
    },
    custom_project_budget_lines_budget_amount: function(frm, cdt, cdn) {
        calculate_total_budget(frm);
    },
    custom_project_budget_lines_remove: function(frm) {
        calculate_total_budget(frm);
    },
    refresh: function(frm) {
        // Also calculate on refresh in case data is loaded/changed server-side
        // but ensure custom_project_budget_lines is present
        if (frm.doc.custom_project_budget_lines) {
            calculate_total_budget(frm);
        }
    }
});

function calculate_total_budget(frm) {
    let total_budget = 0;
    if (frm.doc.custom_project_budget_lines) {
        frm.doc.custom_project_budget_lines.forEach(function(line) {
            total_budget += flt(line.budget_amount);
        });
    }
    frm.set_value('custom_total_budget_amount', total_budget);
    frm.refresh_field('custom_total_budget_amount');
}

// Also, it would be good to have this calculation server-side
// in Project's before_save event to ensure data integrity.
// This can be hooked via hooks.py:
// doc_events = {
//     "Project": {
//         "before_save": "construction_pmis.custom_scripts.project.calculate_total_budget_server"
//     }
// }
// And then create the corresponding python function.
