# -*- coding: utf-8 -*- vim:fileencoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

# Copyright © 2010-2012 Greek Research and Technology Network (GRNET S.A.)
# Copyright © 2012 Faidon Liambotis
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND ISC DISCLAIMS ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL ISC BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
# USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
'''
Compat functions for old versions of Django
'''

from django import VERSION as DJANGO_VERSION

if DJANGO_VERSION[:2] >= (1, 3):
    from django.shortcuts import render
else:
    # Copied from Django 1.3
    #
    # Copyright (c) Django Software Foundation and individual contributors.
    # All rights reserved.

    from django.template import loader, RequestContext
    from django.http import HttpResponse

    def render(request, *args, **kwargs):
        """
        Returns a HttpResponse whose content is filled with the result of calling
        django.template.loader.render_to_string() with the passed arguments.
        Uses a RequestContext by default.
        """
        httpresponse_kwargs = {
            'content_type': kwargs.pop('content_type', None),
            'status': kwargs.pop('status', None),
        }

        if 'context_instance' in kwargs:
            context_instance = kwargs.pop('context_instance')
            if kwargs.get('current_app', None):
                raise ValueError('If you provide a context_instance you must '
                                 'set its current_app before calling render()')
        else:
            current_app = kwargs.pop('current_app', None)
            context_instance = RequestContext(request, current_app=current_app)

        kwargs['context_instance'] = context_instance

        return HttpResponse(loader.render_to_string(*args, **kwargs),
                            **httpresponse_kwargs)
