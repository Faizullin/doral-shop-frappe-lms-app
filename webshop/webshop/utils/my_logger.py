import frappe

frappe.utils.logger.set_log_level("DEBUG")
my_logger = frappe.logger("my-web", allow_site=True, file_count=50)


