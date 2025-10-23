"""
Views for ML-based subscription recommendations
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
import json

from .ml_models import UserPreference, RecommendationHistory
from .models import Subscription
from .ml.recommendation_engine import recommender


@login_required
@require_http_methods(["POST"])
def save_preferences(request):
    """Save user preferences from questionnaire"""
    try:
        data = json.loads(request.body)
        
        # Get or create user preference
        preference, created = UserPreference.objects.get_or_create(
            user=request.user,
            defaults={
                'student_count': data.get('student_count', 0),
                'budget': Decimal(str(data.get('budget', 0))),
                'usage_frequency': data.get('usage_frequency', 1),
                'course_count': data.get('course_count', 0),
                'experience_level': data.get('experience_level', 1),
                'study_hours': Decimal(str(data.get('study_hours', 0))),
                'needs_video': data.get('needs_video', False),
                'needs_quiz': data.get('needs_quiz', False),
                'needs_forum': data.get('needs_forum', False),
                'needs_analytics': data.get('needs_analytics', False),
                'needs_certificates': data.get('needs_certificates', False),
                'needs_offline': data.get('needs_offline', False),
                'needs_support': data.get('needs_support', False),
                'goal_type': data.get('goal_type', 'academic'),
                'education_level': data.get('education_level', 'university'),
            }
        )
        
        if not created:
            # Update existing preference
            for key, value in data.items():
                if hasattr(preference, key):
                    if key in ['budget', 'study_hours']:
                        setattr(preference, key, Decimal(str(value)))
                    else:
                        setattr(preference, key, value)
            preference.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Preferences saved successfully',
            'preference_id': preference.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def get_recommendations(request):
    """Get ML-based subscription recommendations"""
    try:
        # Get user preference
        try:
            preference = UserPreference.objects.get(user=request.user)
        except UserPreference.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Please complete the questionnaire first'
            }, status=400)
        
        # Determine user type
        user_type = request.user.role if hasattr(request.user, 'role') else 'student'
        
        # Get available subscriptions
        subscriptions = Subscription.objects.filter(
            user_type=user_type,
            is_active=True
        ).order_by('price')
        
        if not subscriptions.exists():
            return JsonResponse({
                'success': False,
                'error': 'No subscriptions available'
            }, status=404)
        
        # Get recommendations from ML engine
        recommendations = recommender.get_recommendations(
            preference,
            user_type,
            subscriptions
        )
        
        # Save recommendation history
        if recommendations['primary']:
            rec = recommendations['primary']
            history = RecommendationHistory.objects.create(
                user=request.user,
                preference=preference,
                recommended_subscription=rec['subscription'],
                confidence_score=Decimal(str(rec['ml_confidence'])),
                compatibility_score=Decimal(str(rec['compatibility_score']))
            )
            
            # Add alternatives
            if len(recommendations['alternatives']) > 0:
                alt1 = recommendations['alternatives'][0]
                history.alternative_1 = alt1['subscription']
                history.alternative_1_score = Decimal(str(alt1['compatibility_score']))
            
            if len(recommendations['alternatives']) > 1:
                alt2 = recommendations['alternatives'][1]
                history.alternative_2 = alt2['subscription']
                history.alternative_2_score = Decimal(str(alt2['compatibility_score']))
            
            history.save()
        
        # Format response
        def format_recommendation(rec):
            sub = rec['subscription']
            return {
                'id': sub.id,
                'name': sub.name,
                'price': float(sub.price),
                'duration': sub.duration,
                'description': sub.description,
                'features': sub.features,
                'compatibility_score': rec['compatibility_score'],
                'ml_confidence': rec['ml_confidence'],
                'is_recommended': rec['is_recommended']
            }
        
        response_data = {
            'success': True,
            'primary_recommendation': format_recommendation(recommendations['primary']) if recommendations['primary'] else None,
            'alternatives': [format_recommendation(alt) for alt in recommendations['alternatives']],
            'ml_prediction': recommendations['ml_prediction']
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def recommendation_page(request):
    """Display recommendation questionnaire and results"""
    user_type = request.user.role if hasattr(request.user, 'role') else 'student'
    
    # Get existing preference if any
    try:
        preference = UserPreference.objects.get(user=request.user)
    except UserPreference.DoesNotExist:
        preference = None
    
    # Get available subscriptions
    subscriptions = Subscription.objects.filter(
        user_type=user_type,
        is_active=True
    ).order_by('price')
    
    context = {
        'user_type': user_type,
        'preference': preference,
        'subscriptions': subscriptions,
    }
    
    return render(request, 'ml_recommendation.html', context)


@login_required
@require_http_methods(["POST"])
def record_user_action(request):
    """Record user action on recommendation"""
    try:
        data = json.loads(request.body)
        recommendation_id = data.get('recommendation_id')
        action = data.get('action')  # 'accepted', 'alternative', 'ignored'
        chosen_subscription_id = data.get('chosen_subscription_id')
        
        history = RecommendationHistory.objects.get(id=recommendation_id, user=request.user)
        history.user_action = action
        
        if chosen_subscription_id:
            history.chosen_subscription_id = chosen_subscription_id
        
        history.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Action recorded successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def submit_feedback(request):
    """Submit feedback on recommendation"""
    try:
        data = json.loads(request.body)
        recommendation_id = data.get('recommendation_id')
        rating = data.get('rating')
        feedback_text = data.get('feedback_text', '')
        
        history = RecommendationHistory.objects.get(id=recommendation_id, user=request.user)
        history.satisfaction_rating = rating
        history.feedback_text = feedback_text
        history.feedback_date = timezone.now()
        history.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your feedback!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
