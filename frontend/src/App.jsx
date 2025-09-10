import React, { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001'

function MetricCard({ title, value, suffix, trend, icon }){
  return (
    <div style={{
      border: '1px solid #e5e7eb', 
      padding: '20px', 
      borderRadius: '16px', 
      boxShadow: '0 4px 6px rgba(0,0,0,0.05)',
      background: 'linear-gradient(135deg, #ffffff 0%, #f9fafb 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div style={{
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'flex-start',
        marginBottom: '8px'
      }}>
        <div style={{fontSize: '13px', color: '#6b7280', fontWeight: 500}}>{title}</div>
        {icon && <div style={{fontSize: '20px', opacity: 0.6}}>{icon}</div>}
      </div>
      <div style={{
        fontSize: '32px', 
        fontWeight: 700, 
        color: '#111827',
        lineHeight: 1
      }}>
        {value}{suffix || ''}
      </div>
      {trend && (
        <div style={{
          fontSize: '12px', 
          color: trend.startsWith('+') ? '#059669' : '#dc2626',
          marginTop: '4px',
          fontWeight: 500
        }}>
          {trend}
        </div>
      )}
    </div>
  )
}

function StatusPill({ s, size = 'sm' }){
  const colors = {
    success: { bg: '#22c55e', text: '#ffffff' },
    failure: { bg: '#ef4444', text: '#ffffff' },
    cancelled: { bg: '#6b7280', text: '#ffffff' },
    in_progress: { bg: '#3b82f6', text: '#ffffff' }
  }
  const color = colors[s] || colors.cancelled
  const padding = size === 'lg' ? '6px 12px' : '3px 8px'
  const fontSize = size === 'lg' ? '13px' : '11px'
  
  return (
    <span style={{
      background: color.bg, 
      color: color.text, 
      padding: padding, 
      borderRadius: '9999px', 
      fontSize: fontSize,
      fontWeight: 500,
      textTransform: 'capitalize'
    }}>
      {s.replace('_', ' ')}
    </span>
  )
}

function LogsModal({ build, onClose }) {
  if (!build) return null
  
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: '#ffffff',
        borderRadius: '12px',
        padding: '24px',
        maxWidth: '800px',
        maxHeight: '600px',
        width: '90%',
        boxShadow: '0 20px 25px rgba(0,0,0,0.1)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          borderBottom: '1px solid #e5e7eb',
          paddingBottom: '16px'
        }}>
          <h3 style={{margin: 0, color: '#111827'}}>
            Build Logs - {build.pipeline} ({build.repo})
          </h3>
          <button 
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#6b7280'
            }}
          >
            ×
          </button>
        </div>
        <div style={{marginBottom: '16px'}}>
          <div style={{display: 'flex', gap: '16px', flexWrap: 'wrap'}}>
            <span><strong>Status:</strong> <StatusPill s={build.status} size="lg" /></span>
            <span><strong>Duration:</strong> {build.duration_seconds ? `${Math.round(build.duration_seconds)}s` : 'N/A'}</span>
            <span><strong>Started:</strong> {new Date(build.started_at).toLocaleString()}</span>
          </div>
        </div>
        <div style={{
          background: '#1f2937',
          color: '#f9fafb',
          padding: '16px',
          borderRadius: '8px',
          fontFamily: 'Monaco, Consolas, "Courier New", monospace',
          fontSize: '13px',
          lineHeight: 1.5,
          maxHeight: '300px',
          overflow: 'auto',
          whiteSpace: 'pre-wrap'
        }}>
          {build.logs || 'No logs available for this build.'}
        </div>
        {build.url && (
          <div style={{marginTop: '16px', textAlign: 'center'}}>
            <a 
              href={build.url} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{
                background: '#3b82f6',
                color: '#ffffff',
                padding: '8px 16px',
                borderRadius: '8px',
                textDecoration: 'none',
                fontWeight: 500
              }}
            >
              View Full Build →
            </a>
          </div>
        )}
      </div>
    </div>
  )
}

