from __future__ import unicode_literals, print_function
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response


__all__ = ["BulkCreateModelMixin", "BulkUpdateModelMixin", "BulkDestroyModelMixin"]


class BulkSaveModelMixin(object):
    def pre_bulk_save(self, objects):
        pass

    def post_bulk_save(self, objects, created=False):
        pass


class BulkCreateModelMixin(CreateModelMixin, BulkSaveModelMixin):
    """
    Either create a single or many model instances in bulk by using the
    Serializer's ``many=True`` ability from Django REST >= 2.2.5.

    .. note::
        This mixin uses the same method to create model instances
        as ``CreateModelMixin`` because both non-bulk and bulk
        requests will use ``POST`` request method.
    """

    def create(self, request, *args, **kwargs):
        bulk = isinstance(request.DATA, list)

        if not bulk:
            return super(BulkCreateModelMixin, self).create(request, *args, **kwargs)

        else:
            serializer = self.get_serializer(data=request.DATA, many=True)
            if serializer.is_valid():
                objects = serializer.object
                self.pre_bulk_save(objects)
                [self.pre_save(obj, bulk=True) for obj in objects]

                self.object = serializer.save(force_insert=True)

                [self.post_save(obj, created=True, bulk=True) for obj in self.object]
                self.post_bulk_save(self.object, created=True)

                return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkUpdateModelMixin(BulkSaveModelMixin):
    """
    Update model instances in bulk by using the Serializer's
    ``many=True`` ability from Django REST >= 2.2.5.
    """

    # def get_object(self):
    #     return self.get_queryset()

    def bulk_update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)

        # restrict the update to the filtered queryset
        serializer = self.get_serializer(self.filter_queryset(self.get_queryset()),
                                         data=request.DATA,
                                         many=True,
                                         partial=partial)

        if serializer.is_valid():
            try:
                objects = serializer.object
                self.pre_bulk_save(objects)
                [self.pre_save(obj, bulk=True) for obj in objects]
            except ValidationError as err:
                # full_clean on model instances may be called in pre_save
                # so we have to handle eventual errors.
                return Response(err.message_dict, status=status.HTTP_400_BAD_REQUEST)

            self.object = serializer.save(force_update=True)

            [self.post_save(obj, created=False, bulk=True) for obj in self.object]
            self.post_bulk_save(self.object, created=False)

            return Response(serializer.data, status=status.HTTP_200_OK)

        errors = serializer.errors
        for i, e in enumerate(request.DATA):
            identity = e.get('id', e.get('pk'))
            if identity:
                errors[i]['id'] = e.get('id', e.get('pk'))

        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_bulk_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.bulk_update(request, *args, **kwargs)


class BulkDestroyModelMixin(object):
    """
    Destroy model instances.
    """

    def allow_bulk_destroy(self, qs, filtered):
        """
        Hook to ensure that the bulk destroy should be allowed.

        By default this checks that the destroy is only applied to
        filtered querysets.
        """
        return qs is not filtered

    def bulk_destroy(self, request, *args, **kwargs):
        qs = self.get_queryset()
        objects = self.filter_queryset(qs)
        if not self.allow_bulk_destroy(qs, objects):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        self.pre_bulk_delete(objects)
        for obj in objects:
            self.pre_delete(obj, bulk=True)
            obj.delete()
            self.post_delete(obj, bulk=True)
        self.post_bulk_delete(objects)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def pre_bulk_delete(self, objects):
        pass

    def post_bulk_delete(self, objects):
        pass
