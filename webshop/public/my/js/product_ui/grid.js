webshop.ProductGrid = class {
	/* Options:
		- items: Items
		- settings: Webshop Settings
		- products_section: Products Wrapper
		- preference: If preference is not grid view, render but hide
	*/
	constructor(options) {
		Object.assign(this, options);

		if (this.preference !== "Grid View") {
			this.products_section.addClass("hidden");
		}

		this.products_section.empty();
		this.make();
	}

	get_item_html(item) {
		const me = this;
		let title = item.web_item_name || item.item_name || item.item_code || "";
		title = title.length > 90 ? title.substr(0, 90) + "..." : title;

		return `
     		<div class="col">
				<div class="product-item card p-3 border rounded">
					${me.get_image_html(item, title)}
					${me.get_price_html(item)}
					<h3 class>${title}</h3>
					<div class="mt-2">
						<a href="#" class="add-to-cart-btn btn btn-primary py-1 w-100">Корзина</a>
					</div>
				</div>
			</div>
		`;
	}

	make() {
		let me = this;
		let html = ``;

		this.items.forEach(item => {

			html += `<div class="col">${this.get_item_html(item)}</div>`;
		});

		let $product_wrapper = this.products_section;
		$product_wrapper.append(html);
	}

	get_image_html(item, title) {
		let image = item.website_image;
		const route = item.route ? `/${item.route}` : '#';

		if (image) {
			return `	
				<figure>
					<a href="${route}"
						title="${title}">
						<img itemprop="image" src="${image}" class="tab-image"
							alt="${title}">
					</a>
				</figure>
			`;
		} else {
			return `
				<figure>
					<a href="${route}">
						<div class="no-image">
							${frappe.get_abbr(title)}
						</div>
					</a>
				</figure>
			`;
		}
	}

	get_card_body_html(item, title, settings) {
		let body_html = `
			<div class="card-body text-left card-body-flex" style="width:100%">
				<div style="margin-top: 1rem; display: flex;">
		`;
		body_html += this.get_title(item, title);

		// get floating elements
		if (!item.has_variants) {
			if (settings.enable_wishlist) {
				body_html += this.get_wishlist_icon(item);
			}
			if (settings.enabled) {
				body_html += this.get_cart_indicator(item);
			}

		}

		body_html += `</div>`;
		body_html += `<div class="product-category" itemprop="name">${item.item_group || ''}</div>`;

		if (item.formatted_price) {
			body_html += this.get_price_html(item);
		}

		body_html += this.get_stock_availability(item, settings);
		body_html += this.get_primary_button(item, settings);
		body_html += `</div>`; // close div on line 49

		return body_html;
	}

	get_wishlist_icon(item) {
		let icon_class = item.wished ? "wished" : "not-wished";
		return `
			<div class="like-action ${item.wished ? "like-action-wished" : ''}"
				data-item-code="${item.item_code}">
				<svg class="icon sm">
					<use class="${icon_class} wish-icon" href="#icon-heart"></use>
				</svg>
			</div>
		`;
	}

	get_cart_indicator(item) {
		return `
			<div class="cart-indicator ${item.in_cart ? '' : 'hidden'}" data-item-code="${item.item_code}">
				1
			</div>
		`;
	}

	get_price_html(item) {
		let price_html = `
			<div class="product-price fw-bold" itemprop="offers" itemscope itemtype="https://schema.org/AggregateOffer">
				${item.formatted_price || ''}
		`;

		if (item.formatted_mrp) {
			price_html += `
				<small class="striked-price">
					<s>${item.formatted_mrp ? item.formatted_mrp.replace(/ +/g, "") : ""}</s>
				</small>
				<small class="ml-1 product-info-green">
					${item.discount} OFF
				</small>
			`;
		}
		price_html += `</div>`;
		return price_html;
	}

	get_stock_availability(item, settings) {
		if (settings.show_stock_availability && !item.has_variants) {
			if (item.on_backorder) {
				return `
					<span class="out-of-stock mb-2 mt-1" style="color: var(--primary-color)">
						${__("Available on backorder")}
					</span>
				`;
			} else if (!item.in_stock) {
				return `
					<span class="out-of-stock mb-2 mt-1">
						${__("Out of stock")}
					</span>
				`;
			}
		}

		return ``;
	}

	get_primary_button(item, settings) {
		if (item.has_variants) {
			return `
				<a href="/${item.route || '#'}">
					<div class="btn btn-sm btn-explore-variants w-100 mt-4">
						${__('Explore')}
					</div>
				</a>
			`;
		} else if (settings.enabled && (settings.allow_items_not_in_stock || item.in_stock)) {
			return `
				<div id="${item.name}" class="btn
					btn-sm btn-primary btn-add-to-cart-list
					w-100 mt-2 ${item.in_cart ? 'hidden' : ''}"
					data-item-code="${item.item_code}">
					<span class="mr-2">
						<svg class="icon icon-md">
							<use href="#icon-assets"></use>
						</svg>
					</span>
					${settings.enable_checkout ? __('Add to Cart') : __('Add to Quote')}
				</div>

				<a href="/cart">
					<div id="${item.name}" class="btn
						btn-sm btn-primary btn-add-to-cart-list
						w-100 mt-4 go-to-cart-grid
						${item.in_cart ? '' : 'hidden'}"
						data-item-code="${item.item_code}">
						${settings.enable_checkout ? __('Go to Cart') : __('Go to Quote')}
					</div>
				</a>
			`;
		} else {
			return ``;
		}
	}
};
