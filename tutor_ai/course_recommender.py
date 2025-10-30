import os
import sys
import django
from django.utils import timezone
from django.db.models import Avg

# =========================================================
# Configuration Django
# =========================================================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HubEducator.settings")
django.setup()

# =========================================================
# Import des modèles
# =========================================================
from core.models import Course, User, Review

# =========================================================
# Recommandation pour un étudiant (basé sur level + catégorie + visible + reviews)
# =========================================================
def recommend_for_student(student, top_n=5):
    enrolled_courses = list(student.enrolled_courses.filter(visible=True))
    if not enrolled_courses:
        print(f"Aucun cours inscrit pour {student.username}")
        return []

    print(f"✅ {student.username} est inscrit à {len(enrolled_courses)} cours :")
    for c in enrolled_courses:
        print(f" - {c.title} (niveau: {c.level}, catégorie: {c.category.name if c.category else 'Autre'})")

    enrolled_ids = [c.id for c in enrolled_courses]
    all_recs = []

    for course in enrolled_courses:
        similar_courses = Course.objects.filter(
            visible=True,
            level=course.level,
            category=course.category
        ).exclude(id__in=enrolled_ids)

        for c in similar_courses:
            avg_rating = Review.objects.filter(course=c).aggregate(avg=Avg('rating'))['avg'] or 0.0
            # On ajoute un attribut temporaire à l'objet Course
            c.avg_rating = round(avg_rating, 1)
            all_recs.append(c)

    # Supprimer doublons et trier par note moyenne
    unique = []
    seen_ids = set()
    for c in sorted(all_recs, key=lambda x: x.avg_rating, reverse=True):
        if c.id not in seen_ids:
            seen_ids.add(c.id)
            unique.append(c)

    # Filtrer uniquement les cours avec note moyenne >= 3
    filtered_recs = [c for c in unique if c.avg_rating >= 3]

    return filtered_recs[:top_n]

# =========================================================
# Test local
# =========================================================
if __name__ == "__main__":
    student = User.objects.filter(username='yosrcharek').first()
    if student:
        recs = recommend_for_student(student)
        print(f"\n🎯 Recommandations pour {student.username} basées sur le niveau, la catégorie et la note des reviews :")
        if not recs:
            print("Aucune recommandation trouvée.")
        else:
            for r in recs:
                print(f" - {r.title} ({r.category.name if r.category else 'Autre'}, {r.level}, ⭐ {r.avg_rating})")
    else:
        print("Aucun étudiant trouvé.")

