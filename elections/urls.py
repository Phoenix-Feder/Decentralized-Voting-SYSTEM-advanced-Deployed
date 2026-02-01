from django.urls import path
from . import views

urlpatterns = [
    # --- GATEWAY & LOGIN ---
    path("entry/", views.election_gateway, name="election_entry"),
    path("login/", views.custom_login_view, name="voter_login"),

    # --- HTML UI ---
    path("dashboard/", views.web_dashboard, name="web_dashboard"),
    path("admin-panel/", views.admin_controls_page, name="admin_controls"),

    # --- JSON API (READ) ---
    path("blockchain/election/", views.blockchain_election_info, name="api_election_info"),
    path("blockchain/candidates/", views.blockchain_candidates_info, name="api_candidates_list"),
    path("blockchain/winner/", views.declare_winner_view, name="api_declare_winner"),
    path("blockchain/audit/", views.audit_trail_view, name="api_audit_trail"),

    # --- JSON API (WRITE) ---
    path("blockchain/vote/", views.cast_vote_view, name="api_cast_vote"),
    path("blockchain/admin/setup/", views.admin_reset_view, name="api_admin_reset"),
]