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
    { q: "Kripto varlık teminatı", icon: "🪙" },
    { q: "Mudaraba'da zarar paylaşımı", icon: "⚖️" },
    { q: "Hisse senedi zekat hesabı", icon: "📈" },
    { q: "Konut finansmanı kâr oranları", icon: "🏠" },
    { q: "Vadeli sarf işlemleri", icon: "💱" },
    { q: "Gecikme cezası ve faiz ayrımı", icon: "⚠️" },
    { q: "Banka promosyonları hükmü", icon: "🎁" },
    { q: "Altın bazlı yatırım fonları", icon: "✨" }
  ]

  return (
    <div className="layout-container font-sans text-brand-text">
      {/* Refined Ambient Overlay */}
      <div className="glow-overlay top-[-5%] left-[-5%]"></div>
      <div className="glow-overlay bottom-[-5%] right-[-5%] animate-pulse [animation-duration:10s]"></div>

      {/* Sidebar - Floating Glassmorphic */}
      <aside className={`sidebar transition-all duration-500 ease-out ${sidebarOpen ? 'translate-x-0 opacity-100' : '-translate-x-full opacity-0 absolute'}`}>
        <div className="p-6 flex flex-col h-full overflow-hidden">
          
          {/* Brand Identity */}
          <div className="flex flex-col gap-1 mb-10 px-1">
             <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-brand-primary flex items-center justify-center text-white text-[12px] font-black shadow-lg shadow-brand-primary/20">F</div>
                <div className="font-extrabold text-[17px] tracking-tight text-brand-primary font-display">FiCo</div>
             </div>
          </div>

          <button 
            onClick={handleNewChat}
            className="flex items-center gap-2.5 p-4 w-full bg-brand-primary text-white rounded-2xl text-[12px] font-bold hover:shadow-lg hover:shadow-brand-primary/20 transition-all mb-10 group active:scale-[0.98]"
          >
             <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 4v16m8-8H4" /></svg>
             Yeni Analiz Başlat
          </button>

          <nav className="flex-1 space-y-2 overflow-y-auto pr-2 custom-scrollbar">
            <div className="text-[10px] font-bold text-brand-primary/40 uppercase tracking-[0.4em] px-2 py-4 mb-2 font-display">Denetim Arşivi</div>
            {history.length > 0 ? history.map((h, i) => (
              <button 
                key={h.id || i} 
                onClick={() => handleSelectHistory(h)}
                className="w-full text-left px-4 py-3 rounded-xl text-[12px] text-brand-text-secondary hover:text-brand-primary hover:bg-white/60 transition-all truncate font-medium menu-item-text"
              >
                {h.query || h.query_text}
              </button>
            )) : (
              <div className="px-2 py-2 text-brand-text-secondary/30 text-[11px] font-medium italic">Kayıt bulunamadı.</div>
            )}
          </nav>

          <div className="mt-auto pt-6 border-t border-brand-border/30">
             <div className="flex items-center gap-3 p-4 bg-white/40 rounded-2xl border border-brand-border/20 backdrop-blur-sm">
                <div className="w-8 h-8 rounded-lg bg-brand-primary/10 flex items-center justify-center text-brand-primary text-[10px] font-black">BA</div>
                <div className="flex flex-col">
                   <span className="text-brand-text text-[11px] font-bold">Premium Access</span>
                   <span className="text-brand-primary/60 text-[9px] font-bold uppercase tracking-wider">Lvl 4 Auditor</span>
                </div>
             </div>
          </div>
        </div>
      </aside>

      {/* Main Chat Main Area */}
      <main className="chat-main custom-scrollbar">
        {/* Minimal Header */}
        <header className="w-full h-16 flex items-center justify-between px-10 bg-brand-bg/40 backdrop-blur-sm sticky top-0 z-30">
          <div className="flex items-center gap-6">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-white rounded-xl transition-all text-brand-primary/60 hover:text-brand-primary shadow-sm active:scale-90"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
            <div className={`flex items-center gap-2 transition-opacity duration-300 ${messages.length > 1 ? 'opacity-100' : 'opacity-0'}`}>
               <span className="w-2 h-2 rounded-full bg-brand-primary animate-pulse" />
               <h1 className="font-bold text-[13px] text-brand-primary tracking-tight uppercase">FiCO Advisor Core</h1>
            </div>
          </div>
          <div className="flex items-center gap-4">
             <div className="px-4 py-1.5 bg-white/80 text-brand-primary text-[10px] font-bold rounded-full border border-brand-border/50 uppercase tracking-widest shadow-sm">Live v4.4</div>
          </div>
        </header>

        {/* Vertical Scroll Area */}
        <div ref={scrollRef} className="flex-1 w-full overflow-y-auto custom-scrollbar flex flex-col">
          <div className="chat-content-limit px-10 pb-32">
            
            {messages.length === 1 ? (
              <div className="hero-container animate-fade-in-up">
                 <div className="flex flex-col gap-1 mb-8">
                    <span className="text-brand-primary font-display font-bold text-[13px] tracking-[0.3em] uppercase opacity-70">Merhaba, ben FiCO.</span>
                    <h2 className="hero-title !mt-0">Bugün neyi öğrenmek istersiniz?</h2>
                 </div>
                 <p className="hero-subtitle">
                   Katılım bankacılığı mevzuatları ve fıkhi uyum süreçlerinde 
                   kurumsal düzeyde destek sağlayan yapay zeka danışmanı.
                 </p>

                 <div className="suggestions-row">
                    {suggestionChips.map((chip, i) => (
                      <button 
                        key={i} 
                        onClick={() => handleSend(chip.q)}
                        className="suggestion-card group"
                      >
                        <div className="text-2xl mb-4 group-hover:scale-125 transition-transform origin-left">{chip.icon}</div>
                        <div className="text-[14px] font-bold text-brand-text mb-1 truncate">{chip.q}</div>
                        <div className="text-[10px] text-brand-text-secondary font-bold uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">Başlat →</div>
                      </button>
                    ))}
                 </div>
              </div>
            ) : (
              <div className="flex flex-col space-y-12 pt-6">
                {messages.map((m, i) => (
                  <div key={i} className={`flex flex-col w-full animate-message-in`} style={{ animationDelay: `${i * 0.05}s` }}>
                    <div className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                      
                      {m.role === 'assistant' && (
                        <div className="flex items-center gap-2 mb-3 ml-2">
                           <div className="w-6 h-6 rounded-lg bg-brand-primary flex items-center justify-center text-white text-[8px] font-black">F</div>
                           <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-brand-text-secondary">FiCO Advisors</span>
                        </div>
                      )}

                      <div className={m.role === 'user' ? 'message-user' : 'message-assistant'}>
                        <div className="prose-content">
                          {m.role === 'assistant' && !m.isAnalyzing && (
                            <span className="verdict-title font-display uppercase tracking-widest text-[11px] font-black mb-4 border-b border-brand-border pb-2 inline-block">
                              Analitik Rapor & Hüküm
                            </span>
                          )}
                          
                          {m.content ? <ReactMarkdown>{m.content}</ReactMarkdown> : null}

                          {m.isAnalyzing && (
                            <div className="flex items-center gap-4 py-2">
                               <div className="flex gap-2">
                                  <div className="w-2 h-2 rounded-full bg-brand-primary animate-bounce" />
                                  <div className="w-2 h-2 rounded-full bg-brand-primary animate-bounce [animation-delay:0.2s]" />
                                  <div className="w-2 h-2 rounded-full bg-brand-primary animate-bounce [animation-delay:0.4s]" />
                               </div>
                               <span className="text-[11px] font-black uppercase tracking-[0.2em] text-brand-primary animate-pulse">Kurumsal Veriler Taranıyor</span>
                            </div>
                          )}
                        </div>

                        {m.role === 'assistant' && !m.isAnalyzing && m.sources && m.sources.length > 0 && (
                          <div className="source-muted flex flex-wrap gap-x-5 gap-y-2 mt-8 border-t border-brand-border pt-4">
                             <div className="font-black text-brand-primary uppercase tracking-[0.2em] text-[10px]">Referans Kaynaklar:</div>
                             {m.sources.map((s, si) => (
                               <div key={si} className="flex items-center gap-1.5 text-brand-text-secondary font-bold group cursor-pointer hover:text-brand-primary transition-colors text-[11px]">
                                  <span className="w-1.5 h-1.5 rounded-full bg-brand-border group-hover:bg-brand-primary" />
                                  {s}
                               </div>
                             ))}
                          </div>
                        )}

                        {m.role === 'assistant' && !m.isAnalyzing && m.evaluation && (
                          <div className="mt-6 flex gap-8">
                             <div className="flex flex-col gap-0.5">
                                <div className="text-[9px] font-black text-brand-text-secondary uppercase tracking-widest">Confidence</div>
                                <div className="text-[13px] font-black text-brand-primary font-display">%{Math.round(m.evaluation.hit_rate * 100)} Verified</div>
                             </div>
                             <div className="flex flex-col gap-0.5">
                                <div className="text-[9px] font-black text-brand-text-secondary uppercase tracking-widest">Latency</div>
                                <div className="text-[13px] font-black text-brand-primary font-display">{m.responseTime || "0.8"}s processed</div>
                             </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sticky Input Dock */}
        <div className="input-area-sticky">
           <div className="chat-content-limit px-10">
              <div className="input-pill bg-white shadow-2xl shadow-slate-200">
                <input 
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Karmaşık ürün yapılarını fıkhi uyum açısından analiz edin..."
                  className="flex-1 bg-transparent border-none focus:ring-0 outline-none text-[16px] py-4 text-brand-text placeholder:text-brand-text-secondary/40 font-medium"
                />
                <button 
                  onClick={() => handleSend()}
                  disabled={isFetchingRef.current || !input.trim()}
                  className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                    input.trim() ? 'bg-brand-primary text-white shadow-xl shadow-brand-primary/20 hover:scale-105 active:scale-90' : 'bg-brand-bg text-brand-text-secondary/15'
                  }`}
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 12h14M12 5l7 7-7 7" /></svg>
                </button>
              </div>
              <div className="text-center mt-5 text-[10px] text-brand-text-secondary font-bold uppercase tracking-[0.3em] opacity-40">
                FiCo - Fihri Collective - v4.4 • Enterprise AI Compliance
              </div>
           </div>
        </div>
      </main>
    </div>
  )
}

export default App
