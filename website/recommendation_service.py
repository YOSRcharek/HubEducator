import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment to use Django models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')
import django
django.setup()

from core.models import Certificate, Speciality, CertificateAttempt, User

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/recommend/<int:user_id>', methods=['GET'])
def recommend_certificates(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return jsonify({'error': 'User not found'}), 404

    # Get specialities of certificates the user has passed, ordered by most passed
    passed_attempts = CertificateAttempt.objects.filter(user=user, passed=True)
    speciality_counts = {}
    for attempt in passed_attempts:
        spec_id = attempt.certificate.speciality.id
        speciality_counts[spec_id] = speciality_counts.get(spec_id, 0) + 1

    if not speciality_counts:
        # If no passed certificates, recommend popular or all certificates
        recommended = Certificate.objects.all()[:10]  # Limit to 10
    else:
        # Find the speciality with the most passed certificates
        most_passed_speciality = max(speciality_counts, key=speciality_counts.get)

        # Recommend certificates in the most passed speciality that the user hasn't passed
        recommended = Certificate.objects.filter(
            speciality__id=most_passed_speciality
        ).exclude(
            id__in=[attempt.certificate.id for attempt in passed_attempts]
        )[:10]  # Limit to 10

    # Prepare response
    recommendations = []
    for cert in recommended:
        recommendations.append({
            'id': cert.id,
            'title': cert.title,
            'description': cert.description,
            'speciality': cert.speciality.name,
            'cover_image': cert.cover_image
        })

    return jsonify({'recommendations': recommendations})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
