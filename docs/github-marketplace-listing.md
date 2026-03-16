# GitHub Marketplace Listing — Mento

## Naming and links

- **Listing name:** Mento
- **Very short description:** Render your GitHub docs as a branded portal with access control, search, and AI integration via MCP.
- **Primary category:** Project management
- **Secondary category:** Documentation
- **Customer support URL:** https://github.com/AlexisLaporte/memento/issues
- **Company URL:** https://mento.cc
- **Documentation URL:** https://mento.cc

## Logo and feature card

- **Logo:** logo-book.png
- **Badge background color:** 2a5a4a
- **Text color:** Dark text
- **Background image:** (965x482, à créer)

## Introductory description

Mento turns your GitHub repository into a polished documentation portal. Connect a repo, pick the folders to expose, invite your team — docs are rendered with full markdown support, Mermaid diagrams, syntax highlighting, and PDF/image viewing. Access control is built in: manage members and roles per project. An MCP server lets AI assistants like Claude read and edit your docs directly.

## Detailed description

### Capabilities

- **Markdown rendering** with syntax highlighting, Mermaid diagrams, table of contents, and frontmatter support
- **Multi-format viewer** for PDF, images, code files, and text — all inline
- **Team access control** with member roles (owner, admin, member) and email invitations
- **GitHub Issues integration** — view and manage issues from within the portal
- **Full-text search** across all project documentation (Cmd+K)
- **MCP server** — AI assistants (Claude, etc.) can list projects, read docs, create/update files, and browse issues via the Model Context Protocol

### Benefits

- **Single source of truth:** Docs live in your GitHub repo — no sync, no copy-paste, no drift.
- **Instant onboarding:** Invite a teammate by email, they see the docs. No GitHub access required.
- **AI-native:** Connect Claude or any MCP client to query and update your documentation programmatically.
- **Zero maintenance:** Push to GitHub, docs update automatically. No build step, no deploy pipeline for content.

### Getting Started

**Requirements:**
- **Plan:** Free (self-hosted) or hosted on mento.cc
- **User Permissions:** Install the GitHub App on your org or personal account
- **Availability:** GA — open to all GitHub users

**Setup Process:**
1. Install the Mento GitHub App on your organization or account
2. Go to [mento.cc](https://mento.cc), sign in, and create a new project
3. Select your GitHub installation, pick a repo and folders to expose
4. Invite team members by email — they get instant access

### Example Prompts

Try these with the Mento MCP connector in Claude:
- "List all my Mento projects"
- "Show the doc tree for the backend project"
- "Read the architecture.md file from our docs"
- "Create a new onboarding guide in the team-docs project"
- "What are the open issues labeled 'bug' in my project?"
