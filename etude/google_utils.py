from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from allauth.socialaccount.models import SocialToken, SocialAccount
from django.shortcuts import get_object_or_404

def get_google_credentials_for_user(user):
    """
    Build google Credentials from allauth SocialToken.
    Returns google.oauth2.credentials.Credentials or raises ValueError.
    """
    try:
        token = SocialToken.objects.get(account__user=user, account__provider="google")
    except SocialToken.DoesNotExist:
        raise ValueError("Google account not connected")

    access_token = token.token
    refresh_token = token.token_secret or token.token_secret  # some setups store refresh in token_secret
    client = token.app  # SocialApp instance
    client_id = client.client_id
    client_secret = client.secret

    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/calendar.events"]
    )
    # refresh if needed
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        # store new access token back into SocialToken
        token.token = creds.token
        token.save()
    return creds