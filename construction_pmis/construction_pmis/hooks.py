# Copyright (c) 2024, Jules and contributors
# For license information, please see license.txt

app_name = "construction_pmis"
app_title = "Construction PMIS"
app_publisher = "Jules"
app_description = "Project Management Information System for Construction Companies"
app_email = "jules@example.com"
app_license = "MIT"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/construction_pmis/css/construction_pmis.css"
# app_include_js = "/assets/construction_pmis/js/construction_pmis.js"

# include js, css files in header of web_ όταν.html
# web_include_css = "/assets/construction_pmis/css/construction_pmis.css"
# web_include_js = "/assets/construction_pmis/js/construction_pmis.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "construction_pmis/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "construction_pmis.utils.jinja_methods",
#	"filters": "construction_pmis.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "construction_pmis.install.before_install"
# after_install = "construction_pmis.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "construction_pmis.uninstall.before_uninstall"
# after_uninstall = "construction_pmis.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being integrated is given as a key
# Values can be a list of methods to be called or a dotted path to a single method

# integration_setup = {
#	"frappe": [
#		"method.one",
#		"method.two"
#	]
# }

# Overriding Default Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "construction_pmis.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "construction_pmis.custom_dashboards.get_task_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#           when a supporting document is cancelled
# cancel_linked_documents_on_cancel = ["Stock Entry"]

# Request Events
# ----------------
# before_request = ["construction_pmis.utils.before_request"]
# after_request = ["construction_pmis.utils.after_request"]

# Job Events
# ----------
# before_job = ["construction_pmis.utils.before_job"]
# after_job = ["construction_pmis.utils.after_job"]

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"construction_pmis.tasks.all"
#	],
#	"daily": [
#		"construction_pmis.tasks.daily"
#	],
#	"hourly": [
#		"construction_pmis.tasks.hourly"
#	],
#	"weekly": [
#		"construction_pmis.tasks.weekly"
#	],
#	"monthly": [
#		"construction_pmis.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "construction_pmis.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "construction_pmis.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "construction_pmis.custom_dashboards.get_task_dashboard_data"
# }

# Permissions
# -----------
#
# permissions = [
#	{
#		"role": "System Manager",
#		"doctype": "MyDoctype",
#		"permission_type": "read",
#	}
# ]

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Project": {
		"before_save": "construction_pmis.custom_scripts.project.calculate_total_budget_server"
	}
}
# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"construction_pmis.tasks.all"
#	],
#	"daily": [
#		"construction_pmis.tasks.daily"
#	],
#	"hourly": [
#		"construction_pmis.tasks.hourly"
#	],
#	"weekly": [
#		"construction_pmis.tasks.weekly"
#	],
#	"monthly": [
#		"construction_pmis.tasks.monthly"
#	],
# }

# Fixtures
# --------

# fixtures = ["Custom Field", "Property Setter"]
# fixtures = ["Custom Field", "Property Setter"]
fixtures = [
    {"dt": "Custom Field", "filters": [
        ["module", "=", "Construction PMIS"]
    ]}
]
# fixtures = []

# Module Icons
# ------------
# app_icon = "octicon octicon-file-directory"
# app_color = "grey"
# app_icon_style = "font-size: 1.2em;"

# Required Apps
# -------------
# required_apps = ["erpnext"]

# Boot Session
# ------------
# boot_session = "construction_pmis.patches.boot_session"

# Report Overrides
# ----------------
# report_override = {
#     "Sales Invoice": "construction_pmis.reports.custom_sales_invoice.CustomSalesInvoice"
# }

# Standard Formatters
# -------------------
# standard_formatters = {
#     "Item": "construction_pmis.formatters.item_formatter"
# }

# Ignore Doctypes on Sync
# -----------------------
# ignore_doctypes_on_sync = ["My暫存Doctype"]

# User Data Protection
# --------------------

# has_personal_data = True or False
# items_containing_personal_data = ["User", "Address"] # list of doctypes
# default_fields_containing_personal_data = {
# 	"User": ["email", "first_name", "last_name", "phone"],
# }

