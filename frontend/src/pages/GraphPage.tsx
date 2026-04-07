import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  Panel,
} from '@xyflow/react'
import dagre from '@dagrejs/dagre'
import { apiGet } from '@/lib/api'
import '@xyflow/react/dist/style.css'

interface GraphNode {
  id: string
  type: string
  label: string
  path?: string
  title?: string
  word_count?: number
}

interface GraphEdge {
  source: string
  target: string
  type: string
  link_text?: string
}

interface KnowledgeGraphData {
  project_slug: string
  nodes: GraphNode[]
  edges: GraphEdge[]
}

const NODE_WIDTH = 180
const NODE_HEIGHT = 40

function layoutGraph(
  graphNodes: GraphNode[],
  graphEdges: GraphEdge[],
): { nodes: Node[]; edges: Edge[] } {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', nodesep: 60, ranksep: 80 })

  for (const n of graphNodes) {
    g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  }
  for (const e of graphEdges) {
    // Only add edge if both nodes exist
    if (g.hasNode(e.source) && g.hasNode(e.target)) {
      g.setEdge(e.source, e.target)
    }
  }

  dagre.layout(g)

  const nodes: Node[] = graphNodes.map((n) => {
    const pos = g.node(n.id)
    const isProject = n.type === 'project'
    const isDir = n.type === 'directory'
    return {
      id: n.id,
      position: { x: (pos?.x ?? 0) - NODE_WIDTH / 2, y: (pos?.y ?? 0) - NODE_HEIGHT / 2 },
      data: { ...n, label: n.title || n.label },
      style: {
        width: NODE_WIDTH,
        fontSize: 12,
        padding: '8px 12px',
        borderRadius: isProject ? 12 : 8,
        background: isProject
          ? '#6366f1'
          : isDir
            ? '#f1f5f9'
            : '#ffffff',
        color: isProject ? '#ffffff' : '#1e293b',
        border: isProject
          ? '2px solid #4f46e5'
          : isDir
            ? '1px solid #cbd5e1'
            : '1px solid #e2e8f0',
        fontWeight: isProject || isDir ? 600 : 400,
        cursor: n.type === 'document' ? 'pointer' : 'default',
      },
    }
  })

  const edges: Edge[] = graphEdges
    .filter((e) => g.hasNode(e.source) && g.hasNode(e.target))
    .map((e, i) => ({
      id: `e-${i}`,
      source: e.source,
      target: e.target,
      type: 'smoothstep',
      animated: e.type === 'links_to',
      style: {
        stroke: e.type === 'links_to' ? '#6366f1' : '#94a3b8',
        strokeWidth: e.type === 'links_to' ? 1.5 : 1,
      },
      label: e.type === 'links_to' ? e.link_text : undefined,
      labelStyle: { fontSize: 10, fill: '#64748b' },
    }))

  return { nodes, edges }
}

export default function GraphPage() {
  const { project } = useParams<{ project: string }>()
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge-graph', project],
    queryFn: () => apiGet<KnowledgeGraphData>(`/${project}/api/knowledge-graph`),
    enabled: !!project,
  })

  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  const layout = useMemo(() => {
    if (!data) return null
    return layoutGraph(data.nodes, data.edges)
  }, [data])

  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[])
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[])

  useEffect(() => {
    if (layout) {
      setNodes(layout.nodes)
      setEdges(layout.edges)
    }
  }, [layout, setNodes, setEdges])

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const d = node.data as unknown as GraphNode
      setSelectedNode(d)
      if (d.type === 'document' && d.path) {
        // Double-click navigates
      }
    },
    [],
  )

  const onNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const d = node.data as unknown as GraphNode
      if (d.type === 'document' && d.path) {
        navigate(`/${project}/${d.path}`)
      }
    },
    [navigate, project],
  )

  const stats = useMemo(() => {
    if (!data) return null
    const docs = data.nodes.filter((n) => n.type === 'document').length
    const dirs = data.nodes.filter((n) => n.type === 'directory').length
    const links = data.edges.filter((e) => e.type === 'links_to').length
    return { docs, dirs, links }
  }, [data])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground text-sm">Loading knowledge graph...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-destructive text-sm">Failed to load knowledge graph.</p>
      </div>
    )
  }

  return (
    <div className="h-full w-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onNodeDoubleClick={onNodeDoubleClick}
        fitView
        minZoom={0.1}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background />
        <Controls />
        <MiniMap
          nodeStrokeWidth={3}
          nodeColor={(n) => {
            const d = n.data as unknown as GraphNode
            if (d.type === 'project') return '#6366f1'
            if (d.type === 'directory') return '#cbd5e1'
            return '#e2e8f0'
          }}
          style={{ borderRadius: 8 }}
        />

        {/* Stats panel */}
        {stats && (
          <Panel position="top-left">
            <div className="bg-background/90 backdrop-blur border rounded-lg px-4 py-3 shadow-sm">
              <h2 className="text-sm font-semibold mb-2">Knowledge Graph</h2>
              <div className="flex gap-4 text-xs text-muted-foreground">
                <span>{stats.docs} docs</span>
                <span>{stats.dirs} dirs</span>
                <span>{stats.links} links</span>
              </div>
            </div>
          </Panel>
        )}

        {/* Selected node panel */}
        {selectedNode && (
          <Panel position="top-right">
            <div className="bg-background/90 backdrop-blur border rounded-lg px-4 py-3 shadow-sm max-w-[280px]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium uppercase text-muted-foreground">
                  {selectedNode.type}
                </span>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-muted-foreground hover:text-foreground text-xs"
                >
                  x
                </button>
              </div>
              <p className="text-sm font-medium truncate">
                {selectedNode.title || selectedNode.label}
              </p>
              {selectedNode.path && (
                <p className="text-xs text-muted-foreground mt-1 truncate">{selectedNode.path}</p>
              )}
              {selectedNode.word_count != null && selectedNode.word_count > 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  {selectedNode.word_count.toLocaleString()} words
                </p>
              )}
              {selectedNode.type === 'document' && selectedNode.path && (
                <button
                  onClick={() => navigate(`/${project}/${selectedNode.path}`)}
                  className="mt-2 text-xs text-primary hover:underline"
                >
                  Open document
                </button>
              )}
            </div>
          </Panel>
        )}
      </ReactFlow>
    </div>
  )
}
