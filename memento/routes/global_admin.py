"""Global admin — super admin oversight + GitHub App webhook."""

import hashlib
import hmac
import os

from flask import Blueprint, abort, jsonify, request

from ..auth import requires_super_admin
from .. import db

global_admin_bp = Blueprint('global_admin', __name__)


# ─── Super Admin API ─────────────────────────────────────────────────────────

@global_admin_bp.route('/api/admin/projects')
@requires_super_admin
def api_admin_projects():
    projects = db.load_projects()
    return jsonify([{
        "slug": slug,
        "title": p.title,
        "color": p.color,
        "repo_full_name": p.repo_full_name,
        "owner_email": p.owner_email,
    } for slug, p in projects.items()])


@global_admin_bp.route('/api/admin/projects/<slug>', methods=['DELETE'])
@requires_super_admin
def api_admin_delete_project(slug):
    db.delete_project(slug)
    return jsonify({"ok": True})


# ─── Webhook ─────────────────────────────────────────────────────────────────

@global_admin_bp.route('/api/webhook/github', methods=['POST'])
def webhook():
    """Handle GitHub App webhook events."""
    secret = os.getenv('GITHUB_APP_WEBHOOK_SECRET', '')
    if secret:
        signature = request.headers.get('X-Hub-Signature-256', '')
        expected = 'sha256=' + hmac.new(
            secret.encode(), request.data, hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            abort(403)

    event = request.headers.get('X-GitHub-Event', '')
    payload = request.get_json()

    if event == 'installation' and payload:
        action = payload.get('action')
        if action == 'created':
            pass

    return jsonify({"ok": True})
