from django.contrib import admin
from .models import Election, Candidate, Voter


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "start_time",
        "end_time",
        "contract_address",
        "is_active",
    )

    list_filter = ("start_time", "end_time")
    search_fields = ("name", "contract_address")

    readonly_fields = ("contract_address",)

    def is_active(self, obj):
        from django.utils import timezone
        now = timezone.now()
        return obj.start_time <= now <= obj.end_time

    is_active.boolean = True
    is_active.short_description = "Active"


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "election",
    )

    list_filter = ("election",)
    search_fields = ("name",)


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "wallet_address",
        "election",
        "has_voted",
    )

    list_filter = ("election", "has_voted")
    search_fields = ("wallet_address",)

    readonly_fields = ("has_voted",)
