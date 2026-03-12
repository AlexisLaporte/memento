"""Admin routes for per-project user management."""

from flask import Blueprint, g, redirect, request, url_for

from ..auth import (
    requires_admin, get_table_name,
    _list_users, _set_role, _invite_user,
)

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@requires_admin
def admin_page():
    table_name = get_table_name(g.project)
    users = _list_users(table_name)
    color = g.config.branding.color
    title = g.config.branding.title
    project = g.project

    rows = ''
    for u in users:
        role_cls = {
            'admin': 'bg-purple-100 text-purple-700',
            'member': 'bg-green-100 text-green-700',
            'blocked': 'bg-red-100 text-red-700',
        }.get(u['role'], 'bg-gray-100 text-gray-600')
        options = ''.join(
            f'<option value="{r}" {"selected" if r == u["role"] else ""}>{r}</option>'
            for r in ('blocked', 'member', 'admin')
        )
        rows += f'''<tr class="border-t border-gray-100">
            <td class="px-4 py-3 text-sm">{u['email']}</td>
            <td class="px-4 py-3 text-sm text-gray-600">{u['name'] or ''}</td>
            <td class="px-4 py-3"><span class="text-xs px-2 py-0.5 rounded-full {role_cls}">{u['role']}</span></td>
            <td class="px-4 py-3">
                <form method="post" action="/{project}/admin/{u['email']}/role" class="flex gap-2 items-center">
                    <select name="role" class="text-xs border rounded px-2 py-1">{options}</select>
                    <button class="text-xs text-white px-2 py-1 rounded hover:opacity-90" style="background:{color}">Save</button>
                </form>
            </td>
        </tr>'''

    return f'''<!DOCTYPE html>
<html><head><title>Admin - {title}</title><script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>body {{ font-family: 'Inter', system-ui, sans-serif; }}</style></head>
<body class="bg-gray-50 min-h-screen p-8">
<div class="max-w-3xl mx-auto">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-lg font-semibold text-gray-900">User Management</h1>
        <a href="/{project}/" class="text-sm hover:underline" style="color:{color}">Back to docs</a>
    </div>
    <div class="bg-white rounded-lg shadow-sm overflow-hidden mb-6">
        <table class="w-full">
            <thead class="bg-gray-50 text-xs text-gray-500 uppercase">
                <tr><th class="px-4 py-2 text-left">Email</th><th class="px-4 py-2 text-left">Name</th>
                <th class="px-4 py-2 text-left">Role</th><th class="px-4 py-2 text-left">Action</th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    <div class="bg-white rounded-lg shadow-sm p-4">
        <h2 class="text-sm font-semibold text-gray-900 mb-3">Invite user</h2>
        <form method="post" action="/{project}/admin/invite" class="flex gap-2 items-end">
            <div><label class="text-xs text-gray-500">Email</label>
            <input name="email" type="email" required placeholder="user@example.com" class="block text-sm border rounded px-3 py-1.5 w-64"></div>
            <div><label class="text-xs text-gray-500">Name (optional)</label>
            <input name="name" type="text" placeholder="First Last" class="block text-sm border rounded px-3 py-1.5 w-48"></div>
            <button class="text-sm text-white px-4 py-1.5 rounded hover:opacity-90" style="background:{color}">Invite</button>
        </form>
    </div>
</div></body></html>'''


@admin_bp.route('/admin/invite', methods=['POST'])
@requires_admin
def admin_invite():
    table_name = get_table_name(g.project)
    email = request.form.get('email', '').strip().lower()
    name = request.form.get('name', '').strip()
    if email:
        _invite_user(table_name, email, name)
    return redirect(url_for('admin.admin_page', project=g.project))


@admin_bp.route('/admin/<path:email>/role', methods=['POST'])
@requires_admin
def admin_set_role(email):
    table_name = get_table_name(g.project)
    role = request.form.get('role')
    _set_role(table_name, email, role)
    return redirect(url_for('admin.admin_page', project=g.project))
