import re

with open("core/views.py", "r") as f:
    content = f.read()

# 1. Fix N+1 in dashboard
content = content.replace(
    'periods = Period.objects.all()[:6]',
    'periods = Period.objects.prefetch_related("charges__charge_type", "presences__resident__user", "wifi_contributions__contributor", "payments__resident__user").order_by("-annee", "-mois")[:6]'
)

# 2. Add period.cloturee check
def add_cloturee_check(view_name, require_charge_id=False):
    global content
    
    if view_name == 'presence_update':
        find_str = '    period = get_object_or_404(Period, pk=pk)\n    if request.method == "POST":'
        replace_str = '    period = get_object_or_404(Period, pk=pk)\n    if period.cloturee:\n        messages.error(request, "Cette période est clôturée.")\n        return redirect("period_detail", pk=period.pk)\n    if request.method == "POST":'
    elif require_charge_id and view_name in ['charge_edit', 'charge_delete']:
        find_str = f'def {view_name}(request, pk, charge_id):\n    period = get_object_or_404(Period, pk=pk)\n    charge = get_object_or_404(Charge, pk=charge_id, period=period)'
        replace_str = f'def {view_name}(request, pk, charge_id):\n    period = get_object_or_404(Period, pk=pk)\n    if period.cloturee:\n        messages.error(request, "Cette période est clôturée.")\n        return redirect("period_detail", pk=period.pk)\n    charge = get_object_or_404(Charge, pk=charge_id, period=period)'
    elif require_charge_id and view_name in ['wifi_contribution_edit', 'wifi_contribution_delete']:
        find_str = f'def {view_name}(request, pk, wc_id):\n    period = get_object_or_404(Period, pk=pk)\n    wc = get_object_or_404(WifiContribution, pk=wc_id, period=period)'
        replace_str = f'def {view_name}(request, pk, wc_id):\n    period = get_object_or_404(Period, pk=pk)\n    if period.cloturee:\n        messages.error(request, "Cette période est clôturée.")\n        return redirect("period_detail", pk=period.pk)\n    wc = get_object_or_404(WifiContribution, pk=wc_id, period=period)'
    elif view_name == 'charge_add' or view_name == 'wifi_contribution_add':
        find_str = f'def {view_name}(request, pk):\n    period = get_object_or_404(Period, pk=pk)'
        replace_str = f'def {view_name}(request, pk):\n    period = get_object_or_404(Period, pk=pk)\n    if period.cloturee:\n        messages.error(request, "Cette période est clôturée.")\n        return redirect("period_detail", pk=period.pk)'
    elif view_name == 'payment_tracking':
        find_str = f'def {view_name}(request, pk):\n    """Page d\'administration : cocher qui a payé, combien, et suivre les paiements."""\n    period = get_object_or_404(Period, pk=pk)'
        replace_str = f'def {view_name}(request, pk):\n    """Page d\'administration : cocher qui a payé, combien, et suivre les paiements."""\n    period = get_object_or_404(Period, pk=pk)\n    if period.cloturee and request.method == "POST":\n        messages.error(request, "Cette période est clôturée.")\n        return redirect("period_detail", pk=period.pk)'

    content = content.replace(find_str, replace_str)

add_cloturee_check('charge_add')
add_cloturee_check('charge_edit', True)
add_cloturee_check('charge_delete', True)
add_cloturee_check('presence_update')
add_cloturee_check('wifi_contribution_add')
add_cloturee_check('wifi_contribution_edit', True)
add_cloturee_check('wifi_contribution_delete', True)
add_cloturee_check('payment_tracking')

# 3. Change permissions
# A list of views to change from @login_required to @staff_member_required
staff_views = [
    'charge_add', 'charge_edit', 'charge_delete',
    'presence_update',
    'wifi_contribution_add', 'wifi_contribution_edit', 'wifi_contribution_delete',
    'contributor_list', 'contributor_edit', 'contributor_delete',
    'charge_type_list', 'charge_type_edit', 'charge_type_delete',
    'period_pdf_all'
]

for v in staff_views:
    old_func_def = f'@login_required\ndef {v}('
    new_func_def = f'@staff_member_required\ndef {v}('
    content = content.replace(old_func_def, new_func_def)

with open("core/views.py", "w") as f:
    f.write(content)

