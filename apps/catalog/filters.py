def filter_items(qs, data):
	pk = data.get('pk', '')
	item_type = data.get('type', '')
	item_category = data.get('category', '')
	item = data.get('item', '')

	if pk:
		qs = qs.filter(pk=pk)
	else:
		qs = qs.filter(
			item_type__slug__icontains=item_type,
			item_category__slug__icontains=item_category,
			slug__icontains=item
		).exclude(
			item_type__slug__iexact='',
			item_category__slug__iexact='',
			slug__iexact=''
		)

	return qs.order_by('item_type__name', 'item_category__name', 'name')