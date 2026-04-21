import React, { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'

const INITIAL_MESSAGE = {
  id: 'SYSTEM_INIT',
  role: 'assistant',
  content: 'Hoş geldiniz. Ben FiCO. Finansal hedeflerinize ve mevzuat uyum süreçlerinize rehberlik eden Fihri\'nin dijital mirasındayız.\n\nBugün hangi finansal öngörüye ihtiyacınız var?',
  reportId: 'OASIS-001',
  tag: 'SYSTEM_READY'
}

const TEMPLATES = [
  { q: 'Kripto varlık teminatlı finansman analizi', icon: '💎' },
  { q: "Mudaraba sözleşmelerinde zarar tazmin hükümleri", icon: '📄' },
  { q: 'Katılım esaslı fonlarda arındırma süreci', icon: '✨' },
  { q: 'Gecikme cezası (Ceza-i Şart) modelleri', icon: '⚠️' },
]

export default function App() {
  const [messages, setMessages]   = useState([INITIAL_MESSAGE])
  const [input, setInput]         = useState('')
  const [history, setHistory]     = useState([])
  const [activeTab, setActiveTab] = useState('hub')
  const scrollRef   = useRef(null)
  const isFetchingRef = useRef(false)

  const fetchHistory = async () => {
    try {
      const b = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const r = await fetch(`${b}/v1/query?user_id=demo_user`)
      if (r.ok) {
        const data = await r.json()
        if (Array.isArray(data)) setHistory(data)
      }
    } catch {}
  }

  useEffect(() => { fetchHistory() }, [])
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const analyze = async (text = input) => {
    const q = typeof text === 'string' ? text : input
    if (!q.trim() || isFetchingRef.current) return
    isFetchingRef.current = true
    const id = Date.now()
    const startTime = performance.now()
    setActiveTab('hub') 
    
    setMessages(p => {
      // If we only have the system init message, replace it entirely
      if (p.length === 1 && p[0].id === 'SYSTEM_INIT') {
        return [
          { id: id + 1, role: 'user', content: q },
          { id, role: 'assistant', content: '', isAnalyzing: true, reportId: 'BEKLENİYOR', totalTime: null }
        ]
      }
      // Otherwise append as usual
      return [...p,
        { id: id + 1, role: 'user', content: q },
        { id, role: 'assistant', content: '', isAnalyzing: true, reportId: 'BEKLENİYOR', totalTime: null }
      ]
    })
    setInput('')

    try {
      const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${base}/v1/query/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'demo_user', query_text: q })
      })

      if (!response.ok) throw new Error('STREAM_API_ERROR')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullContent = ''
      let streamBuffer = '' // Robust buffer for metadata detection
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          // Final safety break
          setMessages(p => p.map(m => m.id === id ? { ...m, isAnalyzing: false } : m))
          break
        }

        const chunk = decoder.decode(value, { stream: true })
        streamBuffer += chunk
        
        // Timer stop marker: Text generation is done, scoring starting
        if (streamBuffer.includes('[GENERATION_DONE]')) {
           const parts = streamBuffer.split('[GENERATION_DONE]')
           const currentText = parts[0].trim()
           
           setMessages(prev => prev.map(m => {
             if (m.id === id && m.totalTime === null) {
               const capturedTime = ((performance.now() - startTime) / 1000).toFixed(1)
               return { ...m, content: currentText, totalTime: capturedTime, reportId: 'DEĞERLENDİRİLİYOR' }
             }
             return m.id === id ? { ...m, content: currentText } : m
           }))
           fullContent = currentText
        }

        // Final metadata arrival
        if (streamBuffer.includes('[METADATA]')) {
          const parts = streamBuffer.split('[METADATA]')
          const textBeforeMeta = parts[0].split('[GENERATION_DONE]')[0].trim()
          fullContent = textBeforeMeta
          
          try {
            const meta = JSON.parse(parts[1])
            setMessages(p => p.map(m => m.id === id ? {
              ...m, 
              isAnalyzing: false, 
              content: fullContent,
              totalTime: m.totalTime !== null ? m.totalTime : ((performance.now() - startTime) / 1000).toFixed(1),
              sources: meta.source_urls || [],
              tag:     meta.type?.toUpperCase() || 'ANALİZ',
              confidence: Math.round((meta.confidence_score || 0.9) * 100),
              reportId: `OA-${Math.floor(Date.now()/1000).toString(16).toUpperCase()}`
            } : m))
          } catch (e) {
             setMessages(p => p.map(m => m.id === id ? { ...m, isAnalyzing: false, content: fullContent, reportId: 'TAMAMLANDI' } : m))
          }
          break 
        } else if (!streamBuffer.includes('[GENERATION_DONE]')) {
          // Normal stream flow (before any markers)
          fullContent = streamBuffer
          setMessages(p => p.map(m => m.id === id ? { ...m, isAnalyzing: false, content: fullContent } : m))
        }
      }
      fetchHistory()
    } catch (e) {
      setMessages(p => p.map(m => m.id === id ? {
        ...m, isAnalyzing: false, 
        content: 'Sistem şu an çok yoğun. Lütfen Macbook fanları sakinleşince tekrar deneyin.',
      } : m))
    } finally { 
      isFetchingRef.current = false 
    }
  }

  const inSession = messages.length > 1

  return (
    <div className="oasis-container">

      {/* ── Floating Oasis Portal ── */}
      <nav className="oasis-nav">
        <div className="nav-logo">F</div>
        <button className={`nav-icon-btn ${activeTab === 'hub' ? 'active' : ''}`} onClick={() => setActiveTab('hub')}>
           <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
        </button>
        <button className={`nav-icon-btn ${activeTab === 'reports' ? 'active' : ''}`} onClick={() => setActiveTab('reports')}>
           <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        </button>
        <button className="nav-icon-btn" style={{marginTop: 'auto'}}>
           <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
        </button>
      </nav>

      {/* ── Main Oasis Stage ── */}
      <main className="oasis-stage">
        <header className="stage-header">
          <div className="hub-indicator">
            <span style={{width:'8px', height:'8px', borderRadius:'50%', background:'var(--color-primary)', boxShadow:'0 0 10px var(--color-primary)'}} />
            Fihri Collective · Oasis Portalı {activeTab === 'reports' && '· Arşiv'}
          </div>
          <div className="user-profile" style={{display:'flex', alignItems:'center', gap:'12px'}}>
             <div style={{textAlign:'right'}}>
                <div style={{fontSize:'13px', fontWeight:700}}>Denetçi Kullanıcı</div>
                <div style={{fontSize:'10px', color:'var(--text-soft)', textTransform:'uppercase'}}>Profesyonel Seviye 4</div>
             </div>
             <div style={{width:'40px', height:'40px', borderRadius:'50%', background:'linear-gradient(135deg, #10B981, #C8922A)', border:'2px solid #fff', boxShadow:'0 4px 12px rgba(0,0,0,0.1)'}} />
          </div>
        </header>

        <div className="oasis-scroll" ref={scrollRef}>
          <div className="oasis-canvas">

            {activeTab === 'reports' ? (
              <div className="archive-stage">
                <h2 style={{fontSize:'32px', fontWeight:800, marginBottom:'32px'}}>Denetim <span>Arşivi</span></h2>
                <div className="archive-grid" style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(300px, 1fr))', gap:'20px'}}>
                  {history.length > 0 ? history.map((h, i) => (
                    <div key={h.id || i} className="archive-item" onClick={() => analyze(h.query || h.query_text)}>
                      <div className="archive-item-meta">Rapor · {h.id || i+1}</div>
                      <div className="archive-item-query">{h.query || h.query_text}</div>
                    </div>
                  )) : (
                    <div style={{gridColumn:'1/-1', textAlign:'center', padding:'100px 20px', opacity:0.6, background:'var(--surface-glass)', borderRadius:'30px', border:'1px dashed var(--color-primary)'}}>
                      <div style={{fontSize:'40px', marginBottom:'16px'}}>📭</div>
                      <div style={{fontSize:'15px', fontWeight:700}}>Henüz bir denetim raporu oluşturulmamış.</div>
                      <div style={{fontSize:'13px'}}>Yeni bir analiz başlatarak arşivi doldurabilirsiniz.</div>
                    </div>
                  )}
                </div>
              </div>
            ) : !inSession ? (
              <div className="hero-oasis">
                <div className="oasis-greeting">FiCO'ya Tekrar Hoş Geldiniz</div>
                <h1 className="oasis-title">
                  Fihri'nin <span>Dijital Mirası</span> <br/> Burada Başlıyor.
                </h1>
                <p className="oasis-sub">
                  Analize başlamak için aşağıdaki hazır şablonlardan birini seçin 
                  veya aklınızdaki soruyu aşağıya yazın.
                </p>
                
                <div className="oasis-grid">
                  {TEMPLATES.map((t, i) => (
                    <button key={i} className="oasis-pill-btn" onClick={() => analyze(t.q)}>
                      <div className="pill-icon">{t.icon}</div>
                      <div className="pill-text">{t.q}</div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bloom-feed">
                {messages.map((m, i) => (
                  m.role === 'user' ? (
                    <div key={m.id} className="request-pill">
                      <div className="pill-content">{m.content}</div>
                    </div>
                  ) : (
                    <div key={m.id || i} className="oasis-module">
                      <div className="module-glass">
                        <div className="module-header">
                          <div className="module-title">Analiz · {m.reportId || 'BEKLENİYOR'}</div>
                          <div className="module-tag">{m.tag || 'ANALİZ'}</div>
                        </div>

                        <div className="module-body">
                          {m.isAnalyzing ? (
                            <div className="bloom-loader">
                              <div className="bloom-ring" />
                              <div className="bloom-label">Fihri Bilgi Bankası Taranıyor...</div>
                            </div>
                          ) : (
                            <div className="prose-oasis">
                              <ReactMarkdown>{m.content}</ReactMarkdown>
                              
                              <div className="sources-v3" style={{marginTop:'32px', display:'flex', flexWrap:'wrap', gap:'12px'}}>
                                {(m.sources && m.sources.length > 0) ? m.sources.map((s, si) => (
                                  <div key={`${m.id}-src-${si}`} style={{padding:'8px 16px', borderRadius:'12px', background:'var(--color-primary-soft)', color:'var(--text-mint)', fontSize:'11px', fontWeight:700}}>
                                    {s.split('/').pop()}
                                  </div>
                                )) : m.reportId === 'PENDING' ? (
                                  <div style={{fontSize:'11px', color:'var(--text-soft)', fontStyle:'italic'}}>Kaynaklar taranıyor...</div>
                                ) : null}
                              </div>
                            </div>
                          )}
                        </div>

                        {(m.reportId && (m.reportId !== 'PENDING' || !m.isAnalyzing)) && (
                          <div className="module-footer" style={{padding:'20px 32px', background:'rgba(255,255,255,0.4)', borderTop:'1px solid var(--border-glass)', display:'flex', justifyContent:'space-between'}}>
                             <div className="footer-metric" style={{display:'flex', gap:'32px'}}>
                                <div>
                                   <div style={{fontSize:'9px', fontWeight:800, color:'var(--text-soft)', textTransform:'uppercase'}}>Güven Oranı</div>
                                   <div style={{fontSize:'16px', fontWeight:800, color:'var(--color-primary)'}}>
                                      {['BEKLENİYOR', 'DEĞERLENDİRİLİYOR'].includes(m.reportId) ? '...' : `${m.confidence}%`}
                                   </div>
                                </div>
                                <div>
                                   <div style={{fontSize:'9px', fontWeight:800, color:'var(--text-soft)', textTransform:'uppercase'}}>Analiz Süresi</div>
                                   <div style={{fontSize:'16px', fontWeight:800, color:'var(--color-primary)'}}>
                                      {m.reportId === 'BEKLENİYOR' ? 'Ölçülüyor...' : `${m.totalTime || 0} sn`}
                                   </div>
                                </div>
                                <div>
                                   <div style={{fontSize:'9px', fontWeight:800, color:'var(--text-soft)', textTransform:'uppercase'}}>Durum</div>
                                   <div style={{fontSize:'16px', fontWeight:800, color:'var(--color-primary)'}}>
                                      {m.reportId === 'BEKLENİYOR' ? 'DOĞRULANIYOR' : 'DOĞRULANDI'}
                                   </div>
                                </div>
                             </div>
                             <div className="footer-brand" style={{fontSize:'10px', fontWeight:800, color:'var(--color-accent)', textTransform:'uppercase', display:'flex', alignItems:'center', gap:'8px'}}>
                                <svg width="14" height="14" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M2.166 4.9L10 .3l7.834 4.6a1 1 0 01.5 1.175l-2.263 8.361a1 1 0 01-.767.74l-5.304 2.122-5.304-2.122a1 1 0 01-.767-.74L1.666 6.075a1 1 0 01.5-1.175zM10 3.033L4.694 6.13l1.861 6.877L10 14.593l3.445-1.586 1.861-6.877L10 3.033zM13 8a1 1 0 10-2 0 1 1 0 002 0zM7 8a1 1 0 10-2 0 1 1 0 002 0z" clipRule="evenodd"/></svg>
                                FiCO • Fihri Collective
                             </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── Oasis Input Zone ── */}
        <div className="oasis-input-zone">
          <div className="oasis-input-wrap">
            <input 
              className="oasis-field" 
              placeholder="Yeni bir finansal ufuk keşfedin..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && analyze()}
            />
            <button 
              className="btn-bloom"
              onClick={() => analyze()}
              disabled={isFetchingRef.current || !input.trim()}
            >
              <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 5l7 7-7 7M5 5l7 7-7 7"/></svg>
            </button>
          </div>
        </div>

      </main>
    </div>
  )
}
