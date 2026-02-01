from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Import Reader & Writer functions from your blockchain helpers
from blockchain.contract_reader import (
    get_election_info, 
    get_candidates, 
    get_winner, 
    get_vote_history
)
from blockchain.contract_writer import (
    add_candidate, 
    register_voter, 
    cast_vote, 
    reset_blockchain_election
)

# --- AUTHENTICATION & GATEWAY ---

def custom_login_view(request):
    """ Authenticates users using Wallet Address as Username and Private Key as Password """
    if request.method == "POST":
        wallet_address = request.POST.get('username', '').strip()
        private_key = request.POST.get('password', '').strip()
        
        try:
            # Check if the Wallet Address is an authorized Django User
            user = User.objects.get(username=wallet_address)
            
            # Store the Private Key in session for use on the dashboard
            request.session['voter_pk'] = private_key 
            login(request, user)
            return redirect('election_entry')
        except User.DoesNotExist:
            return render(request, "elections/login.html", {"error": "This Wallet Address is not authorized to vote."})
            
    return render(request, "elections/login.html")

@login_required
def election_gateway(request):
    """ Redirects users based on staff status """
    if request.user.is_staff:
        return redirect('admin_controls')
    return redirect('web_dashboard')

# --- HTML VIEWS ---

def web_dashboard(request):
    """ Renders the main voting dashboard with live blockchain data """
    try:
        candidates = get_candidates()
        winner_name, max_votes, winner_id = get_winner()
        election_info = get_election_info()
        audit_history = get_vote_history() 

        display_winner = winner_name if max_votes > 0 else "Election in Progress"

        return render(request, "elections/dashboard.html", {
            "candidates": candidates,
            "winner_name": display_winner,
            "audit_history": audit_history,
            "election_name": election_info.get('name', 'Decentralized Election'),
            "error": None
        })
    except Exception as e:
        return render(request, "elections/dashboard.html", {
            "error": f"Blockchain connection failed: {str(e)}",
            "candidates": [], "winner_name": "N/A", "audit_history": []
        })

@staff_member_required
def admin_controls_page(request):
    """ 
    Unified Admin Panel with Sidebar. 
    Only accessible by Staff (Admins).
    """
    context = {
        'total_voters': User.objects.count(),
        'blockchain_info': get_election_info()
    }
    
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "add_candidate":
                name = request.POST.get("candidate_name")
                tx = add_candidate(name)
                context['success'] = f"Success: Candidate '{name}' added to Blockchain. Tx: {tx}"
            elif action == "register_voter":
                addr = request.POST.get("voter_address", "").strip()
                tx = register_voter(addr)
                # Ensure the voter also exists as a Django User for authentication
                if not User.objects.filter(username=addr).exists():
                    User.objects.create_user(username=addr, password="temporary_password")
                context['success'] = f"Success: Voter {addr} authorized. Tx: {tx}"
            elif action == "reset_election":
                tx, _, _ = reset_blockchain_election()
                context['success'] = "Election has been reset on the blockchain."
        except Exception as e:
            context['error'] = f"Blockchain Error: {str(e)}"
            
    return render(request, "elections/admin_panel.html", context)

# --- JSON API ENDPOINTS ---

@api_view(["GET"])
def blockchain_election_info(request):
    try:
        return Response(get_election_info(), status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def blockchain_candidates_info(request):
    try:
        return Response(get_candidates(), status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def declare_winner_view(request):
    try:
        name, votes, c_id = get_winner()
        return Response({"winner_name": name, "votes": votes, "candidate_id": c_id}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def audit_trail_view(request):
    try:
        return Response({"history": get_vote_history()}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def cast_vote_view(request):
    candidate_id = request.data.get("candidate_id")
    private_key = request.data.get("voter_private_key")
    try:
        tx_hash = cast_vote(private_key, int(candidate_id))
        return Response({"status": "success", "tx_hash": tx_hash}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def admin_reset_view(request):
    try:
        tx_hash, _, _ = reset_blockchain_election()
        return Response({"status": "Reset successful", "tx_hash": tx_hash}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)