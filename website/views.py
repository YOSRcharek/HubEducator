from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib import messages
from .forms import RegisterForm
from core.decorators import unauthenticated_user
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django import forms
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import requests
import json
from core.models import Subscription

User = get_user_model()  # Always use custom user

# ----------------------------- Public Pages -----------------------------
def home(request):
    return render(request, 'home.html', {})

def pricing(request):
    """Display all active subscriptions for users, separated by type"""
    student_subscriptions = Subscription.objects.filter(is_active=True, user_type='student').order_by('created_at')
    teacher_subscriptions = Subscription.objects.filter(is_active=True, user_type='teacher').order_by('created_at')
    
    return render(request, 'pricing.html', {
        'student_subscriptions': student_subscriptions,
        'teacher_subscriptions': teacher_subscriptions,
    })

def web_development(request):
    return render(request, 'web-development.html', {})

def user_research(request):
    return render(request, 'user-research.html', {})

def courseDetails(request):
    return render(request, 'courseDetails.html', {})

# ----------------------------- Authentication -----------------------------
@unauthenticated_user
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                if not user.email_verified:
                    messages.error(request, "You must verify your email before logging in.")
                    return redirect("verify_code")

                auth_login(request, user)
                messages.success(request, "Connecté avec succès.")
                if user.role == 'admin':
                    return redirect('dashboard')
                elif user.role == 'teacher':
                    return redirect('teacherDash')
                else:
                    return redirect('home')
            else:
                messages.error(request, "Email ou mot de passe invalide.")
        except User.DoesNotExist:
            messages.error(request, "Aucun compte avec cet email.")
    return render(request, "login.html")


@unauthenticated_user
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()
            

            # Send verification code
            send_verification_code(user)
            messages.success(request, "Compte créé — un code de vérification a été envoyé à votre email.")
            return redirect("verify_code")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    return redirect("login")

# ----------------------------- Verification -----------------------------
def send_verification_code(user):
    code = get_random_string(length=6, allowed_chars='0123456789')
    user.verification_code = code
    user.save()

    subject = "Your Verification Code"
    message = f"Hi {user.username},\n\nYour verification code is: {code}\n\nEnter it in your platform to verify your email."
    from_email = f"HubEducator <{settings.DEFAULT_FROM_EMAIL}>"
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)


class VerifyCodeForm(forms.Form):
    code = forms.CharField(max_length=6, label="Verification Code")


def verify_code_view(request):
    if request.method == "POST":
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                user = User.objects.get(verification_code=code)
                user.email_verified = True
                user.verification_code = ''
                user.save()
                messages.success(request, "Your email is verified!")
                return redirect("login")
            except User.DoesNotExist:
                messages.error(request, "Invalid verification code.")
    else:
        form = VerifyCodeForm()
    return render(request, "verify_code.html", {"form": form})


