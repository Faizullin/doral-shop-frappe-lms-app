import frappe
# from webshop.webshop.utils.my_logger import my_logger


def get_products_data(products_data):
    products_dict = {
        i.idx: i for i in products_data
    }
    website_item_codes = [
        i.item_code for i in products_data
    ]
    website_items_dict = {i.name: i for i in frappe.get_all(
        "Website Item",
        filters={"name": ["IN", website_item_codes]},
        fields=["name", "item_name", "thumbnail", "item_code", "route"]
    )}
    item_codes = [i.item_code for i in website_items_dict.values()]
    prices = frappe.get_all(
        "Item Price",
        filters={"item_code": ["IN", item_codes], "selling": 1},
        fields=["item_code", "price_list_rate", "currency"]
    )
    price_dict = {p.item_code: p for p in prices}
    res = []
    for item in products_dict.values():
        item_code = website_items_dict.get(item.item_code).item_code
        res.append({
            "title": item.item_name,
            "image": item.thumbnail,
            "url": item.route,
            "price": price_dict.get(item_code )
        })
    return res

def get_context(context):
    homepage_doc = frappe.get_cached_doc("MyHomePageSettings")
    context.brand_blocks = [
        {
            "title": slide.heading,
            "subtitle": slide.description,
            "url": slide.url or "#",
            "image": slide.image
        }
        for slide in homepage_doc.hero_slideshow
    ]
    context.hit_products = get_products_data(homepage_doc.hit_products)
    context.new_arrival_products = get_products_data(homepage_doc.new_arrival_products)
    
    popular_categories_codes = [
        i.item_group for i in homepage_doc.popular_categories
    ]
    popular_categories = frappe.get_all(
        "Item Group",
        filters={"name": ["IN", popular_categories_codes]},
        fields=["name", "image", "route"]
    )
    context.popular_categories = [
        {
            "title": i.name,
            "image": i.image,
            "url":  i.route or "#",
        }
        for i in popular_categories
    ]
    return context
