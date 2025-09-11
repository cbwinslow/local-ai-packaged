'use client'

import React, { useEffect, useRef, useState, useImperativeHandle, forwardRef, useCallback } from 'react'
import { driver, getSession } from '@/lib/neo4j'
import { DataSet } from 'vis-data/standalone'
import { Network } from 'vis-network/standalone'
import type { QueryResult, Record as Neo4jRecord } from 'neo4j-driver'

interface GraphNode {
  id: string | number
  label: string
  title?: string
  group?: string
  color?: string
  shape?: string
  size?: number
  x?: number
  y?: number
}

interface GraphEdge {
  id?: string
  from: string | number
  to: string | number
  label?: string
  arrows?: string | {
    to?: boolean | { enabled?: boolean; type?: string }
    middle?: boolean | { enabled?: boolean; type?: string }
    from?: boolean | { enabled?: boolean; type?: string }
  }
  width?: number
  color?: string | { color?: string; highlight?: string; hover?: string; inherit?: boolean | string }
  dashes?: boolean | number[]
  hidden?: boolean
  selectionWidth?: number | (() => number)
  smooth?: boolean | {
    enabled?: boolean
    type?: string
    forceDirection?: string | boolean
    roundness?: number
  }
  title?: string
  value?: number
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// Node styling interface
interface NodeOptions {
  borderWidth?: number;
  borderWidthSelected?: number;
  brokenImage?: string;
  chosen?: boolean | {
    node?: (values: any, id: string | number, selected: boolean, hovering: boolean) => any;
    label?: (values: any, id: string | number, selected: boolean, hovering: boolean) => any;
  };
  color?: string | {
    border?: string;
    background?: string;
    highlight?: string | { border?: string; background?: string };
    hover?: string | { border?: string; background?: string };
    opacity?: number;
  };
  fixed?: boolean | { x?: boolean; y?: boolean };
  font?: string | {
    color?: string;
    size?: number;
    face?: string;
    background?: string;
    strokeWidth?: number;
    strokeColor?: string;
    align?: 'left' | 'center' | 'right';
    multi?: boolean | string;
    vadjust?: number;
    bold?: string | { color?: string; size?: string | number; mod?: string; vadjust?: number };
    ital?: string | { color?: string; size?: string | number; face?: string; mod?: string; vadjust?: number };
    boldital?: string | { color?: string; size?: string | number; face?: string; mod?: string; vadjust?: number };
    mono?: string | { color?: string; size?: string | number; face?: string; mod?: string; vadjust?: number; vadjustMulti?: string };
  };
  group?: string;
  heightConstraint?: number | { minimum?: number; maximum?: number; valign?: number };
  hidden?: boolean;
  icon?: {
    face?: string;
    code?: string;
    weight?: string | number;
    size?: number;
    color?: string;
    strokeColor?: string;
    strokeWidth?: number;
  };
  image?: string;
  label?: string;
  labelHighlightBold?: boolean;
  level?: number;
  margin?: {
    top?: number;
    right?: number;
    bottom?: number;
    left?: number;
  };
  mass?: number;
  physics?: boolean;
  scaling?: {
    min?: number;
    max?: number;
    label?: boolean | {
      enabled?: boolean;
      min?: number;
      max?: number;
      maxVisible?: number;
      drawThreshold?: number;
    };
    customScalingFunction?: (min: number, max: number, total: number, value: number) => number;
  };
  selectionWidth?: number | ((width: number) => number);
  selfReferenceSize?: number;
  selfReference?: {
    angle?: number;
    renderBehindTheNode?: boolean;
  };
  shadow?: boolean | {
    enabled?: boolean;
    color?: string;
    size?: number;
    x?: number;
    y?: number;
  };
  shape?: 'ellipse' | 'circle' | 'database' | 'diamond' | 'dot' | 'square' | 'star' | 'triangle' | 'triangleDown' | 'hexagon' | 'icon';
  shapeProperties?: {
    borderDashes?: number[];
    borderRadius?: number;
    interpolation?: boolean;
    useImageSize?: boolean;
    useBorderWithImage?: boolean;
  };
  size?: number;
  smooth?: boolean | {
    enabled?: boolean;
    type?: string;
    forceDirection?: string | boolean;
    roundness?: number;
  };
  title?: string | HTMLElement | ((params?: any) => string | HTMLElement);
  value?: number;
  widthConstraint?: number | boolean | { minimum?: number; maximum?: number };
  x?: number;
  y?: number;
}

interface EdgeOptions {
  color?: string | {
    color?: string;
    highlight?: string;
    hover?: string;
    inherit?: boolean | 'from' | 'to' | 'both';
    opacity?: number;
  };
  arrows?: string | {
    to?: boolean | {
      enabled?: boolean;
      imageHeight?: number;
      imageWidth?: number;
      scaleFactor?: number;
      src?: string;
      type?: string;
    };
    middle?: boolean | {
      enabled?: boolean;
      imageHeight?: number;
      imageWidth?: number;
      scaleFactor?: number;
      src?: string;
      type?: string;
    };
    from?: boolean | {
      enabled?: boolean;
      imageHeight?: number;
      imageWidth?: number;
      scaleFactor?: number;
      src?: string;
      type?: string;
    };
  };
  dashes?: boolean | number[];
  font?: {
    color?: string;
    size?: number;
    face?: string;
    background?: string;
    strokeWidth?: number;
    strokeColor?: string;
    align?: 'horizontal' | 'top' | 'middle' | 'bottom';
    multi?: boolean | string;
    vadjust?: number;
    mod?: string;
  };
  hidden?: boolean;
  hoverWidth?: number | ((width: number) => number);
  label?: string;
  labelHighlightBold?: boolean;
  length?: number;
  physics?: boolean;
  scaling?: {
    min?: number;
    max?: number;
    label?: boolean | {
      enabled?: boolean;
      min?: number;
      max?: number;
      maxVisible?: number;
      drawThreshold?: number;
    };
  };
  selectionWidth?: number | ((width: number) => number);
  selfReference?: {
    angle?: number;
    renderBehindTheNode?: boolean;
  };
  selfReferenceSize?: number;
  shadow?: boolean | {
    enabled?: boolean;
    color?: string;
    size?: number;
    x?: number;
    y?: number;
  };
  smooth?: boolean | {
    enabled: boolean;
    type?: string;
    roundness?: number;
    forceDirection?: 'horizontal' | 'vertical' | 'none';
  };
  title?: string | HTMLElement | ((params?: any) => string | HTMLElement);
  value?: number;
  width?: number;
  widthConstraint?: number | boolean | {
    maximum?: number;
  };
}

interface LayoutOptions {
  randomSeed?: number;
  improvedLayout?: boolean;
  hierarchical?: {
    enabled?: boolean;
    levelSeparation?: number;
    nodeSpacing?: number;
    treeSpacing?: number;
    blockShifting?: boolean;
    edgeMinimization?: boolean;
    parentCentralization?: boolean;
    direction?: 'UD' | 'DU' | 'LR' | 'RL';
    sortMethod?: 'hubsize' | 'directed';
    shakeTowards?: 'leaves' | 'roots' | 'none';
  };
}

interface PhysicsOptions {
  enabled?: boolean;
  barnesHut?: {
    gravitationalConstant?: number;
    centralGravity?: number;
    springLength?: number;
    springConstant?: number;
    nodeDistance?: number;
    damping?: number;
  };
  forceAtlas2Based?: {
    gravitationalConstant?: number;
    centralGravity?: number;
    springLength?: number;
    springConstant?: number;
    nodeDistance?: number;
    damping?: number;
  };
  repulsion?: {
    centralGravity?: number;
    springLength?: number;
    springConstant?: number;
    nodeDistance?: number;
    damping?: number;
  };
  hierarchicalRepulsion?: {
    centralGravity?: number;
    springLength?: number;
    springConstant?: number;
    nodeDistance?: number;
    damping?: number;
  };
  maxVelocity?: number;
  minVelocity?: number;
  solver?: 'barnesHut' | 'repulsion' | 'hierarchicalRepulsion' | 'forceAtlas2Based';
  stabilization?: {
    enabled?: boolean;
    iterations?: number;
    updateInterval?: number;
    onlyDynamicEdges?: boolean;
    fit?: boolean;
  };
  timestep?: number;
  adaptiveTimestep?: boolean;
}

interface InteractionOptions {
  dragNodes?: boolean;
  dragView?: boolean;
  hideEdgesOnDrag?: boolean;
  hideNodesOnDrag?: boolean;
  hover?: boolean;
  hoverConnectedEdges?: boolean;
  keyboard?: boolean | {
    enabled?: boolean;
    speed?: { x: number; y: number; zoom: number };
    bindToWindow?: boolean;
  };
  multiselect?: boolean;
  navigationButtons?: boolean;
  selectable?: boolean;
  selectConnectedEdges?: boolean;
  tooltipDelay?: number;
  zoomView?: boolean;
}

interface NetworkOptions {
  nodes?: NodeOptions;
  edges?: EdgeOptions;
  layout?: LayoutOptions;
  physics?: PhysicsOptions | boolean;
  interaction?: InteractionOptions;
}

interface PhysicsOptions {
  enabled?: boolean;
  barnesHut?: {
    gravitationalConstant?: number;
    centralGravity?: number;
    springLength?: number;
    springConstant?: number;
    nodeDistance?: number;
    damping?: number;
  };
  forceAtlas2Based?: {
    gravitationalConstant?: number;
    centralGravity?: number;
    springLength?: number;
    springConstant?: number;
    nodeDistance?: number;
    damping?: number;
  };
  repulsion?: {
    centralGravity?: number;
    springLength?: number;
    springConstant?: number;
    nodeDistance?: number;
    damping?: number;
  };
  hierarchicalRepulsion?: {
    centralGravity?: number;
    springLength?: number;
    springConstant?: number;
    nodeDistance?: number;
    damping?: number;
  };
  maxVelocity?: number;
  minVelocity?: number;
  solver?: 'barnesHut' | 'repulsion' | 'hierarchicalRepulsion' | 'forceAtlas2Based';
  stabilization?: {
    enabled?: boolean;
    iterations?: number;
    updateInterval?: number;
      onlyDynamicEdges?: boolean
      fit?: boolean
    }
    timestep?: number
    adaptiveTimestep?: boolean
  }
  interaction?: {
    dragNodes?: boolean
    dragView?: boolean
    hideEdgesOnDrag?: boolean
    hideNodesOnDrag?: boolean
    hover?: boolean
    hoverConnectedEdges?: boolean
    keyboard?: boolean | {
      enabled?: boolean
      speed?: { x: number; y: number; zoom: number }
      bindToWindow?: boolean
    }
    multiselect?: boolean
    navigationButtons?: boolean
    selectable?: boolean
    selectConnectedEdges?: boolean
    tooltipDelay?: number
    zoomView?: boolean
      color?: string
      size?: number
      face?: string
      background?: string
      strokeWidth?: number
      strokeColor?: string
      align?: 'left' | 'center' | 'right'
      multi?: boolean | string
      vadjust?: number
      bold?: string | { color?: string; size?: string | number; mod?: string; vadjust?: number }
      ital?: string | { color?: string; size?: string | number; face?: string; mod?: string; vadjust?: number }
      boldital?: string | { color?: string; size?: string | number; face?: string; mod?: string; vadjust?: number }
      mono?: string | { color?: string; size?: string | number; face?: string; mod?: string; vadjust?: number; vadjustMulti?: string }
    }
    group?: string
    heightConstraint?: number | { minimum?: number; maximum?: number; valign?: number }
    hidden?: boolean
    icon?: {
      face?: string
      code?: string
      weight?: string
      size?: number
      color?: string
      strokeColor?: string
      strokeWidth?: number
    }
    image?: string
    label?: string
    labelHighlightBold?: boolean
    level?: number
    margin?: {
      top?: number
      right?: number
      bottom?: number
      left?: number
    }
    mass?: number
    physics?: boolean
    scaling?: {
      min?: number
      max?: number
      label?: {
        enabled?: boolean
        min?: number
        max?: number
        maxVisible?: number
        drawThreshold?: number
      }
      customScalingFunction?: (min: number, max: number, total: number, value: number) => number
    }
    shadow?: boolean | {
      enabled?: boolean
      color?: string
      size?: number
      x?: number
      y?: number
    }
    shape?: 'ellipse' | 'circle' | 'database' | 'diamond' | 'dot' | 'square' | 'star' | 'triangle' | 'triangleDown' | 'hexagon' | 'icon'
    shapeProperties?: {
      borderDashes?: number[]
      borderRadius?: number
      interpolation?: boolean
      useImageSize?: boolean
      useBorderWithImage?: boolean
    }
    size?: number
    title?: string | HTMLElement | ((params?: any) => string | HTMLElement)
    value?: number
    widthConstraint?: number | boolean | { minimum?: number; maximum?: number }
    x?: number
    y?: number
  }
}

