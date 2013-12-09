import unittest

from django import http
from django.contrib.contenttypes.models import ContentType
from django.forms.models import modelform_factory

import autocomplete_light

from .apps.basic.admin import *
from .apps.basic.models import *
from .apps.basic.forms import *


class BaseModelFormTestCase(unittest.TestCase):
    def setUp(self):
        self.james = self.model_class.objects.create(name='James')
        self.janis = self.model_class.objects.create(name='Janis')
        self.test_instance = self.james

    def tearDown(self):
        self.model_class.objects.all().delete()


class ModelFormBaseTestCase(BaseModelFormTestCase):
    widget_class = autocomplete_light.ChoiceWidget

    def form_value(self, model):
        return 'relation=%s' % model.pk

    def field_value(self, model):
        return getattr(model, 'relation')

    def assertExpectedFormField(self, name='relation'):
        self.assertInForm(name)
        self.assertTrue(isinstance(self.form.fields[name],
            self.field_class))
        self.assertTrue(isinstance(self.form.fields[name].widget,
            self.widget_class))
        self.assertEqual(self.form.fields[name].autocomplete.__name__,
                self.autocomplete_name)

    def assertInForm(self, name):
        self.assertIn(name, self.form.fields)

    def assertNotInForm(self, name):
        self.assertNotIn(name, self.form.fields)

    def assertIsAutocomplete(self, name):
        self.assertIsInstance(self.form.fields[name],
                autocomplete_light.FieldBase)

    def assertNotIsAutocomplete(self, name):
        self.assertNotIsInstance(self.form.fields[name],
                autocomplete_light.FieldBase)

    def test_appropriate_field_on_modelform(self):
        self.form = self.model_form_class()

        self.assertExpectedFormField()
        self.assertIsAutocomplete('noise')

    def test_appropriate_field_with_modelformfactory(self):
        form_class = modelform_factory(self.model_class,
                form=self.model_form_class)
        self.form = form_class()

        self.assertExpectedFormField()
        self.assertIsAutocomplete('noise')

    def test_appropriate_field_on_modelform_with_formfield_callback(self):
        # This tests what django admin does
        def cb(f, **kwargs):
            return f.formfield(**kwargs)

        form_class = modelform_factory(self.model_class,
                form=self.model_form_class, formfield_callback=cb)
        self.form = form_class()

        self.assertExpectedFormField()
        self.assertIsAutocomplete('noise')
        self.assertInForm('name')

    def test_meta_exclude_name(self):
        class ModelForm(autocomplete_light.ModelForm):
            class Meta:
                model = self.model_class
                exclude = ('name',)

        self.form = ModelForm()

        self.assertExpectedFormField()
        self.assertNotInForm('name')
        self.assertIsAutocomplete('noise')

    def test_meta_exclude_relation(self):
        class ModelForm(autocomplete_light.ModelForm):
            class Meta:
                model = self.model_class
                exclude = ['relation']

        self.form = ModelForm()

        self.assertInForm('name')
        self.assertIsAutocomplete('noise')
        self.assertNotInForm('relation')

    def test_meta_fields_name(self):
        class ModelForm(autocomplete_light.ModelForm):
            class Meta:
                model = self.model_class
                fields = ['name']

        self.form = ModelForm()

        self.assertInForm('name')
        self.assertNotInForm('noise')
        self.assertNotInForm('relation')

    def test_meta_fields_relation(self):
        class ModelForm(autocomplete_light.ModelForm):
            class Meta:
                model = self.model_class
                fields = ['relation']

        self.form = ModelForm()

        self.assertExpectedFormField()
        self.assertNotInForm('name')
        self.assertNotInForm('noise')

    def test_meta_autocomplete_fields(self):
        class ModelForm(autocomplete_light.ModelForm):
            class Meta:
                model = self.model_class
                autocomplete_fields = ['relation']

        self.form = ModelForm()

        self.assertExpectedFormField()
        self.assertNotIsAutocomplete('noise')
        self.assertInForm('name')

    def test_meta_autocomplete_exclude(self):
        class ModelForm(autocomplete_light.ModelForm):
            class Meta:
                model = self.model_class
                autocomplete_exclude = ['relation']

        self.form = ModelForm()

        self.assertInForm('name')
        self.assertNotIsAutocomplete('relation')
        self.assertIsAutocomplete('noise')

    def test_modelform_factory(self):
        self.form = autocomplete_light.modelform_factory(self.model_class)()

        self.assertExpectedFormField()

    def test_modelform_factory_fields_relation(self):
        self.form = autocomplete_light.modelform_factory(self.model_class,
                fields=['relation'])()

        self.assertExpectedFormField()
        self.assertNotInForm('name')
        self.assertNotInForm('noise')

    def test_modelform_factory_exclude_relation(self):
        self.form = autocomplete_light.modelform_factory(self.model_class,
                exclude=['relation'])()

        self.assertNotInForm('relation')
        self.assertInForm('name')
        self.assertIsAutocomplete('noise')

    def test_modelform_factory_autocomplete_fields_relation(self):
        self.form = autocomplete_light.modelform_factory(self.model_class,
                autocomplete_fields=['relation'])()

        self.assertExpectedFormField()
        self.assertNotIsAutocomplete('noise')
        self.assertInForm('name')

    def test_modelform_factory_autocomplete_exclude_relation(self):
        self.form = autocomplete_light.modelform_factory(self.model_class,
                autocomplete_exclude=['relation'])()

        self.assertNotIsAutocomplete('relation')
        self.assertInForm('name')
        self.assertIsAutocomplete('noise')

    def test_modelform_factory_fields_name(self):
        self.form = autocomplete_light.modelform_factory(self.model_class,
                fields=['name'])()

        self.assertInForm('name')
        self.assertNotInForm('relation')
        self.assertNotInForm('noise')

    def test_modelform_factory_exclude_name(self):
        self.form = autocomplete_light.modelform_factory(self.model_class,
                exclude=['name'])()

        self.assertNotInForm('name')
        self.assertExpectedFormField()
        self.assertIsAutocomplete('noise')

    def test_empty_registry(self):
        registry = autocomplete_light.AutocompleteRegistry()

        class ModelForm(autocomplete_light.ModelForm):
            relation = self.field_class(registry=registry,
                autocomplete=registry.register(self.model_class))
            relation2 = self.field_class(registry=registry,
                autocomplete=registry.register(self.model_class))

            class Meta:
                model = self.model_class

        self.form = ModelForm()

        self.assertExpectedFormField()
        self.assertExpectedFormField('relation2')

    def test_create_with_relation(self):
        form = self.model_form_class(http.QueryDict(
            'name=test&%s' % self.form_value(self.janis)))

        self.assertTrue(form.is_valid())

        result = form.save()
        self.assertEqual(self.field_value(result), self.janis)

    def test_add_relation(self):
        form = self.model_form_class(http.QueryDict(
            'name=test&%s' % self.form_value(self.janis)),
            instance=self.test_instance)

        self.assertTrue(form.is_valid())

        result = form.save()
        self.assertEqual(self.field_value(result), self.janis)


