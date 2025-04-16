frappe.ui.form.on("Item", {
	refresh: function (frm) {
		if (!frm.doc.__islocal) {
			if (!frm.doc.published_in_website) {
				frm.add_custom_button(__("Publish in Website"), function () {
					frappe.call({
						method: "webshop.webshop.doctype.website_item.website_item.make_website_item",
						args: {
							doc: frm.doc,
						},
						freeze: true,
						freeze_message: __("Publishing Item ..."),
						callback: function (result) {
							frappe.msgprint({
								message: __("Website Item {0} has been created.",
									[repl('<a href="/app/website-item/%(item_encoded)s" class="strong">%(item)s</a>', {
										item_encoded: encodeURIComponent(result.message[0]),
										item: result.message[1]
									})]
								),
								title: __("Published"),
								indicator: "green"
							});
						}
					});
				}, __('Actions'));
			} else {
				frm.add_custom_button(__("View Website Item"), function () {
					frappe.db.get_value("Website Item", { item_code: frm.doc.name }, "name", (d) => {
						if (!d.name) frappe.throw(__("Website Item not found"));
						frappe.set_route("Form", "Website Item", d.name);
					});
				});
			}
		}
		update_parent_field_name_options(frm);
	},
});

function collectParentFieldNames(grid) {
    const gridRows = grid.grid_rows || [];

    const parentValues = [
        ...new Set(
            gridRows
                .map(row => row.doc.parent_field_name)
                .filter(val => val && val.trim() !== "")
        )
    ];

    return parentValues.join("\n");
}


function update_parent_field_name_options(frm) {
	console.log("update_parent_field_name_options");
	const grid = frm.fields_dict["item_characteristics_values"].grid;
	// const grid_rows = grid.grid_rows || [];

	// const parent_values = ["",...new Set(
	// 	grid_rows
	// 		.map(row => row.doc.parent_field_name)
	// 		.filter(val => val && val.trim() !== "")
	// )];

	const options_str = collectParentFieldNames(grid);
	console.log("options_str", options_str);

	grid.update_docfield_property(
		"parent_field_name",
		"options",
		options_str
	);
}

frappe.ui.form.on("Item Characterticis Value", {
	item_characteristics_values_add: function (frm) {
		update_parent_field_name_options(frm);
	},
	item_characteristics_values_remove: function (frm) {
		update_parent_field_name_options(frm);
	},
	field_value(frm, cdt, cdn) {
		// const str = frm.fields_dict["item_characteristics_values"].grid.grid_rows.find(r => r.doc.name === cdn).doc.field_value;
		// coopy str stirn wioth ref
		// console.log("str", [...str].join(""));
		// console.log();
		// const grid = frm.fields_dict["item_characteristics_values"].grid;
		// const prev_doc = {...grid.grid_rows.find(r => r.doc.name === cdn).doc};
		
		// const row = frappe.get_doc(cdt, cdn);
		// const newValue = row.field_value;
		// console.log("prev_row", prev_doc, newValue);

    }

});
