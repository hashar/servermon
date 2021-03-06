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
updates views module
'''


from django.shortcuts import get_list_or_404, get_object_or_404
from servermon.compat import render
from django.db.models import Count, Sum
from servermon.puppet.models import Host
from servermon.updates.models import Package, Update
from servermon.hwdoc.models import Equipment
from IPy import IP

def hostlist(request):
    hosts = Host.objects.annotate(update_count=Count('update'),
                                  security_count=Sum('update__is_security'))
    return render(request, 'hostlist.html', {'hosts': hosts })

def packagelist(request):
    packages = Package.objects.annotate(host_count=Count('hosts'),
                                        security_count=Sum('update__is_security'))
    return render(request, 'packagelist.html', {'packages': packages })

def package(request, packagename):
    # there may be multiple Package with same name but different sourcename
    package = get_list_or_404(Package, name=packagename)[0]

    updates = package.update_set.order_by('host__name')
    if "plain" in request.GET:
        return render(request, "package.txt", {"updates": updates}, content_type="text/plain")
    return render(request, 'packageview.html', {'package': package, 'updates': updates})

def host(request, hostname):
    host = get_object_or_404(Host, name=hostname)

    updates = []
    system = []
    location = []

    try:
        iflist = host.get_fact_value('interfaces').split(',')
    except AttributeError:
        iflist = []

    # Network part
    interfaces = []
    for iface in iflist:
        d = {}
        iface1 = iface.replace(':','_')
        mac = host.get_fact_value('macaddress_%s' % iface1)
        ip = host.get_fact_value('ipaddress_%s' % iface1)
        netmask = host.get_fact_value('netmask_%s' % iface1)
        ip6 = host.get_fact_value('ipaddress6_%s' % iface1)

        d = { 'iface': iface,
              'mac': mac }

        if netmask and ip:
            d['ipaddr'] = "%s/%d" % (ip, IP(ip).make_net(netmask).prefixlen())

        if ip6:
            d['ipaddr6'] = ip6

        interfaces.append(d)

    # System part
    fields = [
        ('bios_date', 'BIOS Date'),
        ('bios_version', 'BIOS Version'),
        ('manufacturer', 'System Vendor'),
        ('productname', 'Model'),
        ('serialnumber', 'Serial number'),
        ('processorcount', 'Processors'),
        ('architecture', 'Architecture'),
        ('virtual', 'Machine Type'),
        ('uptime', 'Uptime'),
    ]

    for fact, label in fields:
        system.append({ 'name': label, 'value': host.get_fact_value(fact) })

    system.append({ 'name': 'Processor type',
        'value': ", ".join([ p['value'] for p in host.factvalue_set.filter(fact_name__name__startswith='processor').exclude(fact_name__name='processorcount').values('value').distinct() ]),
    })

    system.append({ 'name': 'Operating System',
        'value': "%s %s" % (host.get_fact_value('operatingsystem'), host.get_fact_value('operatingsystemrelease'))
        })
    system.append({ 'name': 'Memory',
        'value': "%s (%s free)" % (host.get_fact_value('memorytotal'), host.get_fact_value('memoryfree'))
        })

    system.append({ 'name': 'Puppet classes',
        'value': ", ".join([ f.value for f in  host.factvalue_set.filter(fact_name__name='puppetclass') ])
        })

    # Location info part
    try:
        eq = Equipment.objects.get(serial=host.get_fact_value('serialnumber'))
        location.append({ 'name': 'Rack Unit',
            'value': "%s" % (
                eq.unit
                )
            })
        location.append({ 'name': 'Rack',
            'value': "%s" % (
                eq.rack
                )
            })
        location.append({ 'name': 'Rack Row',
            'value': "%s" % (
                eq.rack.rackposition.rr
                )
            })
        location.append({ 'name': 'IPMI Method',
            'value': "%s" % (
                eq.servermanagement.method
                )
            })
        location.append({ 'name': 'IPMI Hostname',
            'value': "%s" % (
                eq.servermanagement.hostname
                )
            })
        location.append({ 'name': 'IPMI MAC',
            'value': "%s" % (
                eq.servermanagement.mac
                )
            })
        location.append({ 'name': 'Datacenter',
            'value': "%s" % (
                eq.rack.rackposition.rr.dc
                )
            })
    except:
        location.append({ 'name': 'Location',
            'value': "%s" % (
                'No location information found'
                )
            })

    # Updates info
    updates = Update.objects.filter(host=host).order_by('package__name')
    updates = updates.select_related()

    return render(request, 'hostview.html', {
        'host': host,
        'updates': updates,
        'interfaces': interfaces,
        'system': system,
        'location': location,
        })