export default function App(){
  const [summary, setSummary] = useState(null)
  const [builds, setBuilds] = useState([])
  const [wsConnected, setWsConnected] = useState(false)
  const [selectedBuild, setSelectedBuild] = useState(null)
  const [timeWindow, setTimeWindow] = useState('7d')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async (window = timeWindow) => {
    try {
      setLoading(true)
      setError(null)
      const [s, b] = await Promise.all([
        axios.get(`${BACKEND_URL}/metrics/summary?window=${window}`),
        axios.get(`${BACKEND_URL}/builds?limit=50`)
      ])
      setSummary(s.data)
      setBuilds(b.data)
    } catch (err) {
      setError('Failed to load data. Please check if the backend is running.')
      console.error('Load error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleTimeWindowChange = (newWindow) => {
    setTimeWindow(newWindow)
    load(newWindow)
  }

  useEffect(() => { 
    load() 
  }, [])

  useEffect(() => {
    const ws = new WebSocket(`${BACKEND_URL.replace('http', 'ws')}/ws`)
    ws.onopen = () => setWsConnected(true)
    ws.onclose = () => setWsConnected(false)
    ws.onerror = () => setWsConnected(false)
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.event === 'build_ingested') {
          load() // Refresh data when new build is ingested
        }
      } catch (err) {
        console.warn('WebSocket message parsing error:', err)
      }
    }
    return () => ws.close()
  }, [timeWindow])

  const chartData = useMemo(() => {
    const copy = [...builds].reverse().slice(-20) // Last 20 builds for better chart visibility
    return copy.map((b, index) => ({
      name: `Build ${index + 1}`,
      fullName: new Date(b.started_at).toLocaleString(),
      duration: b.duration_seconds || 0,
      status: b.status,
      pipeline: b.pipeline
    }))
  }, [builds])

  const pieChartData = useMemo(() => {
    if (!summary) return []
    return [
      { name: 'Success', value: summary.success_rate, color: '#22c55e' },
      { name: 'Failure', value: summary.failure_rate, color: '#ef4444' }
    ]
  }, [summary])

  const lastStatus = summary ? Object.entries(summary.last_status_by_pipeline).map(([k,v]) => ({pipeline: k, status: v})) : []

  const formatBuildTime = (seconds) => {
    if (!seconds) return 'N/A'
    if (seconds < 60) return `${Math.round(seconds)}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.round(seconds % 60)
    return `${minutes}m ${remainingSeconds}s`
  }

  if (loading && !summary) {
    return (
      <div style={{
        fontFamily: 'Inter, system-ui, Arial',
        padding: '24px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: '#f9fafb'
      }}>
        <div style={{textAlign: 'center'}}>
          <div style={{fontSize: '18px', color: '#6b7280'}}>Loading dashboard...</div>
        </div>
      </div>
    )
  }

  return (
    <div style={{
      fontFamily: 'Inter, system-ui, Arial', 
      padding: '24px', 
      minHeight: '100vh',
      background: '#f9fafb'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '24px'
      }}>
        <div>
          <h1 style={{
            margin: 0, 
            fontSize: '28px', 
            fontWeight: 700, 
            color: '#111827'
          }}>
            CI/CD Pipeline Health Dashboard
          </h1>
          <p style={{
            margin: '4px 0 0 0', 
            color: '#6b7280', 
            fontSize: '14px'
          }}>
            Real-time monitoring of your CI/CD pipelines
          </p>
        </div>
        
        <div style={{display: 'flex', alignItems: 'center', gap: '16px'}}>
          {/* Time window selector */}
          <select 
            value={timeWindow}
            onChange={(e) => handleTimeWindowChange(e.target.value)}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              background: '#ffffff',
              fontSize: '14px'
            }}
          >
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
          
          {/* Live status */}
          <div style={{
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            padding: '8px 12px',
            background: wsConnected ? '#ecfdf5' : '#fef2f2',
            border: `1px solid ${wsConnected ? '#a7f3d0' : '#fecaca'}`,
            borderRadius: '8px'
          }}>
            <div style={{
              width: '8px', 
              height: '8px', 
              borderRadius: '50%',
              background: wsConnected ? '#22c55e' : '#ef4444'
            }}></div>
            <span style={{
              fontSize: '12px', 
              fontWeight: 500,
              color: wsConnected ? '#065f46' : '#991b1b'
            }}>
              {wsConnected ? 'Live Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div style={{
          background: '#fef2f2',
          border: '1px solid #fecaca',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '24px',
          color: '#991b1b'
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* Metrics Cards */}
      <div style={{
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
        gap: '16px',
        marginBottom: '24px'
      }}>
        <MetricCard 
          title={`Success Rate (${timeWindow})`}
          value={summary ? summary.success_rate.toFixed(1) : '--'}
          suffix="%" 
          icon="✅"
        />
        <MetricCard 
          title={`Failure Rate (${timeWindow})`}
          value={summary ? summary.failure_rate.toFixed(1) : '--'}
          suffix="%" 
          icon="❌"
        />
        <MetricCard 
          title="Average Build Time"
          value={summary && summary.avg_build_time ? formatBuildTime(summary.avg_build_time) : '--'}
          icon="⏱️"
        />
        <MetricCard 
          title="Total Builds"
          value={builds.length}
          icon="📊"
        />
      </div>

      {/* Visualization Panels */}
      <div style={{
        display: 'grid', 
        gridTemplateColumns: '2fr 1fr', 
        gap: '24px',
        marginBottom: '24px'
      }}>
        {/* Build Duration Trend Chart */}
        <div style={{
          border: '1px solid #e5e7eb', 
          borderRadius: '16px', 
          padding: '20px',
          background: '#ffffff',
          boxShadow: '0 4px 6px rgba(0,0,0,0.05)'
        }}>
          <h3 style={{
            margin: '0 0 16px 0', 
            fontSize: '18px', 
            fontWeight: 600, 
            color: '#111827'
          }}>
            Build Duration Trend
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="name" 
                tick={{fontSize: 12, fill: '#6b7280'}}
                tickLine={{stroke: '#e5e7eb'}}
              />
              <YAxis 
                tick={{fontSize: 12, fill: '#6b7280'}}
                tickLine={{stroke: '#e5e7eb'}}
                label={{value: 'Duration (s)', angle: -90, position: 'insideLeft'}}
              />
              <Tooltip 
                content={({active, payload}) => {
                  if (active && payload && payload[0]) {
                    const data = payload[0].payload
                    return (
                      <div style={{
                        background: '#ffffff',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        padding: '8px 12px',
                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                      }}>
                        <div style={{fontWeight: 600}}>{data.pipeline}</div>
                        <div>Duration: {formatBuildTime(data.duration)}</div>
                        <div>Status: <StatusPill s={data.status} /></div>
                        <div style={{fontSize: '12px', color: '#6b7280'}}>{data.fullName}</div>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Line 
                type="monotone" 
                dataKey="duration" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{fill: '#3b82f6', strokeWidth: 2, r: 4}}
                activeDot={{r: 6, fill: '#1d4ed8'}}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Success/Failure Rate Pie Chart */}
        <div style={{
          border: '1px solid #e5e7eb', 
          borderRadius: '16px', 
          padding: '20px',
          background: '#ffffff',
          boxShadow: '0 4px 6px rgba(0,0,0,0.05)'
        }}>
          <h3 style={{
            margin: '0 0 16px 0', 
            fontSize: '18px', 
            fontWeight: 600, 
            color: '#111827'
          }}>
            Success vs Failure Rate
          </h3>
          {pieChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  dataKey="value"
                  label={({name, value}) => `${name}: ${value.toFixed(1)}%`}
                >
                  {pieChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`${value.toFixed(1)}%`, '']} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{
              height: '300px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#6b7280'
            }}>
              No data available
            </div>
          )}
        </div>
      </div>

      {/* Pipeline Status Summary */}
      <div style={{
        border: '1px solid #e5e7eb', 
        borderRadius: '16px', 
        padding: '20px',
        background: '#ffffff',
        boxShadow: '0 4px 6px rgba(0,0,0,0.05)',
        marginBottom: '24px'
      }}>
        <h3 style={{
          margin: '0 0 16px 0', 
          fontSize: '18px', 
          fontWeight: 600, 
          color: '#111827'
        }}>
          Last Status by Pipeline
        </h3>
        {lastStatus.length > 0 ? (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            gap: '12px'
          }}>
            {lastStatus.map((r, i) => (
              <div key={i} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px 16px',
                background: '#f9fafb',
                borderRadius: '8px',
                border: '1px solid #e5e7eb'
              }}>
                <span style={{fontWeight: 500, color: '#374151'}}>{r.pipeline}</span>
                <StatusPill s={r.status} />
              </div>
            ))}
          </div>
        ) : (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: '#6b7280'
          }}>
            No pipeline data available yet
          </div>
        )}
      </div>

      {/* Latest Builds Table */}
      <div style={{
        border: '1px solid #e5e7eb', 
        borderRadius: '16px', 
        padding: '20px',
        background: '#ffffff',
        boxShadow: '0 4px 6px rgba(0,0,0,0.05)'
      }}>
        <h3 style={{
          margin: '0 0 16px 0', 
          fontSize: '18px', 
          fontWeight: 600, 
          color: '#111827'
        }}>
          Latest Builds & Logs
        </h3>
        
        {builds.length > 0 ? (
          <div style={{overflowX: 'auto'}}>
            <table style={{
              width: '100%', 
              borderCollapse: 'collapse',
              fontSize: '14px'
            }}>
              <thead>
                <tr style={{borderBottom: '2px solid #e5e7eb'}}>
                  <th style={{padding: '12px 8px', textAlign: 'left', fontWeight: 600, color: '#374151'}}>Time</th>
                  <th style={{padding: '12px 8px', textAlign: 'left', fontWeight: 600, color: '#374151'}}>Pipeline</th>
                  <th style={{padding: '12px 8px', textAlign: 'left', fontWeight: 600, color: '#374151'}}>Provider</th>
                  <th style={{padding: '12px 8px', textAlign: 'left', fontWeight: 600, color: '#374151'}}>Repo/Branch</th>
                  <th style={{padding: '12px 8px', textAlign: 'left', fontWeight: 600, color: '#374151'}}>Duration</th>
                  <th style={{padding: '12px 8px', textAlign: 'left', fontWeight: 600, color: '#374151'}}>Status</th>
                  <th style={{padding: '12px 8px', textAlign: 'left', fontWeight: 600, color: '#374151'}}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {builds.map((b, index) => (
                  <tr 
                    key={b.id}
                    style={{
                      borderBottom: '1px solid #f3f4f6',
                      background: index % 2 === 0 ? '#ffffff' : '#f9fafb'
                    }}
                  >
                    <td style={{padding: '12px 8px', color: '#6b7280'}}>
                      {new Date(b.started_at).toLocaleDateString()} <br/>
                      <span style={{fontSize: '12px'}}>
                        {new Date(b.started_at).toLocaleTimeString()}
                      </span>
                    </td>
                    <td style={{padding: '12px 8px', fontWeight: 500, color: '#374151'}}>
                      {b.pipeline}
                    </td>
                    <td style={{padding: '12px 8px'}}>
                      <span style={{
                        background: b.provider === 'github' ? '#f0f9ff' : '#fef3c7',
                        color: b.provider === 'github' ? '#0369a1' : '#92400e',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 500
                      }}>
                        {b.provider}
                      </span>
                    </td>
                    <td style={{padding: '12px 8px', color: '#6b7280'}}>
                      <div>{b.repo}</div>
                      <div style={{fontSize: '12px', color: '#9ca3af'}}>
                        {b.branch}
                      </div>
                    </td>
                    <td style={{padding: '12px 8px', color: '#6b7280'}}>
                      {formatBuildTime(b.duration_seconds)}
                    </td>
                    <td style={{padding: '12px 8px'}}>
                      <StatusPill s={b.status} />
                    </td>
                    <td style={{padding: '12px 8px'}}>
                      <div style={{display: 'flex', gap: '8px'}}>
                        {b.logs && (
                          <button
                            onClick={() => setSelectedBuild(b)}
                            style={{
                              background: '#f3f4f6',
                              border: '1px solid #d1d5db',
                              padding: '4px 8px',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontSize: '12px',
                              fontWeight: 500,
                              color: '#374151'
                            }}
                          >
                            📄 Logs
                          </button>
                        )}
                        {b.url && (
                          <a 
                            href={b.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={{
                              background: '#3b82f6',
                              color: '#ffffff',
                              padding: '4px 8px',
                              borderRadius: '6px',
                              textDecoration: 'none',
                              fontSize: '12px',
                              fontWeight: 500
                            }}
                          >
                            🔗 View
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{
            textAlign: 'center',
            padding: '60px 20px',
            color: '#6b7280'
          }}>
            <div style={{fontSize: '48px', marginBottom: '16px'}}>📊</div>
            <div style={{fontSize: '18px', fontWeight: 500, marginBottom: '8px'}}>
              No builds found
            </div>
            <div style={{fontSize: '14px'}}>
              Start ingesting CI/CD data to see your pipeline builds here
            </div>
          </div>
        )}
      </div>

      {/* Logs Modal */}
      {selectedBuild && (
        <LogsModal 
          build={selectedBuild} 
          onClose={() => setSelectedBuild(null)} 
        />
      )}
    </div>
  )
}
