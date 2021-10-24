def filter_store_items(qs, data):
	pk = data.get('pk', '')
	item_type = data.get('type', '')
	item_category = data.get('category', '')
	item = data.get('item', '')

	if pk:
		qs = qs.filter(pk=pk)
	else:
		qs = qs.filter(
			item__item_type__slug__icontains=item_type,
			item__item_category__slug__icontains=item_category,
			item__slug__icontains=item
		).exclude(
			item__item_type__slug__iexact='',
			item__item_category__slug__iexact='',
			item__slug__iexact=''
		)

	return qs.order_by('item__item_type__name', 'item__item_category__name', 'item__name')