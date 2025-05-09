# -*- coding: utf-8 -*-
# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from erpnext.stock.doctype.item.item import Item

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt, random_string
from frappe.website.doctype.website_slideshow.website_slideshow import get_slideshow
from frappe.website.website_generator import WebsiteGenerator

from webshop.webshop.doctype.item_review.item_review import get_item_reviews
from webshop.webshop.redisearch_utils import (
    delete_item_from_index,
    insert_item_to_index,
    update_index_for_item,
)
from webshop.webshop.shopping_cart.cart import _set_price_list
from webshop.webshop.doctype.override_doctype.item_group import (
    get_parent_item_groups,
    invalidate_cache_for,
)
from erpnext.stock.doctype.item.item import Item
from erpnext.utilities.product import get_price
from webshop.webshop.shopping_cart.cart import get_party
from webshop.webshop.variant_selector.item_variants_cache import (
    ItemVariantsCacheManager,
)


class WebsiteItem(WebsiteGenerator):
	website = frappe._dict(
		page_title_field="web_item_name",
		condition_field="published",
		# template="templates/generators/item/item.html",
		template="templates/generators/my_updated_item/item.html",
		no_cache=1,
	)

	def autoname(self):
		# use naming series to accomodate items with same name (different item code)
		from frappe.model.naming import get_default_naming_series, make_autoname

		naming_series = get_default_naming_series("Website Item")
		if not self.name and naming_series:
			self.name = make_autoname(naming_series, doc=self)

	def onload(self):
		super(WebsiteItem, self).onload()

	def validate(self):
		super(WebsiteItem, self).validate()

		if not self.item_code:
			frappe.throw(_("Item Code is required"), title=_("Mandatory"))

		self.validate_duplicate_website_item()
		self.validate_website_image()
		self.make_thumbnail()
		self.publish_unpublish_desk_item(publish=True)

		if not self.get("__islocal"):
			wig = frappe.qb.DocType("Website Item Group")
			query = (
				frappe.qb.from_(wig)
				.select(wig.item_group)
				.where(
					(wig.parentfield == "website_item_groups")
					& (wig.parenttype == "Website Item")
					& (wig.parent == self.name)
				)
			)
			result = query.run(as_list=True)

			self.old_website_item_groups = [x[0] for x in result]
		


		from webshop.webshop.utils.my_logger import my_logger
		my_logger.debug(f"{self.item_characteristics_values}")
		if self.content_render_type == "Standard Grids":
			if len(self.item_characteristics_values) < 2:
				frappe.throw(
					_("Please add at least 2 characteristics blocks"),
					title=_("Mandatory"),
					exc=frappe.ValidationError,
				)
			for row in self.item_characteristics_values:
				my_logger.debug(f"iter {row.__dict__}")


	def on_update(self):
		invalidate_cache_for_web_item(self)
		self.update_template_item()

	def on_trash(self):
		super(WebsiteItem, self).on_trash()
		delete_item_from_index(self)
		self.publish_unpublish_desk_item(publish=False)

	def validate_duplicate_website_item(self):
		existing_web_item = frappe.db.exists(
			"Website Item", {"item_code": self.item_code}
		)
		if existing_web_item and existing_web_item != self.name:
			message = _("Website Item already exists against Item {0}").format(
				frappe.bold(self.item_code)
			)
			frappe.throw(message, title=_("Already Published"))

	def publish_unpublish_desk_item(self, publish=True):
		if (
			frappe.db.get_value("Item", self.item_code, "published_in_website")
			and publish
		):
			return  # if already published don't publish again
		frappe.db.set_value("Item", self.item_code, "published_in_website", publish)

	def make_route(self):
		"""Called from set_route in WebsiteGenerator."""
		if not self.route:
			return (
				cstr(frappe.db.get_value("Item Group", self.item_group, "route"))
				+ "/"
				+ self.scrub(
					(self.item_name if self.item_name else self.item_code)
					+ "-"
					+ random_string(5)
				)
			)

	def update_template_item(self):
		"""Publish Template Item if Variant is published."""
		if self.variant_of:
			if self.published:
				# show template
				template_item = frappe.get_doc("Item", self.variant_of)

				if not template_item.published_in_website:
					template_item.flags.ignore_permissions = True
					make_website_item(template_item)

	def validate_website_image(self):
		if frappe.flags.in_import:
			return

		"""Validate if the website image is a public file"""
		if not self.website_image:
			return

		# find if website image url exists as public
		file_doc = frappe.get_all(
			"File",
			filters={"file_url": self.website_image},
			fields=["name", "is_private"],
			order_by="is_private asc",
			limit_page_length=1,
		)

		if file_doc:
			file_doc = file_doc[0]

		if not file_doc:
			frappe.msgprint(
				_("Website Image {0} attached to Item {1} cannot be found").format(
					self.website_image, self.name
				)
			)

			self.website_image = None

		elif file_doc.is_private:
			frappe.msgprint(_("Website Image should be a public file or website URL"))

			self.website_image = None

	def make_thumbnail(self):
		"""Make a thumbnail of `website_image`"""
		if frappe.flags.in_import or frappe.flags.in_migrate:
			return

		import requests.exceptions

		db_website_image = frappe.db.get_value(self.doctype, self.name, "website_image")
		if not self.is_new() and self.website_image != db_website_image:
			self.thumbnail = None

		if self.website_image and not self.thumbnail:
			file_doc = None

			try:
				file_doc = frappe.get_doc(
					"File",
					{
						"file_url": self.website_image,
						"attached_to_doctype": "Website Item",
						"attached_to_name": self.name,
					},
				)
			except frappe.DoesNotExistError:
				pass
				# cleanup
				frappe.local.message_log.pop()

			except requests.exceptions.HTTPError:
				frappe.msgprint(
					_("Warning: Invalid attachment {0}").format(self.website_image)
				)
				self.website_image = None

			except requests.exceptions.SSLError:
				frappe.msgprint(
					_("Warning: Invalid SSL certificate on attachment {0}").format(
						self.website_image
					)
				)
				self.website_image = None

			# for CSV import
			if self.website_image and not file_doc:
				try:
					file_doc = frappe.get_doc(
						{
							"doctype": "File",
							"file_url": self.website_image,
							"attached_to_doctype": "Website Item",
							"attached_to_name": self.name,
						}
					).save()

				except IOError:
					self.website_image = None

			if file_doc:
				if not file_doc.thumbnail_url:
					file_doc.make_thumbnail()

				self.thumbnail = file_doc.thumbnail_url

	def get_context(self, context):
		context.show_search = True
		context.search_link = "/search"
		context.body_class = "product-page"

		context.parents = get_parent_item_groups(
			self.item_group, from_item=True
		)  # breadcumbs
		self.attributes = frappe.get_all(
			"Item Variant Attribute",
			fields=["attribute", "attribute_value"],
			filters={"parent": self.item_code},
		)

		if self.slideshow:
			context.update(get_slideshow(self))

		self.set_metatags(context)
		self.set_shopping_cart_data(context)

		settings = context.shopping_cart.cart_settings

		self.get_product_details_section(context)

		if settings.get("enable_reviews"):
			reviews_data = get_item_reviews(self.name)
			context.update(reviews_data)
			context.reviews = context.reviews[:4]

		context.wished = False
		if frappe.db.exists(
			"Wishlist Item",
			{"item_code": self.item_code, "parent": frappe.session.user},
		):
			context.wished = True

		context.user_is_customer = check_if_user_is_customer()

		context.recommended_items = None
		if settings and settings.enable_recommendations:
			context.recommended_items = self.get_recommended_items(settings)



		# item = frappe.get_doc("Item", self.item_code)
		raw_fields = self.item_characteristics_values
		blocks = {} 
  
		i_block_counter = 0
		current_block_row = None
		current_break_value = None
		for row in raw_fields:
			if row.type == "Card Break":
				current_block_row = row
				current_break_value = current_block_row.field_value or str(i_block_counter)
				blocks[current_break_value] = {
					"label": current_block_row.label,
					"field_value": current_block_row.field_value,
					"fields": [],
				}
				i_block_counter +=1
			elif current_block_row is not None:
				label = row.get("label")
				field_value = row.get("field_value")
				dynamic = row.get("dynamic")
				# if dynamic:
				# 	try:
				# 		resolved_value = self.item_group.get(field_value)
				# 		if resolved_value is None:
				# 			raise ValueError(f"Missing value for dynamic field '{field_value}'")
				# 	except Exception as e:
				# 		frappe.throw(f"Error resolving dynamic field '{field_value}': {e}")
				# else:
				resolved_value = field_value
				blocks[current_break_value]["fields"].append({
					"label": label,
					"field_value": resolved_value,
					"dynamic": dynamic
				})
	
		# Convert blocks dict to list
		context.characteristic_blocks = list(blocks.values())
		# context.item = item
		return context

	def set_selected_attributes(self, variants, context, attribute_values_available):
		for variant in variants:
			variant.attributes = frappe.get_all(
				"Item Variant Attribute",
				filters={"parent": variant.name},
				fields=["attribute", "attribute_value as value"],
			)

			# make an attribute-value map for easier access in templates
			variant.attribute_map = frappe._dict(
				{attr.attribute: attr.value for attr in variant.attributes}
			)

			for attr in variant.attributes:
				values = attribute_values_available.setdefault(attr.attribute, [])
				if attr.value not in values:
					values.append(attr.value)

				if variant.name == context.variant.name:
					context.selected_attributes[attr.attribute] = attr.value

	def set_attribute_values(self, attributes, context, attribute_values_available):
		for attr in attributes:
			values = context.attribute_values.setdefault(attr.attribute, [])

			if cint(
				frappe.db.get_value("Item Attribute", attr.attribute, "numeric_values")
			):
				for val in sorted(
					attribute_values_available.get(attr.attribute, []), key=flt
				):
					values.append(val)
			else:
				# get list of values defined (for sequence)
				for attr_value in frappe.db.get_all(
					"Item Attribute Value",
					fields=["attribute_value"],
					filters={"parent": attr.attribute},
					order_by="idx asc",
				):

					if attr_value.attribute_value in attribute_values_available.get(
						attr.attribute, []
					):
						values.append(attr_value.attribute_value)

	def set_metatags(self, context):
		context.metatags = frappe._dict({})

		safe_description = frappe.utils.to_markdown(self.description)

		context.metatags.url = frappe.utils.get_url() + "/" + context.route

		if context.website_image:
			if context.website_image.startswith("http"):
				url = context.website_image
			else:
				url = frappe.utils.get_url() + context.website_image
			context.metatags.image = url

		context.metatags.description = safe_description[:300]

		context.metatags.title = self.web_item_name or self.item_name or self.item_code

		context.metatags["og:type"] = "product"
		context.metatags["og:site_name"] = "ERPNext"

	def set_shopping_cart_data(self, context):
		from webshop.webshop.shopping_cart.product_info import (
			get_product_info_for_website,
		)

		context.shopping_cart = get_product_info_for_website(
			self.item_code, skip_quotation_creation=True
		)

	def copy_specification_from_item_group(self):
		self.set("website_specifications", [])
		if self.item_group:
			for label, desc in frappe.db.get_values(
				"Item Website Specification",
				{"parent": self.item_group},
				["label", "description"],
			):
				row = self.append("website_specifications")
				row.label = label
				row.description = desc

	def get_product_details_section(self, context):
		"""Get section with tabs or website specifications."""
		context.show_tabs = self.show_tabbed_section
		if self.show_tabbed_section and (self.tabs or self.website_specifications):
			context.tabs = self.get_tabs()
		else:
			context.website_specifications = self.website_specifications

	def get_tabs(self):
		tab_values = {}
		tab_values["tab_1_title"] = "Product Details"
		tab_values["tab_1_content"] = frappe.render_template(
			"templates/generators/item/item_specifications.html",
			{
				"website_specifications": self.website_specifications,
				"show_tabs": self.show_tabbed_section,
			},
		)

		for row in self.tabs:
			tab_values[f"tab_{row.idx + 1}_title"] = _(row.label)
			tab_values[f"tab_{row.idx + 1}_content"] = row.content

		return tab_values

	def get_recommended_items(self, settings):
		ri = frappe.qb.DocType("Recommended Items")
		wi = frappe.qb.DocType("Website Item")

		query = (
			frappe.qb.from_(ri)
			.join(wi)
			.on(ri.item_code == wi.item_code)
			.select(
				ri.item_code, ri.route, ri.website_item_name, ri.website_item_thumbnail
			)
			.where((ri.parent == self.name) & (wi.published == 1))
			.orderby(ri.idx)
		)
		items = query.run(as_dict=True)

		if settings.show_price:
			is_guest = frappe.session.user == "Guest"
			# Show Price if logged in.
			# If not logged in and price is hidden for guest, skip price fetch.
			if is_guest and settings.hide_price_for_guest:
				return items

			selling_price_list = _set_price_list(settings, None)
			party = get_party()

			for item in items:
				item.price_info = get_price(
					item.item_code,
					selling_price_list,
					settings.default_customer_group,
					settings.company,
					party=party,
				)

		return items


