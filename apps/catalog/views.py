from common.views import BulkAPIView
from .filters import filter_items
from .models import *
from .serializers import *


class ItemBulkView(BulkAPIView):
	app_label = 'catalog'
	model_name = 'Item'
	
	queryset = Item.objects.all()
	serializer_class = ItemSerializer

	def get_queryset(self):
		qs = super().get_queryset()
		return filter_items(qs, self.request.GET)