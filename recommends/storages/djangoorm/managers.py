from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType


class RecommendsManager(models.Manager):
    _ctypes = None

    @property
    def ctypes(self):
        if self._ctypes is None:
            values = ContentType.objects.values_list('app_label', 'model', 'id')
            ctypes = {}
            [ctypes.update({"%s.%s" % x[:2]: x[2]}) for x in values]
            self._ctypes = ctypes
        return self._ctypes

    def get_ctype_id_for_obj(self, obj):
        app_label = obj._meta.app_label
        module_name = obj._meta.module_name
        return self.ctypes["%s.%s" % (app_label, module_name)]

    def filter_for_model(self, model):
        ctype_id = self.get_ctype_id_for_obj(model)
        return self.filter(object_ctype=ctype_id)

    def filter_for_object(self, obj):
        return self.filter_for_model(obj).filter(object_id=obj.id)


class SimilarityManager(RecommendsManager):
    def filter_for_related_model(self, related_model):
        ctype_id = self.get_ctype_id_for_obj(related_model)
        return self.filter(related_object_ctype=ctype_id)

    def filter_for_related_object(self, related_obj):
        return self.filter_for_related_model(related_obj).filter(related_object_id=related_obj.id)

    def get_query_set(self):
        return super(SimilarityManager, self).get_query_set().filter(score__isnull=False)

    def get_or_create_for_objects(self, object_target, object_target_site, object_related, object_related_site):
        object_ctype_id = self.get_ctype_id_for_obj(object_target)
        object_id = object_target.id

        related_object_ctype_id = self.get_ctype_id_for_obj(object_related)
        related_object_id = object_related.id

        return self.get_or_create(
            object_ctype=object_ctype_id,
            object_id=object_id,
            object_site=object_target_site.id,
            related_object_ctype=related_object_ctype_id,
            related_object_id=related_object_id,
            related_object_site=object_related_site.id
        )

    def set_score_for_objects(self, object_target, object_target_site, object_related, object_related_site, score):
        result, created = self.get_or_create_for_objects(object_target, object_target_site, object_related, object_related_site)
        result.score = score
        result.save()
        return result

    def similar_to(self, obj, site=None, **kwargs):
        if site is None and 'related_object_site' not in kwargs:
            kwargs['related_object_site'] = settings.SITE_ID
        return self.filter_for_object(obj).filter(**kwargs)


class RecommendationManager(RecommendsManager):
    def get_query_set(self):
        return super(RecommendationManager, self).get_query_set().filter(score__isnull=False)

    def get_or_create_for_object(self, user, object_recommended, object_site):
        object_ctype_id = self.get_ctype_id_for_obj(object_recommended)
        object_id = object_recommended.id

        return self.get_or_create(
            object_ctype=object_ctype_id,
            object_id=object_id,
            object_site=object_site.id,
            user=user.id
        )

    def set_score_for_object(self, user, object_recommended, object_site, score):
        result, created = self.get_or_create_for_object(user, object_recommended, object_site)
        result.score = score
        result.save()
        return result
