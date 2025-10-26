from rest_framework import serializers

from .models import ImportBatch


class ImportBatchSerializer(serializers.ModelSerializer):
    report_csv_url = serializers.SerializerMethodField()
    report_json_url = serializers.SerializerMethodField()

    class Meta:
        model = ImportBatch
        fields = [
            "id",
            "source",
            "mode",
            "status",
            "totals",
            "created_at",
            "updated_at",
            "dry_run",
            "conflict_policy",
            "enable_linking",
            "report_csv_url",
            "report_json_url",
        ]

    def get_report_csv_url(self, obj):
        if not obj.report_csv:
            return None
        request = self.context.get("request")
        url = obj.report_csv.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_report_json_url(self, obj):
        if not obj.report_json:
            return None
        request = self.context.get("request")
        url = obj.report_json.url
        if request:
            return request.build_absolute_uri(url)
        return url
