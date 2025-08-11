# Copyright (c) 2025, Geetab Technologies Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from collections import defaultdict
from erpnext.setup.doctype.brand.brand import get_brand_defaults
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.setup.utils import get_exchange_rate
from erpnext.stock.doctype.item.item import get_item_defaults, get_uom_conv_factor
from erpnext import get_default_company


def execute(filters=None):
	if not filters.get('pack_list'):
		frappe.throw(_("Packing List is mandatory"))
		return

	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_data(filters):
	rows = frappe.db.sql("""
		SELECT 
			pli.item_code, 
			pli.item_name, 
			SUM(pli.invoiced_qty) AS invoiced_qty, 
			pli.warehouse
		FROM `tabPack List Item` pli
		WHERE pli.parent = %(pack_list)s
		GROUP BY pli.item_code
		""", {
			"pack_list": filters.get('pack_list')
		}, as_dict=1)

	grouped_data = []
	warehouse_map = defaultdict(list)
	for r in rows:
		xwarehouse = get_item_warehouse(r)
		if xwarehouse:
			r.warehouse = xwarehouse
			
		warehouse_map[r.warehouse].append(r)

	for warehouse, items in warehouse_map.items():
		totl = sum(row.invoiced_qty for row in items) 
		grouped_data.append({"item_code": warehouse, "invoiced_qty": totl, "bold": 1,})
		grouped_data.extend(items)
		
	return grouped_data
        
def get_item_warehouse(item, defaults=None):
	company = get_default_company()
	if not defaults:
		defaults = frappe._dict(
			{
				"item_defaults": get_item_defaults(item.item_code, company),
				"item_group_defaults": get_item_group_defaults(item.item_code, company),
				"brand_defaults": get_brand_defaults(item.item_code, company),
			}
		)

	warehouse = (
		defaults.item_defaults.get("default_warehouse")
		or defaults.item_group_defaults.get("default_warehouse")
		or defaults.brand_defaults.get("default_warehouse")
	)

	if not warehouse:
		defaults = frappe.defaults.get_defaults() or {}
		warehouse_exists = frappe.db.exists(
			"Warehouse", {"name": defaults.default_warehouse, "company": company}
		)
		if defaults.get("default_warehouse") and warehouse_exists:
			warehouse = defaults.default_warehouse

	
	if not warehouse:
		default_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
		if frappe.db.get_value("Warehouse", default_warehouse, "company") == company:
			return default_warehouse

	return warehouse



def get_columns(filters):
	columns = [
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		
		{
			"label": _("Quantity"),
			"fieldname": "invoiced_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		
	]

	return columns

