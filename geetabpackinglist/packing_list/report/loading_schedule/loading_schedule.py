# Copyright (c) 2025, Geetab Technologies Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _

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

	return rows
        


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

