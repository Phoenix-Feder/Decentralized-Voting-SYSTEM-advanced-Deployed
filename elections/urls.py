from django.urls import path
from . import views

urlpatterns = [
    # --- GATEWAY & LOGIN ---
    # The primary entry point that decides if you are an Admin or Voter
    path("entry/", views.election_gateway, name="election_entry"),
    path("login/", views.custom_login_view, name="voter_login"),

    # --- HTML UI ---
    # The main Voter/Public Dashboard
    path("dashboard/", views.web_dashboard, name="web_dashboard"),
    
    # The Unified Admin Command Center (Voter Reg, Candidate Add, Election Reset)
    path("admin-panel/", views.admin_controls_page, name="admin_controls"),

    # --- JSON API (READ) ---
    path("blockchain/election/", views.blockchain_election_info, name="api_election_info"),
    path("blockchain/candidates/", views.blockchain_candidates_info, name="api_candidates_list"),
    path("blockchain/winner/", views.declare_winner_view, name="api_declare_winner"),
    path("blockchain/audit/", views.audit_trail_view, name="api_audit_trail"),

    # --- JSON API (WRITE) ---
    # Note: These now point to the views that handle the API POST requests
    path("blockchain/vote/", views.cast_vote_view, name="api_cast_vote"),
    path("blockchain/admin/reset/", views.admin_reset_view, name="api_admin_reset"),
]