class GenericModelFormTestCaseMixin(object):
    autocomplete_name = 'A'

    def test_meta_autocomplete_exclude(self):
        class ModelForm(autocomplete_light.ModelForm):
            class Meta:
                model = self.model_class
                autocomplete_exclude = ['relation']

        self.form = ModelForm()

        self.assertNotInForm('relation')
        self.assertInForm('name')
        self.assertIsAutocomplete('noise')

    def test_modelform_factory_autocomplete_exclude_relation(self):
        self.form = autocomplete_light.modelform_factory(self.model_class,
                autocomplete_exclude=['relation'])()

        self.assertNotInForm('relation')
        self.assertInForm('name')
        self.assertIsAutocomplete('noise')

    def test_empty_registry(self):
        registry = autocomplete_light.AutocompleteRegistry()

        class ModelForm(autocomplete_light.ModelForm):
            relation = self.field_class(registry=registry,
                autocomplete=registry.register(autocomplete_light.AutocompleteGenericBase,
                    choices=[self.model_class.objects.all()],
                    search_fields=['name']))

            class Meta:
                model = self.model_class

        self.form = ModelForm()

        self.assertExpectedFormField()
        self.assertInForm('name')
        self.assertIsAutocomplete('noise')

    def form_value(self, model):
        return 'relation=%s-%s' % (ContentType.objects.get_for_model(model).pk, model.pk)


class MultipleRelationTestCaseMixin(ModelFormBaseTestCase):
    widget_class = autocomplete_light.MultipleChoiceWidget

    def field_value(self, model):
        return super(MultipleRelationTestCaseMixin, self).field_value(model).all()[0]


class FkModelFormTestCase(ModelFormBaseTestCase):
    model_class = FkModel
    model_form_class = FkModelForm
    field_class = autocomplete_light.ModelChoiceField
    autocomplete_name = 'FkModelAutocomplete'


class OtoModelFormTestCase(ModelFormBaseTestCase):
    model_class = OtoModel
    model_form_class = OtoModelForm
    field_class = autocomplete_light.ModelChoiceField
    autocomplete_name = 'OtoModelAutocomplete'


class GfkModelFormTestCase(GenericModelFormTestCaseMixin,
        ModelFormBaseTestCase):
    model_class = GfkModel
    model_form_class = GfkModelForm
    field_class = autocomplete_light.GenericModelChoiceField


class MtmModelFormTestCase(MultipleRelationTestCaseMixin, ModelFormBaseTestCase):
    model_class = MtmModel
    model_form_class = MtmModelForm
    field_class = autocomplete_light.ModelMultipleChoiceField
    autocomplete_name = 'MtmModelAutocomplete'


try:
    from taggit.models import Tag
except ImportError:
    class TaggitModelFormTestCase(object):
        pass
else:
    class TaggitModelFormTestCase(ModelFormBaseTestCase):
        model_class = TaggitModel
        model_form_class = TaggitModelForm
        field_class = autocomplete_light.TaggitField
        widget_class = autocomplete_light.TaggitWidget
        autocomplete_name = 'TagAutocomplete'

        def setUp(self):
            self.james = 'james'
            self.janis = 'janis'
            self.test_instance = self.model_class.objects.create(name='test')

        def form_value(self, model):
            return 'relation=%s' % model

        def field_value(self, model):
            return model.relation.all().values_list('name', flat=True)[0]

        def test_empty_registry(self):
            pass


try:
    import genericm2m
except ImportError:
    class GmtmModelFormTestCase(object):
        pass
else:
    class GmtmModelFormTestCase(MultipleRelationTestCaseMixin,
            GenericModelFormTestCaseMixin,
            ModelFormBaseTestCase):
        model_class = GmtmModel
        model_form_class = GmtmModelForm
        field_class = autocomplete_light.GenericModelMultipleChoiceField

        def field_value(self, model):
            return getattr(model, 'relation').all().generic_objects()[0]