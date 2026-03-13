"""Flask application factory for Memento — multi-project docs portal."""

import os

from dotenv import load_dotenv
from flask import Flask, abort, g, redirect, request, session
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/static',
    )
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'memento-dev-secret')

    dev_mode = os.getenv('MEMENTO_DEV', '') == '1'
    _branch_cache: dict[str, str] = {}

    # Ensure DB schema
    from .db import ensure_schema
    ensure_schema()

    # Auth (global)
    from .auth import auth_bp, has_project_access, init_auth
    init_auth(app)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Per-project blueprints
    from .routes.docs import docs_bp
    from .routes.github import github_bp
    from .routes.settings import settings_bp
    app.register_blueprint(docs_bp, url_prefix='/<project>')
    app.register_blueprint(github_bp, url_prefix='/<project>')
    app.register_blueprint(settings_bp, url_prefix='/<project>')

    # Global: admin, projects, webhook
    from .routes.global_admin import global_admin_bp
    from .routes.projects import projects_bp
    app.register_blueprint(global_admin_bp)
    app.register_blueprint(projects_bp)

    # Extract project from URL and resolve config
    @app.url_value_preprocessor
    def resolve_project(endpoint, values):
        if values:
            project = values.pop('project', None)
            if project:
                from .db import get_project
                config = get_project(project)
                if not config:
                    if dev_mode:
                        config = _dev_config(project)
                    else:
                        abort(404)
                # Resolve default branch (cached)
                if config.repo_full_name and config.installation_id:
                    if project not in _branch_cache:
                        try:
                            from .github_app import github_api
                            repo_info = github_api(config.installation_id, f'/repos/{config.repo_full_name}')
                            _branch_cache[project] = repo_info.get('default_branch', 'main')
                        except Exception:
                            _branch_cache[project] = 'main'
                    config.default_branch = _branch_cache[project]
                g.project = project
                g.config = config

    # Dev mode: auto-login
    if dev_mode:
        @app.before_request
        def dev_auto_login():
            if not session.get('user'):
                session['user'] = {
                    'email': 'dev@local', 'name': 'Dev', 'picture': '',
                }
                g.user_role = 'admin'

    # Root route: project dashboard
    @app.route('/')
    def root():
        user = session.get('user')
        if not dev_mode and not user:
            return _welcome_page()

        from .db import load_projects, load_projects_for_user
        if dev_mode:
            projects = load_projects()
        else:
            projects = load_projects_for_user(user['email'])

        return _dashboard_page(projects, user)

    @app.context_processor
    def inject_globals():
        return {
            'config': getattr(g, 'config', None),
            'project_slug': getattr(g, 'project', None),
            'user_role': getattr(g, 'user_role', None),
        }

    return app


def _dev_config(project: str):
    from .config import ProjectConfig
    return ProjectConfig(slug=project, title=project.capitalize())


def _welcome_page():
    return '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Memento — Documentation portal for your team</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<style>body { font-family: 'Inter', system-ui, sans-serif; }</style>
</head>
<body class="bg-gray-50 min-h-screen">

<!-- Nav -->
<nav class="max-w-4xl mx-auto flex justify-between items-center px-6 py-6">
    <span class="text-lg font-bold text-gray-900 tracking-tight">Memento</span>
    <a href="/auth/login?next=/" class="text-sm font-medium text-white bg-indigo-500 px-4 py-2 rounded-lg hover:bg-indigo-600 transition">Sign in</a>
</nav>

<!-- Hero -->
<section class="max-w-4xl mx-auto px-6 pt-16 pb-20 text-center">
    <h1 class="text-4xl font-bold text-gray-900 mb-4">Your docs, always accessible</h1>
    <p class="text-lg text-gray-500 max-w-2xl mx-auto mb-8">
        Memento turns your GitHub markdown into a clean documentation portal.
        Invite your team, control access, and let AI read your docs too.
    </p>
    <a href="/auth/login?next=/" class="inline-flex items-center gap-2 text-sm font-medium text-white bg-indigo-500 px-6 py-3 rounded-lg hover:bg-indigo-600 transition">
        Get started
    </a>
</section>

<!-- Features -->
<section class="max-w-4xl mx-auto px-6 pb-20">
    <div class="grid md:grid-cols-3 gap-6">
        <div class="bg-white rounded-xl p-6 shadow-sm">
            <div class="text-2xl mb-3">&#128194;</div>
            <h3 class="font-semibold text-gray-900 mb-1">GitHub-powered</h3>
            <p class="text-sm text-gray-500">Connect a GitHub repo and Memento renders your markdown docs with a clean UI. No build step, no config files.</p>
        </div>
        <div class="bg-white rounded-xl p-6 shadow-sm">
            <div class="text-2xl mb-3">&#128101;</div>
            <h3 class="font-semibold text-gray-900 mb-1">Team access control</h3>
            <p class="text-sm text-gray-500">Invite members by email, allow entire domains, and manage roles. Each project has its own permissions.</p>
        </div>
        <div class="bg-white rounded-xl p-6 shadow-sm">
            <div class="text-2xl mb-3">&#129302;</div>
            <h3 class="font-semibold text-gray-900 mb-1">AI-ready via MCP</h3>
            <p class="text-sm text-gray-500">Connect Claude AI to your docs with one URL. Your team can query documentation directly from claude.ai.</p>
        </div>
    </div>