export interface GraphViewerProps {
  initialData?: GraphData
  height?: string | number
  width?: string | number
  options?: NetworkOptions
  events?: {
    select?: (params: any) => void
    hoverNode?: (params: { node: string }) => void
    blurNode?: () => void
    click?: (params: any) => void
    doubleClick?: (params: any) => void
    oncontext?: (params: any) => void
    dragStart?: (params: any) => void
    dragging?: (params: any) => void
    dragEnd?: (params: any) => void
    zoom?: (params: any) => void
    showPopup?: (nodeId: string) => string
    hidePopup?: () => void
  }
}

export interface GraphViewerRef {
  getNetwork: () => Network | null
  fit: (options?: any) => void
  focus: (nodeId: string | number, options?: any) => void
  getSelectedNodes: () => (string | number)[]
  getSelectedEdges: () => (string | number)[]
  getNodeAt: (position: { x: number; y: number }) => string | number | undefined
  getEdgeAt: (position: { x: number; y: number }) => string | number | undefined
  getPosition: (nodeId: string | number) => { x: number; y: number } | undefined
  getBoundingBox: (nodeId: string | number) => { top: number; left: number; right: number; bottom: number } | undefined
  getConnectedNodes: (nodeId: string | number, direction?: 'from' | 'to' | 'both') => (string | number)[]
  getConnectedEdges: (nodeId: string | number) => (string | number)[]
  selectNodes: (nodeIds: (string | number)[], highlightEdges?: boolean) => void
  selectEdges: (edgeIds: (string | number)[]) => void
  setSelection: (selection: { nodes?: (string | number)[]; edges?: (string | number)[] }, options?: any) => void
  setData: (data: GraphData) => void
  addNode: (node: GraphNode) => void
  addEdge: (edge: GraphEdge) => void
  updateNode: (node: GraphNode) => void
  updateEdge: (edge: GraphEdge) => void
  removeNode: (nodeId: string | number) => void
  removeEdge: (edgeId: string) => void
  clear: () => void
  destroy: () => void
}

