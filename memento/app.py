"""Flask application factory for Memento — multi-project docs portal."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, g, redirect, request, session
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import load_all

load_dotenv()


def create_app() -> Flask:
    """Create and configure the Flask application with all project instances."""
    instances_dir = os.getenv('MEMENTO_INSTANCES_DIR', 'instances')
    configs = load_all(instances_dir)

    if not configs:
        print(f"Error: no YAML configs found in {instances_dir}", file=sys.stderr)
        sys.exit(1)

    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/static',
    )
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'memento-dev-secret')
    app.config['MEMENTO_CONFIGS'] = configs

    dev_mode = os.getenv('MEMENTO_DEV', '') == '1'

    # Auth (global)
    from .auth import auth_bp, init_auth
    init_auth(app)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Per-project blueprints
    from .routes.docs import docs_bp
    from .routes.github import github_bp
    from .routes.admin import admin_bp
    app.register_blueprint(docs_bp, url_prefix='/<project>')
    app.register_blueprint(github_bp, url_prefix='/<project>')
    app.register_blueprint(admin_bp, url_prefix='/<project>')

    # Extract project from URL and resolve config before view dispatch
    @app.url_value_preprocessor
    def resolve_project(endpoint, values):
        if values:
            project = values.pop('project', None)
            if project:
                if project not in configs:
                    abort(404)
                g.project = project
                g.config = configs[project]

    # Dev mode: auto-login
    if dev_mode:
        @app.before_request
        def dev_auto_login():
            if not session.get('user'):
                session['user'] = {'email': 'dev@local', 'name': 'Dev', 'picture': ''}
                g.user_role = 'admin'

    # Root route: project selector (filtered by user access)
    @app.route('/')
    def root():
        user = session.get('user')
        if not dev_mode and not user:
            # Not logged in — redirect to login, then back here
            return redirect('/auth/login?next=/')

        if dev_mode:
            accessible = configs
        else:
            email = user['email']
            domain = email.split('@')[-1]
            accessible = {
                slug: cfg for slug, cfg in configs.items()
                if domain in cfg.auth.allowed_domains
                or email in cfg.auth.allowed_emails
                or email == cfg.auth.initial_admin
            }
        if len(accessible) == 1:
            return redirect(f'/{next(iter(accessible))}/')
        if not accessible:
            return _no_access_page()
        return _selector_page(accessible)

    @app.context_processor
    def inject_globals():
        return {
            'config': getattr(g, 'config', None),
            'project_slug': getattr(g, 'project', None),
            'user_role': getattr(g, 'user_role', None),
        }

    return app


def _selector_page(configs):
    cards = ''
    for slug, config in configs.items():
        color = config.branding.color
        title = config.branding.title
        cards += f'''
        <a href="/{slug}/" class="block border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow bg-white">
            <div class="font-semibold text-lg" style="color:{color}">{title}</div>
            <p class="text-sm text-gray-500 mt-1">Documentation portal</p>
        </a>'''

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Memento</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
body {{ font-family: 'Inter', system-ui, sans-serif; background: #f8fafc; margin: 0;
  min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; max-width: 800px; width: 100%; padding: 2rem; }}
h1 {{ text-align: center; color: #374151; font-size: 1.25rem; font-weight: 600; margin-bottom: 1.5rem; }}
</style></head>
<body>
<div>
<h1>Memento</h1>
<div class="grid">{cards}</div>
</div>
</body></html>'''


def _no_access_page():
    return '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Memento</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>body { font-family: 'Inter', system-ui, sans-serif; background: #f8fafc; margin: 0;
  min-height: 100vh; display: flex; align-items: center; justify-content: center; }
</style></head>
<body>
<div class="text-center">
<p style="color:#6b7280;margin-bottom:0.5rem">No projects available for your account.</p>
<a href="/auth/logout" style="color:#6366f1;font-size:0.875rem">Logout</a>
</div>
</body></html>''', 403


def main():
    """CLI entry point."""
    app = create_app()
    port = int(os.getenv('PORT', '5002'))
    app.run(debug=True, port=port)


if __name__ == '__main__':
    main()
