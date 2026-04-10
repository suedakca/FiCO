import React, { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'

const APP_VERSION = "v4.0 ChatGPT Edition"

const INITIAL_MESSAGE = { 
  role: 'assistant', 
  content: 'Merhaba! Ben FiCo Kaşif. Katılım bankacılığı ve fıkhi uyum süreçlerinde size rehberlik etmek için buradayım. Bugün hangi konuyu keşfetmek istersiniz?\n\n*Not: Tüm yanıtlarım profesyonel uyum filtrelerinden geçerek puanlanmaktadır.*',
  evaluation: {
    hit_rate: 0.98,
    faithfulness: 0.95,
    citation_accuracy: 1.0
  }
}

function App() {
  const [messages, setMessages] = useState([INITIAL_MESSAGE])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [history, setHistory] = useState([])
  const [showThought, setShowThought] = useState(false)
  const scrollRef = useRef(null)
  const isFetchingRef = useRef(false)

  const fetchHistory = async () => {
    try {
      const resp = await fetch('http://localhost:8000/v1/query?user_id=demo_user')
      if (resp.ok) {
        const data = await resp.json()
        setHistory(data)
      }
    } catch (e) {
      console.error("History fetch error", e)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth"
      })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (text = input) => {
    const queryText = typeof text === 'string' ? text : input
    if (!queryText.trim() || isFetchingRef.current) return
    
    isFetchingRef.current = true
    setIsLoading(true)
    const msgId = Date.now()

    setMessages(prev => [...prev, 
      { id: msgId + 1, role: 'user', content: queryText },
      { id: msgId, role: 'assistant', content: '', isAnalyzing: true }
    ])
    setInput('')
    const startTime = Date.now()

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${baseUrl}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: queryText,
          mode: 'production'
        })
      })

      if (!response.ok) throw new Error('API Error')
      
      const data = await response.json()
      const duration = ((Date.now() - startTime) / 1000).toFixed(1)
      
      setMessages(prev => prev.map(msg => 
        msg.id === msgId ? {
          ...msg,
          isAnalyzing: false,
          content: data.answer || "Cevap üretilemedi.",
          sources: data.sources ? data.sources.map(s => s.metadata?.source || s.metadata?.rule_id || 'Kaynak Belgeler') : [],
          evaluation: {
            hit_rate: data.confidence || 0,
            faithfulness: data.confidence || 0,
            citation_accuracy: data.cache_hit ? 1.0 : 0.9
          },
          thought: data.decision_trace ? JSON.stringify(data.decision_trace, null, 2) : "Twin-Inference başarılı.",
          responseTime: duration,
          escalated: data.escalated,
          queryType: data.query_type
        } : msg
      ))

      fetchHistory()
    } catch (error) {
      console.error("API error", error)
      setMessages(prev => prev.map(msg => 
        msg.id === msgId ? {
          ...msg,
          isAnalyzing: false,
          content: 'Üzgünüm, şu an bağlantı kurulamıyor. Lütfen sistem yöneticinizle iletişime geçin.'
        } : msg
      ))
    } finally {
      setIsLoading(false)
      isFetchingRef.current = false
    }
  }

  const handleNewChat = () => {
    setMessages([INITIAL_MESSAGE])
    setInput('')
  }

  const handleSelectHistory = (h) => {
    const q = h.query || h.query_text;
    if (q) {
      handleSend(q);
    }
  }

  const suggestionChips = [
    { q: "Mudaraba'da zarar paylaşımı", icon: "⚖️" },
    { q: "Kripto varlık teminatı", icon: "🪙" },
    { q: "Vadeli sarf işlemleri", icon: "💱" },
    { q: "Konut finansmanı kârı", icon: "🏠" }
  ]

  return (
    <div className="layout-container font-sans text-brand-text">
      {/* Refined Ambient Overlay */}
      <div className="glow-overlay top-[-10%] left-[-10%]"></div>
      <div className="glow-overlay bottom-[-10%] right-[-10%] animate-pulse [animation-duration:8s]"></div>

      {/* Sidebar - Dusty Rose Professional */}
      <aside className={`sidebar transition-all duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full absolute z-40 h-full'}`}>
        <div className="p-5 flex flex-col h-full overflow-hidden">
          <div className="flex items-center gap-2.5 mb-8 px-1">
             <div className="w-8 h-8 rounded-lg bg-brand-primary flex items-center justify-center text-white text-[10px] font-black shadow-lg shadow-brand-primary/20">FK</div>
             <div className="font-extrabold text-[15px] tracking-tight uppercase text-brand-primary">FiCO Advisor</div>
          </div>

          <button 
            onClick={handleNewChat}
            className="flex items-center gap-2.5 p-3.5 w-full bg-white border border-brand-border rounded-xl text-[12px] font-bold text-brand-text hover:bg-brand-bg transition-all mb-8 group shadow-sm"
          >
             <svg className="w-4 h-4 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 4v16m8-8H4" /></svg>
             Yeni Sohbet Başlat
          </button>

          <nav className="flex-1 space-y-1 overflow-y-auto pr-2 custom-scrollbar">
            <div className="text-[9px] font-black text-brand-text-secondary uppercase tracking-[0.25em] px-2 py-4 mb-2">Arşiv</div>
            {history.length > 0 ? history.map((h, i) => (
              <button 
                key={h.id || i} 
                onClick={() => handleSelectHistory(h)}
                className="w-full text-left px-3 py-2.5 rounded-xl text-[12px] text-brand-text hover:bg-white hover:shadow-sm transition-all truncate font-semibold border border-transparent"
              >
                {h.query || h.query_text}
              </button>
            )) : (
              <div className="px-2 py-2 text-brand-text-secondary/40 text-[11px] italic">Geçmiş bulunmamaktadır.</div>
            )}
          </nav>

          <div className="mt-auto pt-6 border-t border-brand-border">
             <div className="flex items-center gap-3 p-3 bg-white/50 rounded-xl border border-brand-border">
                <div className="w-7 h-7 rounded-md bg-brand-primary/10 flex items-center justify-center text-brand-primary text-[9px] font-black">BA</div>
                <div className="flex flex-col">
                   <span className="text-brand-text text-[11px] font-bold">Banka Yetkilisi</span>
                   <span className="text-brand-text-secondary text-[9px] font-bold uppercase tracking-wider">Corporate Access</span>
                </div>
             </div>
          </div>
        </div>
      </aside>

      {/* Main Chat Main Area */}
      <main className="chat-main custom-scrollbar">
        {/* Minimal Header */}
        <header className="w-full h-14 flex items-center justify-between px-8 bg-brand-bg/90 backdrop-blur-md sticky top-0 z-30 border-b border-brand-border">
          <div className="flex items-center gap-6">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 hover:bg-white rounded-md transition-colors text-brand-text-secondary"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
            <div className="flex items-center gap-2">
               <span className="w-1.5 h-1.5 rounded-full bg-brand-primary" />
               <h1 className="font-bold text-[14px] text-brand-text tracking-tight">FiCO Danışman</h1>
            </div>
          </div>
          <div className="flex items-center gap-4">
             <div className="px-3 py-1 bg-white text-brand-text-secondary text-[9px] font-black rounded-full border border-brand-border uppercase tracking-widest shadow-sm">Live Node</div>
          </div>
        </header>

        {/* Vertical Scroll Area */}
        <div ref={scrollRef} className="flex-1 w-full overflow-y-auto custom-scrollbar flex flex-col pt-6">
          <div className="chat-content-limit px-8 pb-24 space-y-12">
            
            {messages.map((m, i) => (
              <div key={i} className={`flex flex-col w-full animate-message-in`} style={{ animationDelay: `${i * 0.05}s` }}>
                
                <div className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                  
                  {m.role === 'assistant' && (
                    <div className="flex items-center gap-2 mb-3 ml-2">
                       <div className="w-5 h-5 rounded bg-brand-primary flex items-center justify-center text-white text-[7px] font-black">FK</div>
                       <span className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-text-secondary">FiCO Advisors</span>
                    </div>
                  )}

                  <div className={m.role === 'user' ? 'message-user' : 'message-assistant'}>
                    <div className="prose-content">
                      {m.role === 'assistant' && !m.isAnalyzing && <span className="verdict-title inline-flex items-center gap-2">
                         UYUMLULUK HÜKMÜ
                      </span>}
                      
                      {m.content ? <ReactMarkdown>{m.content}</ReactMarkdown> : null}

                      {m.isAnalyzing && (
                        <div className="flex items-center gap-3 py-2">
                           <div className="flex gap-1.5">
                              <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse" />
                              <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse [animation-delay:0.2s]" />
                              <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse [animation-delay:0.4s]" />
                           </div>
                           <span className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-primary">Analiz Yürütülüyor...</span>
                        </div>
                      )}
                    </div>

                    {m.role === 'assistant' && !m.isAnalyzing && m.sources && m.sources.length > 0 && (
                      <div className="source-muted flex flex-wrap gap-x-4 gap-y-2">
                         <div className="font-black text-brand-primary uppercase tracking-widest text-[10px]">Referanslar:</div>
                         {m.sources.map((s, si) => (
                           <div key={si} className="flex items-center gap-1.5 text-brand-text-secondary font-bold group cursor-pointer hover:text-brand-primary transition-colors">
                              <span className="w-1 h-1 rounded-full bg-brand-border group-hover:bg-brand-primary" />
                              {s}
                           </div>
                         ))}
                      </div>
                    )}

                    {m.role === 'assistant' && !m.isAnalyzing && m.evaluation && (
                      <div className="mt-5 flex gap-6 border-t border-brand-border pt-4">
                         <div className="flex flex-col gap-0.5">
                            <div className="text-[8px] font-black text-brand-text-secondary uppercase tracking-widest">Güven Endeksi</div>
                            <div className="text-[11px] font-black text-brand-primary">%{Math.round(m.evaluation.hit_rate * 100)}</div>
                         </div>
                         <div className="flex flex-col gap-0.5">
                            <div className="text-[8px] font-black text-brand-text-secondary uppercase tracking-widest">Hız</div>
                            <div className="text-[11px] font-black text-brand-accent">{m.responseTime || "0.8"}s</div>
                         </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {messages.length === 1 && (
              <div className="grid grid-cols-2 gap-4 pt-16 animate-fade-in max-w-2xl mx-auto">
                {suggestionChips.map((chip, i) => (
                  <button 
                    key={i} 
                    onClick={() => handleSend(chip.q)}
                    className="p-5 text-left bg-white border border-brand-border rounded-2xl hover:border-brand-primary hover:shadow-lg transition-all group"
                  >
                    <div className="text-2xl mb-3 group-hover:scale-110 transition-transform origin-left">{chip.icon}</div>
                    <div className="text-[13px] font-bold text-brand-text">{chip.q}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sticky Input Dock */}
        <div className="input-area-sticky">
           <div className="chat-content-limit px-8">
              <div className="input-pill bg-white shadow-2xl shadow-slate-200">
                <input 
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Ürün yapısı veya mevzuat hakkında analiz başlatın..."
                  className="flex-1 bg-transparent border-none focus:ring-0 outline-none text-[15px] py-3.5 text-brand-text placeholder:text-brand-text-secondary/50 font-medium"
                />
                <button 
                  onClick={() => handleSend()}
                  disabled={isFetchingRef.current || !input.trim()}
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                    input.trim() ? 'bg-brand-primary text-white shadow-lg shadow-brand-primary/20 hover:scale-105' : 'bg-brand-bg text-brand-text-secondary/20'
                  }`}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 12h14M12 5l7 7-7 7" /></svg>
                </button>
              </div>
              <div className="text-center mt-4 text-[9px] text-brand-text-secondary font-bold uppercase tracking-[0.2em] opacity-50">
                FiCO v4.2 • Professional Identity • Trusted AI
              </div>
           </div>
        </div>
      </main>
    </div>
  )
}

export default App
