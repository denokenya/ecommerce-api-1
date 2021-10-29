from rest_framework import serializers


class BulkSerializer(serializers.Serializer):
	data = serializers.ListField(child=serializers.DictField())

	def validate_data(self, value):
		for i in range(0, len(value)):
			if not str(value[i].get('id')).isdigit():
				raise serializers.ValidationError(
					f"Dictionary instance at position '{i}' doesn't have 'id' key"
				)
		return value

	def get_update_ids(self):
		return {d['id']: d for d in self.validated_data['data']}

	def get_delete_ids(self):
		return [d['id'] for d in self.validated_data['data']]