def resend_code_view(request):
    user_id = request.session.get('user_id')  # Get user id from session
    if not user_id:
        messages.error(request, "Unable to resend code. Please login again.")
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        send_verification_code(user)
        messages.success(request, "A new verification code has been sent to your email.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    
    return redirect('verify_code')

# ----------------------------- Password Reset -----------------------------
def custom_password_reset(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "User with this email does not exist.")
                return redirect('password_reset')

            # Generate token and link
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{request.scheme}://{request.get_host()}/reset/{uid}/{token}/"

            # HTML email with inline styles
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>Password Reset</title></head>
            <body style="font-family:Arial,sans-serif; background:#f8f9fa; margin:0; padding:20px;">
                <div style="max-width:600px; margin:auto; background:#fff; padding:30px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.1); text-align:center;">
                    <img src="https://hubeducator-production.up.railway.app/static/website/img/favicons/android-chrome-192x192.png" width="100" alt="HubEducator Logo" style="margin-bottom:20px;">
                    <h1 style="font-size:24px; margin:20px 0;">Reset Your Password</h1>
                    <p style="font-size:16px;">Hi {user.username},</p>
                    <p style="font-size:16px;">Click the button below to reset your password:</p>
                    <a href="{reset_link}" style="display:inline-block; padding:12px 25px; color:#fff; background-color:#FFD700; border-radius:8px; text-decoration:none; font-weight:600;">Reset Password</a>
                    <p style="margin-top:20px; font-size:14px; color:#555;">If you didn't request this, you can ignore this email.</p>
                </div>
            </body>
            </html>
            """
            text_content = f"Hi {user.username},\nReset your password here: {reset_link}"

            email_message = EmailMultiAlternatives(
                subject="Reset Your Password",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            messages.success(request, "Password reset email sent successfully.")
            return redirect('password_reset_done')
    else:
        form = PasswordResetForm()

    return render(request, 'ResetPassword/password_reset.html', {'form': form})


# views.py
import requests
from django.shortcuts import redirect
from django.contrib.auth import get_user_model, login

User = get_user_model()

def google_callback(request):
    code = request.GET.get('code')
    if not code:
        return redirect('/')  # Or some error page

    # Exchange the code for an access token
    token_req = requests.post(
        'https://oauth2.googleapis.com/token',
        data={
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
        
    )
    token_data = token_req.json()
    access_token = token_data.get('access_token')

    # Get user info
    user_req = requests.get(
        'https://www.googleapis.com/oauth2/v1/userinfo',
        params={'access_token': access_token}
    )
    user_data = user_req.json()

    # Create or get user
    user, created = User.objects.get_or_create(email=user_data['email'])
    if created:
        user.username = user_data.get('name', user_data['email'])
        user.save()

    # Log the user in
    login(request, user)

    return redirect('/')  # Redirect to homepage after login


# ----------------------------- Payment System -----------------------------
@login_required
def initiate_payment(request, subscription_id):
    """Initiate payment for a subscription"""
    subscription = get_object_or_404(Subscription, id=subscription_id, is_active=True)
    
    # Get currency and amount from query parameters
    selected_currency = request.GET.get('currency', 'USD').upper()
    selected_amount = request.GET.get('amount', str(subscription.price))
    
    # Map of unsupported currencies to supported ones with conversion rates
    unsupported_currencies = {
        'TND': {'stripe_currency': 'usd', 'rate': 3.1},  # TND to USD
        'MAD': {'stripe_currency': 'usd', 'rate': 10.2}  # MAD to USD
    }
    
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Check if currency is supported by Stripe
        amount_float = float(selected_amount)
        display_currency = selected_currency
        display_amount = selected_amount
        
        if selected_currency in unsupported_currencies:
            # Convert to supported currency for Stripe
            conversion_info = unsupported_currencies[selected_currency]
            stripe_currency = conversion_info['stripe_currency']
            rate = conversion_info['rate']
            amount_float = amount_float / rate  # Convert back to USD
        else:
            stripe_currency = selected_currency.lower()
        
        # Convert amount to cents/smallest currency unit
        amount_in_cents = int(amount_float * 100)
        
        # Create a PaymentIntent
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency=stripe_currency,
            metadata={
                'subscription_id': subscription.id,
                'user_id': request.user.id,
                'user_email': request.user.email,
                'display_currency': display_currency,
                'display_amount': display_amount
            },
            description=f'{subscription.name} subscription for {request.user.email}'
        )
        
        # Store info in session
        request.session['subscription_id'] = subscription.id
        request.session['payment_intent_id'] = payment_intent.id
        request.session['client_secret'] = payment_intent.client_secret
        request.session['payment_currency'] = display_currency
        request.session['payment_amount'] = display_amount
        
        return render(request, 'payment/checkout.html', {
            'subscription': subscription,
            'client_secret': payment_intent.client_secret,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            'currency': display_currency,
            'amount': display_amount,
        })
        
    except Exception as e:
        messages.error(request, f"Error initiating payment: {str(e)}")
        return redirect('pricing')


@login_required
def process_payment(request):
    """Confirm payment after Stripe Elements submission"""
    if request.method == 'POST':
        try:
            import stripe
            from core.models import Transaction, UserSubscription
            from datetime import timedelta
            from django.utils import timezone
            
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Get payment intent ID from session
            payment_intent_id = request.session.get('payment_intent_id')
            subscription_id = request.session.get('subscription_id')
            
            if not payment_intent_id or not subscription_id:
                messages.error(request, "Invalid payment session")
                return redirect('pricing')
            
            # Retrieve the PaymentIntent to check its status
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            subscription = get_object_or_404(Subscription, id=subscription_id)
            
            if payment_intent.status == 'succeeded':
                # Create transaction record
                transaction, created = Transaction.objects.get_or_create(
                    stripe_payment_intent_id=payment_intent.id,
                    defaults={
                        'user': request.user,
                        'subscription': subscription,
                        'amount': subscription.price,
                        'currency': 'usd',
                        'status': 'completed',
                        'description': f'{subscription.name} subscription',
                        'completed_at': timezone.now()
                    }
                )
                
                if created:
                    # Calculate end date based on duration
                    # Simple parsing - you can make this more sophisticated
                    duration_days = 30  # Default
                    if 'month' in subscription.duration.lower():
                        duration_days = 30
                    elif 'year' in subscription.duration.lower():
                        duration_days = 365
                    elif 'day' in subscription.duration.lower():
                        import re
                        days_match = re.search(r'(\d+)', subscription.duration)
                        if days_match:
                            duration_days = int(days_match.group(1))
                    
                    # Create user subscription
                    UserSubscription.objects.create(
                        user=request.user,
                        subscription=subscription,
                        transaction=transaction,
                        end_date=timezone.now() + timedelta(days=duration_days),
                        is_active=True
                    )
                
                    # Clear session
                for key in ['subscription_id', 'payment_intent_id', 'client_secret']:
                    if key in request.session:
                        del request.session[key]
                
                # Update user role based on subscription type
                if subscription.user_type == 'teacher':
                    request.user.role = 'teacher'
                    request.user.save()
                    return redirect('teacherDash')
                else:  # student subscription
                    request.user.role = 'student'
                    request.user.save()
                    return redirect('home')
            else:
                messages.error(request, f"Payment status: {payment_intent.status}")
                return redirect('payment_failed')
            
        except Exception as e:
            messages.error(request, f"Payment processing error: {str(e)}")
            return redirect('payment_failed')
    
    return redirect('pricing')


@login_required
def payment_success(request):
    """Payment success page"""
    if request.user.role == 'teacher':
        return render(request, 'payment/success_teacher.html')
    else:
        return render(request, 'payment/success_student.html')


@login_required
def payment_failed(request):
    """Payment failed page"""
    return render(request, 'payment/failed.html')


# ----------------------------- Stripe Webhook -----------------------------
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    import stripe
    from core.models import Transaction, UserSubscription
    from datetime import timedelta
    from django.utils import timezone
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        if endpoint_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        else:
            event = json.loads(payload)
        
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            
            # Update transaction status
            try:
                transaction = Transaction.objects.get(
                    stripe_payment_intent_id=payment_intent['id']
                )
                transaction.status = 'completed'
                transaction.completed_at = timezone.now()
                transaction.save()
                
                print(f"✅ Payment succeeded for transaction {transaction.id}")
                
            except Transaction.DoesNotExist:
                print(f"⚠️ Transaction not found for payment_intent: {payment_intent['id']}")
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            
            # Update transaction status
            try:
                transaction = Transaction.objects.get(
                    stripe_payment_intent_id=payment_intent['id']
                )
                transaction.status = 'failed'
                transaction.save()
                
                print(f"❌ Payment failed for transaction {transaction.id}")
                
            except Transaction.DoesNotExist:
                print(f"⚠️ Transaction not found for payment_intent: {payment_intent['id']}")
        
        return HttpResponse(status=200)
        
    except ValueError as e:
        # Invalid payload
        print(f"❌ Invalid payload: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"❌ Invalid signature: {e}")
        return HttpResponse(status=400)
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return HttpResponse(status=500)