</section>

<!-- How it works -->
<section class="max-w-4xl mx-auto px-6 pb-20">
    <h2 class="text-xl font-bold text-gray-900 mb-6 text-center">How it works</h2>
    <div class="grid md:grid-cols-4 gap-4">
        <div class="text-center">
            <div class="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 font-bold text-sm flex items-center justify-center mx-auto mb-2">1</div>
            <p class="text-sm text-gray-600">Sign in and create a project</p>
        </div>
        <div class="text-center">
            <div class="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 font-bold text-sm flex items-center justify-center mx-auto mb-2">2</div>
            <p class="text-sm text-gray-600">Pick a GitHub repo with markdown docs</p>
        </div>
        <div class="text-center">
            <div class="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 font-bold text-sm flex items-center justify-center mx-auto mb-2">3</div>
            <p class="text-sm text-gray-600">Invite your team by email or domain</p>
        </div>
        <div class="text-center">
            <div class="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 font-bold text-sm flex items-center justify-center mx-auto mb-2">4</div>
            <p class="text-sm text-gray-600">Browse docs on the web or via Claude AI</p>
        </div>
    </div>
</section>

<!-- Footer -->
<footer class="max-w-4xl mx-auto px-6 py-8 border-t border-gray-200 text-center">
    <p class="text-xs text-gray-400">Memento &mdash; open source on <a href="https://github.com/AlexisLaporte/memento" class="hover:text-gray-600 underline" target="_blank">GitHub</a></p>
</footer>

</body></html>'''


def _dashboard_page(configs, user):
    email = user.get('email', '') if user else ''
    name = user.get('name', '') if user else ''
    initials = ''.join(w[0] for w in name.split()[:2]).upper() if name else email[0:1].upper()
    picture = user.get('picture', '') if user else ''

    avatar = (
        f'<img src="{picture}" class="w-9 h-9 rounded-full">'
        if picture else
        f'<div class="w-9 h-9 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-semibold">{initials}</div>'
    )

    cards = ''
    for slug, config in configs.items():
        owner_badge = ''
        if config.owner_email == email:
            owner_badge = '<span class="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">Owner</span>'
        cards += f'''
        <a href="/{slug}/" class="group block bg-white rounded-xl border border-gray-200 p-5 hover:border-indigo-300 hover:shadow-md transition-all">
            <div class="flex items-start justify-between mb-3">
                <div class="w-3 h-3 rounded-full mt-1" style="background:{config.color}"></div>
                {owner_badge}
            </div>
            <div class="font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">{config.title}</div>
            <p class="text-xs text-gray-400 mt-1 font-mono">{config.repo_full_name}</p>
        </a>'''

    empty_state = '''
    <div class="col-span-full text-center py-12">
        <div class="text-4xl mb-3">&#128218;</div>
        <p class="text-gray-500 mb-1">No projects yet</p>
        <p class="text-sm text-gray-400">Create your first project to get started.</p>
    </div>''' if not cards else ''

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Memento</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>body {{ font-family: 'Inter', system-ui, sans-serif; }}</style></head>
<body class="bg-gray-50 min-h-screen">

<nav class="max-w-4xl mx-auto flex justify-between items-center px-6 py-5">
    <span class="text-lg font-bold text-gray-900 tracking-tight">Memento</span>
    <div class="flex items-center gap-4">
        {avatar}
        <div class="text-right hidden sm:block">
            <div class="text-sm font-medium text-gray-700">{name or email}</div>
            <a href="/auth/logout" class="text-xs text-gray-400 hover:text-gray-600">Sign out</a>
        </div>
    </div>
</nav>

<main class="max-w-4xl mx-auto px-6 pt-6 pb-20">
    <div class="flex justify-between items-center mb-6">
        <div>
            <h1 class="text-xl font-bold text-gray-900">Your projects</h1>
            <p class="text-sm text-gray-400 mt-0.5">{len(configs)} project{'s' if len(configs) != 1 else ''}</p>
        </div>
        <a href="/new" class="inline-flex items-center gap-1.5 text-sm font-medium text-white bg-indigo-500 px-4 py-2 rounded-lg hover:bg-indigo-600 transition">
            + New project
        </a>
    </div>
    <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards}{empty_state}
    </div>
</main>

</body></html>'''


def main():
    """CLI entry point."""
    app = create_app()
    port = int(os.getenv('PORT', '5002'))
    app.run(debug=True, port=port)


if __name__ == '__main__':
    main()