export const GraphViewer = forwardRef<GraphViewerRef, GraphViewerProps>(({
  initialData = { nodes: [], edges: [] },
  height = '600px',
  width = '100%',
  options = {},
  events = {}
}, ref) => {
  const [graphData, setGraphData] = useState<GraphData>(initialData)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const networkRef = useRef<Network | null>(null)
  const nodesRef = useRef<DataSet<GraphNode, 'id'>>(new DataSet(initialData.nodes))
  const edgesRef = useRef<DataSet<GraphEdge, 'id'>>(new DataSet(initialData.edges))

  const fetchGraph = useCallback(async () => {
    try {
      const session = getSession()
      const result = await session.run('MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 10') as QueryResult
      const nodeSet = new Set<string>()
      const graphEdges: GraphEdge[] = []
      const graphNodes: GraphNode[] = []

      result.records.forEach((record: Neo4jRecord) => {
        const n = record.get('n')
        const m = record.get('m')
        const r = record.get('r')

        const nodeIdN = n.identity.low.toString()
        const nodeIdM = m.identity.low.toString()

        if (!nodeSet.has(nodeIdN)) {
          nodeSet.add(nodeIdN)
          const labelN = n.properties.name || (n.labels && n.labels[0]) || 'Node'
          graphNodes.push({
            id: n.identity.low,
            label: labelN,
            title: n.properties.description || '',
            group: (n.labels && n.labels[0]) || 'default'
          })
        }

        if (!nodeSet.has(nodeIdM)) {
          nodeSet.add(nodeIdM)
          const labelM = m.properties.name || (m.labels && m.labels[0]) || 'Node'
          graphNodes.push({
            id: m.identity.low,
            label: labelM,
            title: m.properties.description || '',
            group: (m.labels && m.labels[0]) || 'default'
          })
        }

        graphEdges.push({
          id: `${r.identity.low}`,
          from: n.identity.low,
          to: m.identity.low,
          label: r.type,
          arrows: 'to'
        })
      })

      setGraphData({
        nodes: graphNodes,
        edges: graphEdges
      })
    } catch (error) {
      console.error('Neo4j query error:', error);
    } finally {
      setLoading(false);
    }
  }, [getSession])

  useEffect(() => {
    fetchGraph()
  }, [fetchGraph])

  useEffect(() => {
    if (graphData.nodes.length === 0 && graphData.edges.length === 0) return

    nodesRef.current.clear()
    edgesRef.current.clear()

    if (graphData.nodes.length > 0) {
      nodesRef.current.add(graphData.nodes)
    }

    if (graphData.edges.length > 0) {
      edgesRef.current.add(graphData.edges)
    }
  }, [graphData])

  useEffect(() => {
    if (!containerRef.current) return

    // Convert to plain arrays to avoid DataSet type issues
      // Convert to plain arrays for vis-network
    const nodeList = Array.isArray(graphData.nodes) ? 
      [...graphData.nodes] : 
      graphData.nodes ? Array.from(graphData.nodes) : [];
    
    const edgeList = Array.isArray(graphData.edges) ? 
      [...graphData.edges] : 
      graphData.edges ? Array.from(graphData.edges) : [];
    
    const data = { nodes: nodeList, edges: edgeList };

    const defaultOptions: NetworkOptions = {
      nodes: {
        shape: 'dot',
        size: 16,
        font: {
          size: 12,
          color: '#000000',
          strokeWidth: 3,
          strokeColor: '#ffffff'
        },
        borderWidth: 2,
        color: {
          border: '#2B7CE9',
          background: '#97C2FC',
          highlight: {
            border: '#2B7CE9',
            background: '#D2E5FF'
          },
          hover: {
            border: '#2B7CE9',
            background: '#D2E5FF'
          }
        }
      },
      edges: {
        width: 2,
        color: { color: '#848484' },
        smooth: {
          type: 'continuous',
          roundness: 0.5
        },
        arrows: {
          to: {
            enabled: true,
            type: 'arrow'
          }
        },
        selectionWidth: 3,
        hoverWidth: 2.5
      },
      physics: {
        enabled: true,
        stabilization: {
          enabled: true,
          iterations: 1000,
          updateInterval: 25
        },
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 200,
          springConstant: 0.04,
          damping: 0.09
        },
        minVelocity: 0.75,
        solver: 'barnesHut',
        timestep: 0.5
      },
      interaction: {
        dragNodes: true,
        dragView: true,
        hideEdgesOnDrag: false,
        hideNodesOnDrag: false,
        hover: true,
        hoverConnectedEdges: true,
        keyboard: {
          enabled: true,
          speed: { x: 10, y: 10, zoom: 0.02 },
          bindToWindow: true
        },
        multiselect: true,
        navigationButtons: true,
        selectable: true,
        selectConnectedEdges: true,
        tooltipDelay: 200,
        zoomView: true
      },
      layout: {
        improvedLayout: true,
        hierarchical: {
          enabled: false,
          levelSeparation: 150,
          nodeSpacing: 100,
          treeSpacing: 200,
          blockShifting: true,
          edgeMinimization: true,
          parentCentralization: true,
          direction: 'UD',
          sortMethod: 'hubsize',
          shakeTowards: 'leaves'
        }
      }
    }

    const network = new Network(containerRef.current, data, defaultOptions)

    networkRef.current = network

    network.on('select', (params: any) => {
      if (events.select) {
        events.select(params)
      }
    })

    network.on('hoverNode', (params: { node: string }) => {
      if (events.hoverNode) {
        events.hoverNode(params)
      }
    })

    network.on('blurNode', () => {
      if (events.blurNode) {
        events.blurNode()
      }
    })

    network.on('click', (params: any) => {
      if (events.click) {
        events.click(params)
      }
    })

    network.on('doubleClick', (params: any) => {
      if (events.doubleClick) {
        events.doubleClick(params)
      }
    })

    network.on('oncontext', (params: any) => {
      if (events.oncontext) {
        events.oncontext(params)
      }
    })

    network.on('dragStart', (params: any) => {
      if (events.dragStart) {
        events.dragStart(params)
      }
    })

    network.on('dragging', (params: any) => {
      if (events.dragging) {
        events.dragging(params)
      }
    })

    network.on('dragEnd', (params: any) => {
      if (events.dragEnd) {
        events.dragEnd(params)
      }
    })

    network.on('zoom', (params: any) => {
      if (events.zoom) {
        events.zoom(params)
      }
    })

    network.on('showPopup', (nodeId: string) => {
      if (events.showPopup) {
        events.showPopup(nodeId)
      }
    })

    network.on('hidePopup', () => {
      if (events.hidePopup) {
        events.hidePopup()
      }
    })

    return () => {
      network.destroy()
      networkRef.current = null
    }
  }, [containerRef, graphData, events])

  const getNetwork = useCallback((): Network | null => networkRef.current, [])

  const fit = useCallback((options?: any): void => {
    networkRef.current?.fit(options)
  }, [])

  const focus = useCallback((nodeId: string | number, options?: any): void => {
    networkRef.current?.focus(nodeId, options)
  }, [])

  const getSelectedNodes = useCallback((): (string | number)[] => {
    return networkRef.current?.getSelectedNodes() || []
  }, [])

  const getSelectedEdges = useCallback((): (string | number)[] => {
    return networkRef.current?.getSelectedEdges() || []
  }, [])

  const getNodeAt = useCallback((position: { x: number; y: number }): string | number | undefined => {
    return networkRef.current?.getNodeAt(position)
  }, [])

  const getEdgeAt = useCallback((position: { x: number; y: number }): string | number | undefined => {
    return networkRef.current?.getEdgeAt(position)
  }, [])

  const getPosition = useCallback((nodeId: string | number): { x: number; y: number } | undefined => {
    return networkRef.current?.getPosition(nodeId)
  }, [])

  const getBoundingBox = useCallback((nodeId: string | number): { top: number; left: number; right: number; bottom: number } | undefined => {
    return networkRef.current?.getBoundingBox(nodeId)
  }, [])

  const getConnectedNodes = useCallback((nodeId: string | number, direction?: 'from' | 'to' | 'both'): (string | number)[] => {
    try {
      const result = networkRef.current?.getConnectedNodes(nodeId, direction as any) || []
      // Convert any complex objects to simple IDs
      return result.map(item => {
        if (typeof item === 'object' && item !== null) {
          return (item as any).id || item
        }
        return item
      })
    } catch (error) {
      console.error('Error getting connected nodes:', error)
      return []
    }
  }, [])

  const getConnectedEdges = useCallback((nodeId: string | number): (string | number)[] => {
    return networkRef.current?.getConnectedEdges(nodeId) || []
  }, [])

  const selectNodes = useCallback((nodeIds: (string | number)[], highlightEdges: boolean = true): void => {
    networkRef.current?.selectNodes(nodeIds, highlightEdges)
  }, [])

  const selectEdges = useCallback((edgeIds: (string | number)[]): void => {
    networkRef.current?.selectEdges(edgeIds)
  }, [])

  const setSelection = useCallback((selection: { nodes?: (string | number)[]; edges?: (string | number)[] }, options?: any): void => {
    networkRef.current?.setSelection(selection, options)
  }, [])

  const setData = useCallback((data: GraphData) => {
    setGraphData(data)
    nodesRef.current.clear()
    edgesRef.current.clear()
    if (data.nodes.length > 0) nodesRef.current.add(data.nodes)
    if (data.edges.length > 0) edgesRef.current.add(data.edges)
  }, [])

  const addNode = useCallback((node: GraphNode) => {
    nodesRef.current.add(node)
    setGraphData(prev => ({
      nodes: [...prev.nodes, node],
      edges: prev.edges
    }))
  }, [])

  const addEdge = useCallback((edge: GraphEdge) => {
    edgesRef.current.add(edge)
    setGraphData(prev => ({
      nodes: prev.nodes,
      edges: [...prev.edges, edge]
    }))
  }, [])

  const updateNode = useCallback((node: GraphNode) => {
    nodesRef.current.update(node)
    setGraphData(prev => ({
      nodes: prev.nodes.map(n => n.id === node.id ? { ...n, ...node } : n),
      edges: prev.edges
    }))
  }, [])

  const updateEdge = useCallback((edge: GraphEdge) => {
    edgesRef.current.update(edge)
    setGraphData(prev => ({
      nodes: prev.nodes,
      edges: prev.edges.map(e => e.id === edge.id ? { ...e, ...edge } : e)
    }))
  }, [])

  const removeNode = useCallback((nodeId: string | number) => {
    nodesRef.current.remove(nodeId)
    setGraphData(prev => ({
      nodes: prev.nodes.filter(n => n.id !== nodeId),
      edges: prev.edges.filter(e => e.from !== nodeId && e.to !== nodeId)
    }))
  }, [])

  const removeEdge = useCallback((edgeId: string) => {
    edgesRef.current.remove(edgeId)
    setGraphData(prev => ({
      nodes: prev.nodes,
      edges: prev.edges.filter(e => e.id !== edgeId)
    }))
  }, [])

  const clear = useCallback(() => {
    nodesRef.current.clear()
    edgesRef.current.clear()
    setGraphData({ nodes: [], edges: [] })
  }, [])

  const destroy = useCallback(() => {
    if (networkRef.current) {
      networkRef.current.destroy()
      networkRef.current = null
    }
  }, [])

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    getNetwork,
    fit,
    focus,
    getSelectedNodes,
    getSelectedEdges,
    getNodeAt,
    getEdgeAt,
    getPosition,
    getBoundingBox,
    getConnectedNodes,
    getConnectedEdges,
    selectNodes,
    selectEdges,
    setSelection,
    setData,
    addNode,
    addEdge,
    updateNode,
    updateEdge,
    removeNode,
    removeEdge: (edgeId: string) => void
    clear: () => void
    destroy: () => void
  }))

  useEffect(() => {
    if (!containerRef.current) return;

    try {
      setLoading(true);

      const nodes = Array.isArray(graphData.nodes) ? 
        [...graphData.nodes] : 
        graphData.nodes ? Array.from(graphData.nodes) : [];
      
      const edges = Array.isArray(graphData.edges) ? 
        [...graphData.edges] : 
        graphData.edges ? Array.from(graphData.edges) : [];
      
      const data = { nodes, edges };;

      const defaultOptions: NetworkOptions = {
        nodes: {
          shape: 'dot',
          size: 16,
          font: {
            size: 12,
            color: '#000000',
            strokeWidth: 3,
            strokeColor: '#ffffff'
          },
          borderWidth: 2,
          color: {
            border: '#2B7CE9',
            background: '#97C2FC',
            highlight: {
              border: '#2B7CE9',
              background: '#D2E5FF'
            },
            hover: {
              border: '#2B7CE9',
              background: '#D2E5FF'
            }
          }
        },
        edges: {
          width: 2,
          color: { color: '#848484' },
          smooth: {
            type: 'continuous',
            roundness: 0.5
          },
          arrows: {
            to: {
              enabled: true,
              type: 'arrow'
            }
          },
          selectionWidth: 3,
          hoverWidth: 2.5
        },
        physics: {
          enabled: true,
          stabilization: {
            enabled: true,
            iterations: 1000,
            updateInterval: 25
          },
          barnesHut: {
            gravitationalConstant: -2000,
            centralGravity: 0.3,
            springLength: 200,
            springConstant: 0.04,
            damping: 0.09,
            avoidOverlap: 0.1
          },
          minVelocity: 0.75,
          solver: 'barnesHut',
          timestep: 0.5
        },
        interaction: {
          dragNodes: true,
          dragView: true,
          hideEdgesOnDrag: false,
          hideNodesOnDrag: false,
          hover: true,
          hoverConnectedEdges: true,
          keyboard: {
            enabled: true,
            speed: { x: 10, y: 10, zoom: 0.02 },
            bindToWindow: true
          },
          multiselect: true,
          navigationButtons: true,
          selectable: true,
          selectConnectedEdges: true,
          tooltipDelay: 200,
          zoomView: true
        },
        layout: {
          improvedLayout: true,
          hierarchical: {
            enabled: false,
            levelSeparation: 150,
            nodeSpacing: 100,
            treeSpacing: 200,
            blockShifting: true,
            edgeMinimization: true,
            parentCentralization: true,
            direction: 'UD',
            sortMethod: 'hubsize',
            shakeTowards: 'leaves'
          }
        }
      };

      const mergedOptions = mergeDeep({}, defaultOptions, options);

      const network = new Network(containerRef.current, data, mergedOptions);
      networkRef.current = network;

      if (events.select) {
        network.on('select', events.select);
      }

      if (events.hoverNode) {
        network.on('hoverNode', events.hoverNode);
      }

      if (events.blurNode) {
        network.on('blurNode', events.blurNode);
      }

      if (events.click) {
        network.on('click', events.click);
      }

      if (events.doubleClick) {
        network.on('doubleClick', events.doubleClick);
      }

      if (events.oncontext) {
        network.on('oncontext', events.oncontext);
      }

      if (events.dragStart) {
        network.on('dragStart', events.dragStart);
      }

      if (events.dragging) {
        network.on('dragging', events.dragging);
      }

      if (events.dragEnd) {
        network.on('dragEnd', events.dragEnd);
      }

      if (events.zoom) {
        network.on('zoom', events.zoom);
      }

      if (events.showPopup) {
        network.on('hoverNode', (params: { node: string }) => {
          if (!containerRef.current) return;

          const popup = document.createElement('div');
          popup.className = 'network-tooltip';
          popup.innerHTML = events.showPopup?.(params.node) || '';

          const position = network.getPosition(params.node);
          const canvasPosition = network.canvasToDOM(position);

          popup.style.position = 'absolute';
          popup.style.left = `${canvasPosition.x + 10}px`;
          popup.style.top = `${canvasPosition.y - 10}px`;
          popup.style.pointerEvents = 'none';
          popup.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
          popup.style.color = 'white';
          popup.style.padding = '5px 10px';
          popup.style.borderRadius = '4px';
          popup.style.fontSize = '12px';
          popup.style.zIndex = '1000';
          popup.style.maxWidth = '200px';
          popup.style.wordWrap = 'break-word';

          containerRef.current.appendChild(popup);
        });

        network.on('blurNode', () => {
          if (!containerRef.current) return;
          const tooltip = containerRef.current.querySelector('.network-tooltip');
          if (tooltip) {
            containerRef.current.removeChild(tooltip);
          }
          events.hidePopup?.();
        });
      }

      network.once('stabilizationIterationsDone', () => {
        network.fit({
          animation: {
            duration: 1000,
            easingFunction: 'easeInOutQuad'
          }
        });
        setLoading(false);
      });

      return () => {
        network.off('select');
        network.off('hoverNode');
        network.off('blurNode');
        network.off('click');
        network.off('doubleClick');
        network.off('oncontext');
        network.off('dragStart');
        network.off('dragging');
        network.off('dragEnd');
        network.off('zoom');
        network.destroy();
      };
    } catch (err) {
      console.error('Error initializing network:', err);
      setError('Failed to initialize graph visualization');
      setLoading(false);
    }
  }, [graphData, options, events]);

  const mergeDeep = (target: any, ...sources: any[]): any => {
    if (!sources.length) return target;
    const source = sources.shift();

    if (isObject(target) && isObject(source)) {
      for (const key in source) {
        if (isObject(source[key])) {
          if (!target[key]) Object.assign(target, { [key]: {} });
          mergeDeep(target[key], source[key]);
        } else {
          Object.assign(target, { [key]: source[key] });
        }
      }
    }

    return mergeDeep(target, ...sources);
  };

  const isObject = (item: any): boolean => {
    return item && typeof item === 'object' && !Array.isArray(item);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 border border-gray-200 rounded-lg">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="relative h-96 border border-gray-200 rounded-lg overflow-hidden">
      <div 
        ref={containerRef} 
        className="w-full h-full"
        style={{ width: '100%', height: '100%' }}
      />
      {error && (
        <div className="absolute inset-0 bg-red-50 bg-opacity-90 flex items-center justify-center p-4">
          <div className="text-center">
            <p className="text-red-600 font-medium">Error loading graph</p>
            <p className="text-sm text-red-500 mt-1">{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-2 px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded text-sm"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}
    </div>
  )
})