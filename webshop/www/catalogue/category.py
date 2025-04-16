import frappe
# from webshop.webshop.utils.my_logger import my_logger


def get_context(context):
    # context.parents = [{"name": frappe._("Home"), "route": "/"}]
    item_groups = frappe.get_all(
        "Item Group",
        filters={
            "parent_item_group": "Doral Products",
            },
        fields=["name", "parent_item_group", "image", "item_group_name"],
        order_by="item_group_name",
    )
    context.categories = [{
        "url": "/catalogue/category/" + i.name,
        "title": i.name,
        "image": i.image,
    } for i in item_groups]
        