# On Install
# ----------
# on_install = "construction_pmis.setup.install.after_install"
# on_uninstall = "construction_pmis.setup.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# desk_notifications = {
#     "Item": {
#         "method": "construction_pmis.notifications.item_notification",
#         "condition": "doc.item_group == 'Raw Material'"
#     }
# }

# Portal Menu Items
# -----------------
# portal_menu_items = [
#     {"title": _("Item"), "route": "/item", "role": "Customer"}
# ]

# On Update
# ---------
# on_update = "construction_pmis.setup.update.after_update"

# Website Route Rules
# -------------------
# website_route_rules = [
#	{"from_route": "/old-url", "to_route": "/new-url", "redirect": True},
# ]

# Asset Compilation
# -----------------
# build_json = {
#     "mymodule.bundle.js": [
#         "public/js/mymodule/file1.js",
#         "public/js/mymodule/file2.js"
#     ],
#     "mymodule.bundle.css": [
#         "public/css/mymodule/file1.css",
#         "public/css/mymodule/file2.css"
#     ]
# }

# Default Email Template
# ----------------------
# default_email_template = "construction_pmis/templates/emails/default.html"

# Access Control
# --------------
# allow_guest_to_view = ["Web Page"]

# App Commands
# ------------
# app_commands = [
#     "construction_pmis.commands.my_custom_command"
# ]

# Background Jobs
# ---------------
# background_workers = {
#     "my_queue": {
#         "jobs": ["construction_pmis.utils.long_running_job"],
#         "interval": 300 # seconds
#     }
# }

# Desk Pages
# ----------
# desk_pages = {
#     "My Page": {
#         "label": _("My Page"),
#         "icon": "octicon octicon-book",
#         "route": "app/my-page",
#         "module": "Construction PMIS"
#     }
# }

# Form Scripts
# ------------
doctype_js = {
    "Project": "public/js/project_budget.js"
}
# form_render_js = {
#     "Sales Order": "public/js/sales_order_form.js"
# }

# List View Settings
# ------------------
# list_view_settings = {
#     "Sales Order": {
#         "get_indicator": "construction_pmis.utils.get_sales_order_indicator"
#     }
# }

# Property Setters
# ----------------
# property_setters = {
#     "Sales Order": {
#         "naming_series": "SO-.#####"
#     }
# }

# Website Sitemap Generators
# --------------------------
# sitemap_generators = ["construction_pmis.utils.sitemap_generator"]

# Standard Reply Templates
# ------------------------
# standard_reply_templates = {
#     "Issue": "templates/emails/issue_reply.html"
# }
# Translation
# -----------
# get_translated_dict = {
#     ("doctype", "Item"): "construction_pmis.translations.get_item_translation",
#     ("page", "cart"): "construction_pmis.translations.get_cart_translation"
# }

# Update Notifications
# --------------------
# update_notifications = {
#     "1.0.0": {
#         "title": "New Feature Available",
#         "message": "Check out the new feature in version 1.0.0!",
#         "route": "/app/new-feature"
#     }
# }

# Website Theme
# -------------
# website_themes = [
#     {
#         "name": "my_theme",
#         "label": "My Theme",
#         "module": "Construction PMIS",
#         "parent_theme": "Standard"
#     }
# ]

# Workflow Actions
# ----------------
# workflow_actions = {
#     "Sales Order": {
#         "on_submit": "construction_pmis.workflows.sales_order.on_submit",
#         "before_cancel": "construction_pmis.workflows.sales_order.before_cancel"
#     }
# }

# Custom Permissions
# ------------------
# custom_permissions = {
#     "MyDoctype": {
#         "my_custom_permission_type": "construction_pmis.permissions.my_custom_permission_check"
#     }
# }
# Note:
# ----
# hooks.py is loaded when Frappe starts.
# It's a good place to add customizations that affect the entire app.
# For more information, see:
# https://frappeframework.com/docs/v14/user/en/basics/hooks
pass
