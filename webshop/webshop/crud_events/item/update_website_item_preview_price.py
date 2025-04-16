import frappe

# frappe.utils.logger.set_log_level("DEBUG")
# my_logger = frappe.logger("my-web", allow_site=True, file_count=50)


def execute(doc, method=None):
    """Update Website Item if change in Item impacts it."""
    web_item = frappe.db.exists("Website Item", {"item_code": doc.item_code})
    # my_logger.info(
    #     f"[update_website_item_preview_price] Item: {doc.item_code}, Website Item: {web_item}, Method: {method}"
    # )

    if web_item:
        price_list_rate = frappe.db.get_value(
            'Item Price',
            {'item_code': doc.item_code, 'price_list': 'Standard Selling'},
            'price_list_rate'
        ) or 0
        
        # my_logger.info(
        #     f"[update_website_item_preview_price] Price List Rate: {price_list_rate}"
        # )
        web_item_doc = frappe.get_doc("Website Item", web_item)
        web_item_doc.raw_price_value = int(price_list_rate)
        web_item_doc.save()