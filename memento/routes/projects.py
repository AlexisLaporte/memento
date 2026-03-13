"""Self-service project creation."""

import os

import httpx
from flask import Blueprint, abort, jsonify, redirect, request, session

from .. import db
from ..auth import requires_auth
from ..github_app import get_app_jwt, get_installation_token

projects_bp = Blueprint('projects', __name__)

_GITHUB_APP_NAME = os.getenv('GITHUB_APP_NAME', 'memento-document')
_INSTALL_URL = f'https://github.com/apps/{_GITHUB_APP_NAME}/installations/new'


def _list_installations() -> list[dict]:
    """List all GitHub App installations with account info."""
    try:
        resp = httpx.get(
            'https://api.github.com/app/installations',
            headers={'Authorization': f'Bearer {get_app_jwt()}', 'Accept': 'application/vnd.github+json'},
        )
        if resp.status_code != 200:
            return []
        return [
            {'id': inst['id'], 'account': inst['account']['login'], 'avatar': inst['account']['avatar_url']}
            for inst in resp.json()
        ]
    except Exception:
        return []


def _list_repos_for_installation(installation_id: int) -> list[dict]:
    """List repos accessible to a specific installation."""
    try:
        token = get_installation_token(installation_id)
        resp = httpx.get(
            'https://api.github.com/installation/repositories',
            headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'},
            params={'per_page': '100'},
        )
        if resp.status_code != 200:
            return []
        return [
            {'full_name': r['full_name'], 'name': r['name'], 'private': r['private']}
            for r in resp.json().get('repositories', [])
        ]
    except Exception:
        return []


@projects_bp.route('/new')
@requires_auth
def new_project_page():
    return f'''<!DOCTYPE html>
<html><head><title>New project — Memento</title><script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>body {{ font-family: 'Inter', system-ui, sans-serif; }}</style></head>
<body class="bg-gray-50 min-h-screen flex items-center justify-center">
<div class="w-full max-w-lg p-8">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-lg font-semibold text-gray-900">New project</h1>
        <a href="/" class="text-sm text-gray-500 hover:text-gray-700">Cancel</a>
    </div>
    <form method="post" action="/api/projects" class="bg-white rounded-lg shadow-sm p-6 space-y-4">
        <div>
            <label class="text-xs text-gray-500">GitHub Account</label>
            <select id="account" required class="block w-full text-sm border rounded px-3 py-2 mt-1">
                <option value="">Loading accounts...</option>
            </select>
            <p class="text-xs text-gray-400 mt-1">
                Don't see your account?
                <a href="{_INSTALL_URL}" target="_blank" class="text-indigo-600 hover:underline">Install the Memento GitHub App</a>
            </p>
        </div>
        <div>
            <label class="text-xs text-gray-500">Repository</label>
            <select name="repo" id="repo" required disabled class="block w-full text-sm border rounded px-3 py-2 mt-1 disabled:bg-gray-50">
                <option value="">Select an account first</option>
            </select>
        </div>
        <div>
            <label class="text-xs text-gray-500">Slug (URL identifier)</label>
            <input name="slug" id="slug" required placeholder="my-project" pattern="[a-z0-9-]+"
                   class="block w-full text-sm border rounded px-3 py-2 mt-1">
        </div>
        <div>
            <label class="text-xs text-gray-500">Title</label>
            <input name="title" id="title" required placeholder="My Project"
                   class="block w-full text-sm border rounded px-3 py-2 mt-1">
        </div>
        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="text-xs text-gray-500">Color</label>
                <input name="color" value="#6366F1" type="color" class="block h-9 w-20 border rounded mt-1">
            </div>
            <div>
                <label class="text-xs text-gray-500">Docs paths</label>
                <input name="docs_paths" value="docs" class="block w-full text-sm border rounded px-3 py-2 mt-1">
            </div>
        </div>
        <button class="w-full text-sm text-white py-2 rounded bg-indigo-600 hover:bg-indigo-700">Create project</button>
    </form>
</div>
<script>
const accountSel = document.getElementById('account');
const repoSel = document.getElementById('repo');
const slugInput = document.getElementById('slug');
const titleInput = document.getElementById('title');

fetch('/api/installations').then(r => r.json()).then(accounts => {{
    accountSel.innerHTML = '<option value="">Select your GitHub account</option>';
    accounts.forEach(a => {{
        accountSel.innerHTML += `<option value="${{a.id}}">${{a.account}}</option>`;
    }});
}});

accountSel.addEventListener('change', () => {{
    const id = accountSel.value;
    if (!id) {{ repoSel.disabled = true; repoSel.innerHTML = '<option>Select an account first</option>'; return; }}
    repoSel.disabled = true;
    repoSel.innerHTML = '<option>Loading repos...</option>';
    fetch(`/api/installations/${{id}}/repos`).then(r => r.json()).then(repos => {{
        repoSel.innerHTML = '<option value="">Select a repo</option>';
        repos.forEach(r => {{
            const lock = r.private ? ' 🔒' : '';
            repoSel.innerHTML += `<option value="${{r.full_name}}">${{r.name}}${{lock}}</option>`;
        }});
        repoSel.disabled = false;
    }});
}});

repoSel.addEventListener('change', () => {{
    const name = repoSel.value.split('/').pop() || '';
    if (!slugInput.value) slugInput.value = name.toLowerCase();
    if (!titleInput.value) titleInput.value = name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}});
</script>
</body></html>'''


@projects_bp.route('/api/installations')
@requires_auth
def api_installations():
    return jsonify(_list_installations())


@projects_bp.route('/api/installations/<int:installation_id>/repos')
@requires_auth
def api_installation_repos(installation_id):
    return jsonify(_list_repos_for_installation(installation_id))


@projects_bp.route('/api/projects', methods=['POST'])
@requires_auth
def create_project_route():
    user = session['user']
    slug = request.form.get('slug', '').strip().lower().replace(' ', '-')
    title = request.form.get('title', '').strip()
    repo_full_name = request.form.get('repo', '').strip()

    if not slug or not title or not repo_full_name or '/' not in repo_full_name:
        abort(400)

    if db.get_project(slug):
        abort(409)

    # Find the installation that has access
    owner = repo_full_name.split('/')[0]
    installations = _list_installations()
    installation_id = None
    for inst in installations:
        if inst['account'].lower() == owner.lower():
            installation_id = inst['id']
            break

    if not installation_id:
        return f'''<!DOCTYPE html>
<html><head><title>Error</title><script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>body {{ font-family: 'Inter', system-ui, sans-serif; }}</style></head>
<body class="bg-gray-50 min-h-screen flex items-center justify-center">
<div class="text-center max-w-md">
    <p class="text-red-500 font-medium mb-2">GitHub App not installed</p>
    <p class="text-sm text-gray-500 mb-4">
        The Memento GitHub App is not installed on <strong>{owner}</strong>.<br>
        <a href="{_INSTALL_URL}" class="text-indigo-600 hover:underline">Install it here</a>.
    </p>
    <a href="/new" class="text-sm text-indigo-600 hover:underline">Back</a>
</div></body></html>''', 400

    docs_paths = [p.strip() for p in request.form.get('docs_paths', 'docs').split(',') if p.strip()]
    color = request.form.get('color', '#6366F1').strip()

    db.create_project(
        slug=slug, title=title, repo_full_name=repo_full_name,
        installation_id=installation_id, owner_email=user['email'],
        docs_paths=docs_paths, color=color,
    )
    return redirect(f'/{slug}/')
