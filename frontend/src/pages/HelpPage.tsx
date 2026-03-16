import { Link } from 'react-router-dom'

const sections = [
  {
    title: 'Getting started',
    items: [
      { q: 'How do I create a project?', a: 'Sign in, click "+ New" in the sidebar, select your GitHub installation and repository, choose the folders to expose, and your docs are live instantly.' },
      { q: 'How do I install the GitHub App?', a: 'During project creation, click "Install the Mento GitHub App" to add it to your GitHub organization or personal account. This grants Mento read access to your repositories.' },
      { q: 'What file types are supported?', a: 'Markdown (.md) with full rendering, PDF (inline viewer), images (PNG, JPG, SVG, WebP), and code/text files with syntax highlighting.' },
    ],
  },
  {
    title: 'Team & access',
    items: [
      { q: 'How do I invite team members?', a: 'Go to your project Settings, enter their email address, and send an invite. They\'ll receive an email with a direct link — no GitHub account required.' },
      { q: 'What are the roles?', a: 'Owner (full control), Admin (manage members and settings), Member (read docs and issues). You can also block users to revoke access.' },
      { q: 'Can I use a custom domain?', a: 'Yes. In project Settings, set your custom domain and point a CNAME record to mento.cc in your DNS.' },
    ],
  },
  {
    title: 'AI & MCP',
    items: [
      { q: 'What is MCP?', a: 'The Model Context Protocol lets AI assistants like Claude read and edit your documentation. Add the Mento MCP server URL in your AI client to get started.' },
      { q: 'What can AI do with my docs?', a: 'List projects, browse the doc tree, read files, create or update documents, and query GitHub issues — all through natural language.' },
      { q: 'What\'s the MCP server URL?', a: 'Connect your AI client to https://mcp.mento.cc/mcp — you\'ll authenticate via your Mento account.' },
    ],
  },
  {
    title: 'Troubleshooting',
    items: [
      { q: 'My docs aren\'t updating', a: 'Mento fetches directly from GitHub on each request. Clear your browser cache or hard-refresh (Ctrl+Shift+R). If the issue persists, check that the file exists in your repo\'s default branch.' },
      { q: 'I can\'t see my repository', a: 'Make sure the Mento GitHub App is installed on the organization or account that owns the repo. You may need to grant access to specific repositories in your GitHub App settings.' },
      { q: 'PDF won\'t load', a: 'Large PDFs (>1MB) may take a moment to load as they\'re proxied through the server. If it fails, try opening it in a new tab via the link below the viewer.' },
    ],
  },
]

export default function HelpPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="max-w-3xl mx-auto flex items-center justify-between px-4 sm:px-8 py-4">
        <Link to="/" className="flex items-center gap-2">
          <img src="/logo-book.svg" alt="Mento" className="h-7 w-7" />
          <span className="text-base font-bold tracking-tight font-serif">Mento</span>
        </Link>
        <a
          href="/auth/login?next=/"
          className="text-sm font-medium text-primary hover:text-foreground transition"
        >
          Sign in
        </a>
      </nav>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-4 sm:px-8 py-8">
        <h1 className="text-2xl font-bold font-serif mb-2">Help center</h1>
        <p className="text-muted-foreground mb-10">Everything you need to know about Mento.</p>

        {sections.map(section => (
          <div key={section.title} className="mb-10">
            <h2 className="text-lg font-semibold mb-4 pb-2 border-b border-border">{section.title}</h2>
            <div className="space-y-4">
              {section.items.map(item => (
                <details key={item.q} className="group">
                  <summary className="cursor-pointer text-sm font-medium text-foreground hover:text-primary transition flex items-center gap-2">
                    <svg className="w-3.5 h-3.5 shrink-0 text-muted-foreground group-open:rotate-90 transition-transform" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                    {item.q}
                  </summary>
                  <p className="text-sm text-muted-foreground mt-2 ml-5.5 leading-relaxed">{item.a}</p>
                </details>
              ))}
            </div>
          </div>
        ))}

        {/* Contact */}
        <div className="mt-12 p-6 rounded-xl bg-card border border-border text-center">
          <h3 className="font-semibold mb-2">Still need help?</h3>
          <p className="text-sm text-muted-foreground mb-4">Open an issue on GitHub or reach out by email.</p>
          <div className="flex items-center justify-center gap-4">
            <a
              href="https://github.com/AlexisLaporte/memento/issues"
              target="_blank"
              className="text-sm font-medium text-primary hover:underline"
            >
              GitHub Issues
            </a>
            <span className="text-muted-foreground">·</span>
            <a
              href="mailto:alexis@otomata.tech"
              className="text-sm font-medium text-primary hover:underline"
            >
              alexis@otomata.tech
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
