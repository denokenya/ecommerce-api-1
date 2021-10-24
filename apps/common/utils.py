from rest_framework.renderers import JSONRenderer


# Admin
def hide_admin_btns(extra_context, show_save=False, show_save_add=False, close=False):
	extra_context['show_save_and_continue'] = show_save
	extra_context['show_save_and_add_another'] = show_save_add
	extra_context['show_close'] = close
	return extra_context

def remove_field(field_list, field):
	if field in field_list:
		field_list.remove(field)


# Misc.
class PrettyJsonRenderer(JSONRenderer):    
	def get_indent(self, accepted_media_type, renderer_context):
		return 2