def invalidate_item_variants_cache_for_website(doc):
	"""
	Rebuild ItemVariantsCacheManager via Item or Website Item

	Args:
		doc (Item): item of which cache should be cleared
	"""
	item_code = None
	is_web_item = doc.get("published_in_website") or doc.get("published")

	if doc.has_variants and is_web_item:
		item_code = doc.item_code
	elif doc.variant_of and frappe.db.get_value(
		"Item", doc.variant_of, "published_in_website"
	):
		item_code = doc.variant_of

	if not item_code:
		return

	item_cache = ItemVariantsCacheManager(item_code)
	item_cache.rebuild_cache()


def invalidate_cache_for_web_item(doc):
	"""
	Invalidate Website Item Group cache and rebuild ItemVariantsCacheManager
	Args:
		doc (Item): document against which cache should be cleared
	"""
	invalidate_cache_for(doc, doc.item_group)

	website_item_groups = list(
		set(
			(doc.get("old_website_item_groups") or [])
			+ [
				d.item_group
				for d in doc.get({"doctype": "Website Item Group"})
				if d.item_group
			]
		)
	)

	for item_group in website_item_groups:
		invalidate_cache_for(doc, item_group)

	# Update Search Cache
	update_index_for_item(doc)

	invalidate_item_variants_cache_for_website(doc)


