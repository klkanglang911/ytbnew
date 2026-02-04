import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

// 创建 API 实例
const api = axios.create({
  baseURL: API_BASE
})

export default function App() {
  const [activeTab, setActiveTab] = useState('bulk-import')
  const [message, setMessage] = useState(null)
  const [channels, setChannels] = useState([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState(null)

  // 标签页组件
  const tabs = [
    { id: 'bulk-import', label: '批量导入', icon: '📥' },
    { id: 'add-channel', label: '添加频道', icon: '➕' },
    { id: 'channel-list', label: '频道列表', icon: '📺' }
  ]

  useEffect(() => {
    loadChannels()
  }, [])

  // 加载频道列表
  const loadChannels = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/admin/channels/list')
      setChannels(response.data.channels || [])
      setStats(response.data.statistics || {})
    } catch (error) {
      showMessage('加载频道列表失败: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  // 显示消息
  const showMessage = (text, type = 'success') => {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 3000)
  }

  return (
    <div className="container">
      <div className="header">
        <h1>🎬 YouTube 直播频道管理</h1>
        <p>快速导入、管理和验证 YouTube 直播频道</p>
      </div>

      {message && (
        <div className={`message ${message.type} show`} style={{ marginTop: '20px', marginLeft: '30px', marginRight: '30px' }}>
          {message.text}
        </div>
      )}

      <div className="tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      <div className="tab-content" style={{ display: activeTab === 'bulk-import' ? 'block' : 'none' }}>
        <BulkImportTab onImport={loadChannels} onMessage={showMessage} />
      </div>

      <div className="tab-content" style={{ display: activeTab === 'add-channel' ? 'block' : 'none' }}>
        <AddChannelTab onAdd={loadChannels} onMessage={showMessage} />
      </div>

      <div className="tab-content" style={{ display: activeTab === 'channel-list' ? 'block' : 'none' }}>
        <ChannelListTab channels={channels} stats={stats} loading={loading} onRefresh={loadChannels} onDelete={loadChannels} onMessage={showMessage} />
      </div>
    </div>
  )
}

// 批量导入标签页
function BulkImportTab({ onImport, onMessage }) {
  const [input, setInput] = useState('')
  const [preview, setPreview] = useState(null)
  const [importing, setImporting] = useState(false)

  const handlePreview = async () => {
    if (!input.trim()) {
      onMessage('请输入 URL 或 M3U 内容', 'error')
      return
    }

    try {
      const response = await api.post('/api/admin/channels/import', { raw_input: input })
      setPreview(response.data)
    } catch (error) {
      onMessage('预览失败: ' + error.message, 'error')
    }
  }

  const handleImport = async () => {
    if (!preview) return

    try {
      setImporting(true)
      const importRequest = {
        channels: preview.channels,
        validate: true
      }

      const response = await api.post('/api/admin/channels/confirm-import', importRequest)
      onMessage('导入成功: ' + response.data.message, 'success')
      setInput('')
      setPreview(null)
      onImport()
    } catch (error) {
      onMessage('导入失败: ' + error.message, 'error')
    } finally {
      setImporting(false)
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: '20px', fontSize: '18px' }}>📥 批量导入频道</h2>

      <div className="form-group">
        <label>输入 URL 或 M3U 内容</label>
        <textarea
          placeholder="可粘贴以下格式：&#10;1. 单行 URL：https://www.youtube.com/watch?v=xxx&#10;2. M3U 格式：&#10;#EXTINF:-1 tvg-name=&#34;频道名&#34;,频道名&#10;https://www.youtube.com/watch?v=xxx"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
      </div>

      <div className="input-group">
        <button className="button button-primary" onClick={handlePreview} disabled={!input.trim()}>
          预览导入
        </button>
        <button className="button button-secondary" onClick={() => setInput('')}>
          清空
        </button>
      </div>

      {preview && (
        <div>
          <div className="preview-list">
            <div style={{ marginBottom: '15px', fontWeight: '600' }}>
              预览: {preview.total_count} 个 URL，新增 {preview.new_count} 个，重复 {preview.duplicate_count} 个
            </div>

            {preview.channels.map((ch, idx) => (
              <div key={idx} className="preview-item">
                <div>
                  <strong>{ch.name}</strong>
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                    {ch.url.substring(0, 60)}...
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="input-group">
            <button
              className="button button-primary"
              onClick={handleImport}
              disabled={importing || preview.new_count === 0}
            >
              {importing ? '导入中...' : `确认导入 ${preview.new_count} 个`}
            </button>
            <button className="button button-secondary" onClick={() => setPreview(null)}>
              取消
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// 添加频道标签页
function AddChannelTab({ onAdd, onMessage }) {
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    description: '',
    logo: ''
  })
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!formData.name.trim() || !formData.url.trim()) {
      onMessage('频道名称和 URL 为必填项', 'error')
      return
    }

    try {
      setLoading(true)
      const response = await api.post('/api/admin/channels/confirm-import', {
        channels: [formData],
        validate: true
      })

      onMessage('频道已添加: ' + response.data.message, 'success')
      setFormData({ name: '', url: '', description: '', logo: '' })
      onAdd()
    } catch (error) {
      onMessage('添加失败: ' + error.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: '20px', fontSize: '18px' }}>➕ 手动添加频道</h2>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>频道名称 *</label>
          <input
            type="text"
            name="name"
            placeholder="如：新闻直播"
            value={formData.name}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label>YouTube URL *</label>
          <input
            type="url"
            name="url"
            placeholder="https://www.youtube.com/watch?v=..."
            value={formData.url}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label>描述</label>
          <textarea
            name="description"
            placeholder="频道简介"
            value={formData.description}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label>Logo URL</label>
          <input
            type="url"
            name="logo"
            placeholder="https://..."
            value={formData.logo}
            onChange={handleChange}
          />
        </div>

        <div className="input-group">
          <button type="submit" className="button button-primary" disabled={loading}>
            {loading ? '添加中...' : '添加频道'}
          </button>
          <button
            type="button"
            className="button button-secondary"
            onClick={() => setFormData({ name: '', url: '', description: '', logo: '' })}
          >
            重置
          </button>
        </div>
      </form>
    </div>
  )
}

// 频道列表标签页
function ChannelListTab({ channels, stats, loading, onRefresh, onDelete, onMessage }) {
  const handleDelete = async (name) => {
    if (!confirm(`确定要删除频道 "${name}" 吗？`)) return

    try {
      await api.delete(`/api/admin/channels/${name}`)
      onMessage('频道已删除', 'success')
      onDelete()
    } catch (error) {
      onMessage('删除失败: ' + error.message, 'error')
    }
  }

  const getStatusBadge = (status) => {
    const statusMap = {
      'valid': { text: '✓ 正常', className: 'status-valid' },
      'invalid': { text: '✗ 无效', className: 'status-invalid' },
      'pending': { text: '⏳ 待验证', className: 'status-pending' }
    }
    const info = statusMap[status] || statusMap['pending']
    return <span className={`status-badge ${info.className}`}>{info.text}</span>
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '18px' }}>📺 频道列表</h2>
        <button className="button button-primary" onClick={onRefresh} disabled={loading}>
          {loading ? '刷新中...' : '刷新'}
        </button>
      </div>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>总频道数</h3>
            <div className="value">{stats.total || 0}</div>
          </div>
          <div className="stat-card">
            <h3>正常</h3>
            <div className="value" style={{ color: '#10b981' }}>{stats.valid || 0}</div>
          </div>
          <div className="stat-card">
            <h3>无效</h3>
            <div className="value" style={{ color: '#ef4444' }}>{stats.invalid || 0}</div>
          </div>
          <div className="stat-card">
            <h3>待验证</h3>
            <div className="value" style={{ color: '#f59e0b' }}>{stats.pending || 0}</div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">
          <div className="spinner" style={{ marginRight: '10px' }}></div>
          加载中...
        </div>
      ) : channels.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
          暂无频道，请先导入或添加
        </div>
      ) : (
        <div className="channel-list">
          <table>
            <thead>
              <tr>
                <th>频道名称</th>
                <th>URL</th>
                <th>描述</th>
                <th>验证状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {channels.map((ch, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: '500' }}>{ch.name}</td>
                  <td style={{ fontSize: '12px', maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {ch.url}
                  </td>
                  <td style={{ fontSize: '12px', color: '#666' }}>{ch.description || '-'}</td>
                  <td>{getStatusBadge(ch.validation_status || 'pending')}</td>
                  <td>
                    <div className="action-buttons">
                      <button className="button button-danger" onClick={() => handleDelete(ch.name)}>
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
