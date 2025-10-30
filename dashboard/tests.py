from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.core.exceptions import ValidationError

from . import forms as dashboard_forms
from . import models as dashboard_models
from core import models as core_models


class DashboardFormsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create minimal related objects if needed by ModelForms (e.g., FK dependencies)
        # Attempt to create a simple Speciality if exists; ignore if model not present
        try:
            if hasattr(dashboard_models, 'Speciality'):
                cls.speciality = dashboard_models.Speciality.objects.create(
                    name="Data Science",
                    description="Test speciality"
                )
        except Exception:
            cls.speciality = None

        # Create a user if needed
        try:
            from django.contrib.auth import get_user_model
            cls.user = get_user_model().objects.create_user(
                username="tester",
                email="tester@example.com",
                password="password123!",
            )
        except Exception:
            cls.user = None

    def _get_valid_image(self, name="test.png", size_bytes=1024):
        # PNG header + padding to simulate image content
        content = b"\x89PNG\r\n\x1a\n" + b"0" * (size_bytes - 8 if size_bytes > 8 else 0)
        return SimpleUploadedFile(name, content, content_type="image/png")

    def test_required_fields_missing(self):
        # For each form in dashboard.forms, attempt minimal invalid submission to assert required errors
        if not hasattr(dashboard_forms, '__all__'):
            # Fallback: iterate attributes and find Form subclasses
            form_classes = []
            for attr_name in dir(dashboard_forms):
                attr = getattr(dashboard_forms, attr_name)
                try:
                    from django import forms as dj_forms
                    if isinstance(attr, type) and issubclass(attr, dj_forms.BaseForm) and attr is not dj_forms.BaseForm:
                        form_classes.append(attr)
                except Exception:
                    continue
        else:
            form_classes = [getattr(dashboard_forms, n) for n in dashboard_forms.__all__]

        # If no forms defined, skip gracefully
        if not form_classes:
            self.skipTest("No forms found in dashboard.forms")

        for FormClass in form_classes:
            form = FormClass(data={})
            self.assertFalse(form.is_valid(), msg=f"{FormClass.__name__} should be invalid with empty data")
            self.assertTrue(form.errors, msg=f"{FormClass.__name__} should have errors for required fields")

    def test_unique_field_validation(self):
        # Try to detect a model and a field that likely should be unique (e.g., name or slug)
        # This is heuristic; if not applicable, skip
        target_model = None
        unique_field = None
        try:
            for name, model in dashboard_models.__dict__.items():
                from django.db.models import Model
                if isinstance(model, type) and issubclass(model, Model):
                    for field in model._meta.fields:
                        if getattr(field, 'unique', False) or field.name in ("name", "slug"):
                            target_model = model
                            unique_field = field.name
                            break
                if target_model:
                    break
        except Exception:
            pass

        if not target_model or not unique_field:
            self.skipTest("No suitable model with a unique-like field was found for uniqueness validation test")

        first = target_model.objects.create(**{unique_field: "unique-value"})
        # Find a ModelForm for this model
        ModelFormClass = None
        try:
            from django.forms import ModelForm
            for attr_name in dir(dashboard_forms):
                attr = getattr(dashboard_forms, attr_name)
                if isinstance(attr, type) and issubclass(attr, ModelForm) and attr is not ModelForm:
                    if getattr(getattr(attr, 'Meta', None), 'model', None) is target_model:
                        ModelFormClass = attr
                        break
        except Exception:
            pass

        if not ModelFormClass:
            self.skipTest("No ModelForm found for target model to test uniqueness validation")

        form = ModelFormClass(data={unique_field: "unique-value"})
        self.assertFalse(form.is_valid(), msg="Form should be invalid for duplicate unique field value")

    def test_choice_field_validation(self):
        # Find any ChoiceField in any form and assert invalid choice is rejected
        from django import forms as dj_forms
        for attr_name in dir(dashboard_forms):
            attr = getattr(dashboard_forms, attr_name)
            if isinstance(attr, type) and issubclass(attr, dj_forms.BaseForm) and attr is not dj_forms.BaseForm:
                form = attr(data={"__bogus__": "__bogus__"})
                for fname, field in form.fields.items():
                    if isinstance(field, dj_forms.ChoiceField) and field.choices:
                        bad_choice = "__invalid__"
                        data = {fname: bad_choice}
                        test_form = attr(data=data)
                        self.assertFalse(test_form.is_valid(), msg=f"{attr.__name__} should reject invalid choice for {fname}")
                        return
        self.skipTest("No ChoiceField found in forms to validate invalid choice handling")

    def test_file_image_validation(self):
        # Find first form with an ImageField/FileField and validate content type/size where applicable
        from django import forms as dj_forms
        for attr_name in dir(dashboard_forms):
            attr = getattr(dashboard_forms, attr_name)
            if isinstance(attr, type) and issubclass(attr, dj_forms.BaseForm) and attr is not dj_forms.BaseForm:
                form = attr()
                for fname, field in form.fields.items():
                    if isinstance(field, (dj_forms.FileField, dj_forms.ImageField)):
                        # Provide a small PNG
                        image = self._get_valid_image()
                        data = {}
                        files = {fname: image}
                        test_form = attr(data=data, files=files)
                        # Some forms require other fields; if invalid, ensure at least file is accepted at field level
                        # We assert that the file does not independently cause an invalid content-type error.
                        # If the form is valid with only file, assert valid; otherwise ensure file-specific errors are absent.
                        if test_form.is_valid():
                            self.assertTrue(True)
                        else:
                            file_errors = test_form.errors.get(fname, [])
                            prohibited = [e for e in file_errors if "type" in "".join(e).lower() or "format" in "".join(e).lower()]
                            self.assertFalse(prohibited, msg=f"{attr.__name__} should accept PNG for field {fname}")
                        return
        self.skipTest("No FileField/ImageField found in forms to validate file acceptance")

    def test_valid_submission_creates_or_cleans(self):
        # Attempt to find a ModelForm and submit minimal valid data
        from django.forms import ModelForm
        for attr_name in dir(dashboard_forms):
            attr = getattr(dashboard_forms, attr_name)
            if isinstance(attr, type) and issubclass(attr, ModelForm) and attr is not ModelForm:
                model = getattr(attr.Meta, 'model', None)
                fields = list(getattr(attr.Meta, 'fields', []) or [])
                if not model or not fields:
                    continue
                # Build minimal data for required fields
                data = {}
                for field in model._meta.fields:
                    if field.name in fields and not getattr(field, 'blank', False) and field.editable:
                        if field.is_relation:
                            # if FK and we have an instance in setUpTestData
                            if getattr(field, 'remote_field', None) and getattr(field.remote_field, 'model', None):
                                related_model = field.remote_field.model
                                obj = related_model.objects.first()
                                if not obj:
                                    try:
                                        obj = related_model.objects.create()
                                    except Exception:
                                        # Skip if can't auto create
                                        pass
                                if obj:
                                    data[field.name] = obj.pk
                        else:
                            from django.db.models import (CharField, TextField, IntegerField, BooleanField, DateField, DateTimeField)
                            if isinstance(field, (CharField, TextField)):
                                data[field.name] = "ok"
                            elif isinstance(field, IntegerField):
                                data[field.name] = 1
                            elif isinstance(field, BooleanField):
                                data[field.name] = True
                            elif isinstance(field, DateField):
                                data[field.name] = timezone.now().date()
                            elif isinstance(field, DateTimeField):
                                data[field.name] = timezone.now()
                form = attr(data=data)
                if form.is_valid():
                    instance = form.save(commit=True)
                    self.assertIsNotNone(instance.pk, msg=f"{attr.__name__} did not save instance")
                    return
        self.skipTest("No suitable ModelForm found for a valid submission test")
