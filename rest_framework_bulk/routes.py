from __future__ import unicode_literals, print_function

import copy

from rest_framework.routers import SimpleRouter
from rest_framework_extensions.routers import ExtendedSimpleRouter


__all__ = ['BulkRouter', 'BulkExtendedSimpleRouter']


def patch(base_routes):
    routes = copy.deepcopy(base_routes)
    routes[0].mapping.update({
        'put': 'bulk_update',
        'patch': 'partial_bulk_update',
        'delete': 'bulk_destroy',
    })
    return routes


class BulkRouter(SimpleRouter):
    """
    Map http methods to actions defined on the bulk mixins.
    """
    routes = patch(SimpleRouter.routes)


class BulkExtendedSimpleRouter(ExtendedSimpleRouter):
    """
    Map http methods to actions defined on the bulk mixins.
    """
    routes = patch(ExtendedSimpleRouter.routes)