def on_doctype_update():
	# since route is a Text column, it needs a length for indexing
	frappe.db.add_index("Website Item", ["route(500)"])


def check_if_user_is_customer(user=None):
	from frappe.contacts.doctype.contact.contact import get_contact_name

	if not user:
		user = frappe.session.user

	contact_name = get_contact_name(user)
	customer = None

	if contact_name:
		contact = frappe.get_doc("Contact", contact_name)
		for link in contact.links:
			if link.link_doctype == "Customer":
				customer = link.link_name
				break

	return True if customer else False


@frappe.whitelist()
def make_website_item(doc, save=True):
	"""
	Make Website Item from Item. Used via Form UI or patch.
	"""
	if not doc:
		return

	if isinstance(doc, str):
		doc = json.loads(doc)

	if frappe.db.exists("Website Item", {"item_code": doc.get("item_code")}):
		message = _("Website Item already exists against {0}").format(
			frappe.bold(doc.get("item_code"))
		)
		frappe.throw(message, title=_("Already Published"))

	website_item = frappe.new_doc("Website Item")
	website_item.web_item_name = doc.get("item_name")

	fields_to_map = [
		"item_code",
		"item_name",
		"item_group",
		"stock_uom",
		"brand",
		"has_variants",
		"variant_of",
		"description",
	]
	for field in fields_to_map:
		website_item.update({field: doc.get(field)})

	# Needed for publishing/mapping via Form UI only
	if not frappe.flags.in_migrate and (
		doc.get("image") and not website_item.website_image
	):
		website_item.website_image = doc.get("image")

	if not save:
		return website_item

	website_item.save()

	# Add to search cache
	insert_item_to_index(website_item)

	return [website_item.name, website_item.web_item_name]

@frappe.whitelist()
def has_website_permission_for_website_item(doc, ptype, user, verbose=False):
	# Check item group permissions for website

	if user == "Administrator":
		return True

	if frappe.has_permission("Website Item", ptype=ptype, doc=doc, user=user):
		return True

	if not frappe.db.get_single_value("Webshop Settings", "login_required_to_view_products"):
		return True

	return False

@frappe.whitelist()
def has_website_permission_for_item_group(doc, ptype, user, verbose=False):
	# Check item group permissions for website
	if user == "Administrator":
		return True

	if frappe.has_permission("Item Group", ptype=ptype, doc=doc, user=user):
		return True

	if not frappe.db.get_single_value("Webshop Settings", "login_required_to_view_products"):
		return True

	return False