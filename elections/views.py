from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

# Import Reader & Writer functions from your blockchain helpers
from blockchain.contract_reader import (
    get_election_info, 
    get_candidates, 
    get_winner, 
    get_vote_history
)
from blockchain.contract_writer import (
    add_candidate, 
    authorize_voter, 
    revoke_voter, 
    cast_vote, 
    setup_blockchain_election # Now expects (name, start_iso, end_iso)
)

# --- AUTHENTICATION & GATEWAY ---

def custom_login_view(request):
    """ Authenticates users using Wallet Address as Username and Private Key as Password """
    if request.method == "POST":
        wallet_address = request.POST.get('username', '').strip()
        private_key = request.POST.get('password', '').strip()
        
        try:
            user = User.objects.get(username=wallet_address)
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

# --- HTML UI VIEWS ---

def web_dashboard(request):
    """ Renders the main voting dashboard with live blockchain data """
    try:
        candidates = get_candidates()
        winner_name, max_votes, winner_id = get_winner()
        election_info = get_election_info()
        audit_history = get_vote_history() 

        # Convert Blockchain Unix Timestamps to Readable Python Datetime
        start_date = datetime.fromtimestamp(election_info.get('startTime', 0))
        end_date = datetime.fromtimestamp(election_info.get('endTime', 0))

        display_winner = winner_name if max_votes > 0 else "Election in Progress"

        return render(request, "elections/dashboard.html", {
            "candidates": candidates,
            "winner_name": display_winner,
            "audit_history": audit_history,
            "election_name": election_info.get('electionName', 'Decentralized Election'),
            "start_date": start_date,
            "end_date": end_date,
            "remaining_time": election_info.get('remainingTime', 0),
            "error": None
        })
    except Exception as e:
        return render(request, "elections/dashboard.html", {
            "error": f"Blockchain connection failed: {str(e)}",
            "candidates": [], "winner_name": "N/A", "audit_history": []
        })

@staff_member_required
def admin_controls_page(request):
    """ Unified Admin Panel for managing candidates, voters, and scheduling """
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
                context['success'] = f"Success: Candidate '{name}' added. Tx: {tx}"

            elif action == "register_voter":
                addr = request.POST.get("voter_address", "").strip()
                tx = authorize_voter(addr)
                if not User.objects.filter(username=addr).exists():
                    User.objects.create_user(username=addr, password="temporary_password")
                context['success'] = f"Success: Voter {addr} authorized. Tx: {tx}"

            elif action == "revoke_voter":
                addr = request.POST.get("voter_address", "").strip()
                tx = revoke_voter(addr)
                context['success'] = f"Success: Voter {addr} revoked. Tx: {tx}"

            elif action == "reset_election":
                name = request.POST.get("election_name")
                start_iso = request.POST.get("start_time")
                end_iso = request.POST.get("end_time")
                
                tx = setup_blockchain_election(name, start_iso, end_iso)
                context['success'] = f"Election '{name}' successfully scheduled on blockchain."

        except Exception as e:
            context['error'] = f"Blockchain Error: {str(e)}"
            
    return render(request, "elections/admin_panel.html", context)

# --- JSON API ENDPOINTS ---

@api_view(["GET"])
def blockchain_election_info(request):
    """ Returns current election state (Fixed the AttributeError) """
    try:
        return Response(get_election_info(), status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def blockchain_candidates_info(request):
    """ Returns all candidates """
    try:
        return Response(get_candidates(), status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def declare_winner_view(request):
    """ Returns current winner status """
    try:
        name, votes, c_id = get_winner()
        return Response({"winner_name": name, "votes": votes, "candidate_id": c_id}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def audit_trail_view(request):
    """ Returns full vote history """
    try:
        return Response({"history": get_vote_history()}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def cast_vote_view(request):
    """ Processes a vote via API """
    candidate_id = request.data.get("candidate_id")
    private_key = request.data.get("voter_private_key")
    try:
        tx_hash = cast_vote(private_key, int(candidate_id))
        return Response({"status": "success", "tx_hash": tx_hash}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def admin_reset_view(request):
    """ API endpoint for setting up an election via JSON POST """
    try:
        name = request.data.get("name")
        start_time = request.data.get("start_time")
        end_time = request.data.get("end_time")
        tx_hash = setup_blockchain_election(name, start_time, end_time)
        return Response({"status": "Setup successful", "tx_hash": tx_hash}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)