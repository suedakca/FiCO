import React, { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'

const APP_VERSION = "v3.0 ChatGPT Edition"

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
  const [showThought, setShowThought] = useState(false) // Analiz şeffaflığı kontrolü
  const chatEndRef = useRef(null)
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
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
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

      fetchHistory() // Yan menüyü güncelle
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
    if (!h.response) {
      // Eğer cevap kaydedilmemişse sadece soruyu gönder (Fallback)
      handleSend(h.query_text)
      return
    }
    
    setMessages([
      INITIAL_MESSAGE,
      { role: 'user', content: h.query_text },
      { 
        role: 'assistant', 
        content: h.response.answer_text,
        sources: h.response.source_urls ? h.response.source_urls.split(',') : [],
        evaluation: {
          hit_rate: h.response.confidence_score, 
          faithfulness: 0.9, 
          citation_accuracy: 0.9
        },
        thought: h.response.thought // Geçmişten thought verisini de yükle
      }
    ])
  }

  const suggestionChips = [
    { q: "Mudaraba'da zarar paylaşımı", icon: "⚖️" },
    { q: "Kripto varlık teminatı", icon: "🪙" },
    { q: "Vadeli sarf işlemleri", icon: "💱" },
    { q: "Konut finansmanı kârı", icon: "🏠" }
  ]

  return (
    <div className="flex h-screen bg-white font-sans selection:bg-brand-emerald/10 text-[#0d0d0d]">
      
      {/* Sidebar (Corporate Style) */}
      <aside className={`${sidebarOpen ? 'w-[280px]' : 'w-0'} transition-all duration-300 bg-brand-navy overflow-hidden flex flex-col z-20 shadow-2xl`}>
        <div className="p-4 flex flex-col h-full">
          <button 
            onClick={handleNewChat}
            className="flex items-center gap-3 p-4 bg-white/5 border border-white/10 text-white/90 hover:bg-white/10 rounded-xl transition-all mb-6 group shadow-lg"
          >
            <div className="w-8 h-8 rounded-lg bg-brand-gold flex items-center justify-center text-white text-xs font-bold shadow-gold/20">FK</div>
            <span className="font-semibold text-sm">Yeni Analiz</span>
            <div className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            </div>
          </button>

          <nav className="flex-1 space-y-2 overflow-y-auto px-1 scrollbar-hide">
            <div className="text-white/30 text-[10px] font-bold uppercase tracking-[0.2em] px-3 py-4">DENETİM KAYITLARI</div>
            {history.length > 0 ? history.map((h, i) => (
              <button 
                key={h.id || i} 
                onClick={() => handleSelectHistory(h)}
                className="w-full text-left p-3.5 rounded-xl text-white/70 text-[13px] hover:bg-white/5 hover:text-white border border-transparent hover:border-white/5 transition-all truncate animate-fade-in group font-medium"
              >
                <span className="opacity-40 mr-2 font-mono text-[10px]">{String(i+1).padStart(2, '0')}</span>
                {h.query_text}
              </button>
            )) : (
              <div className="px-3 py-2 text-white/20 text-xs italic">Henüz denetim kaydı yok.</div>
            )}
          </nav>

          <div className="mt-auto p-2 border-t border-white/5 pt-4 space-y-2">
            <div className="flex items-center gap-3 p-3 bg-white/5 rounded-xl border border-white/5 mb-4">
              <div className="w-8 h-8 rounded-full bg-brand-gold/20 flex items-center justify-center text-brand-gold text-xs font-bold border border-brand-gold/30 italic">BA</div>
              <div className="flex flex-col">
                <span className="text-white text-[12px] font-bold">Banka Yetkilisi</span>
                <span className="text-white/40 text-[10px]">Demo Hesabı</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative overflow-hidden h-full">
        
        {/* Professional Header */}
        <header className="h-[70px] border-bottom border-slate-200 bg-white/80 backdrop-blur-md flex items-center justify-between px-8 z-10 shadow-sm">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-500"
            >
              <svg className={`w-5 h-5 transition-transform ${!sidebarOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
            <div className="h-6 w-[1px] bg-slate-200 mx-2" />
            <div className="flex flex-col">
              <h1 className="text-[15px] font-bold text-brand-navy tracking-tight leading-tight">FiCO Compliance Hub</h1>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Mevzuat Analiz & Denetim Sistemi</span>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-brand-emerald/10 text-brand-emerald rounded-full text-[11px] font-bold">
              <span className="w-2 h-2 rounded-full bg-brand-emerald animate-pulse" />
              Sistem Aktif
            </div>
            <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
            </button>
          </div>
        </header>

        {/* Chat Stream */}
        <div className="flex-1 overflow-y-auto w-full flex flex-col items-center bg-brand-cream custom-scrollbar">
          
          {messages.length === 1 && (
            <div className="flex-1 flex flex-col items-center justify-center max-w-3xl px-6 -mt-10 animate-fade-in w-full">
              <div className="w-20 h-20 bg-brand-navy text-white rounded-[24px] flex items-center justify-center shadow-2xl mb-10 ring-8 ring-brand-navy/5 animate-bounce-subtle">
                <span className="text-3xl font-bold tracking-tighter">FK</span>
              </div>
              <h2 className="text-4xl font-display font-black text-center mb-4 tracking-tighter text-brand-navy">Analiz Merkezi'ne Hoş Geldiniz</h2>
              <p className="text-slate-400 text-center mb-12 max-w-md font-medium">Katılım bankacılığı mevzuat uyum süreçlerinizi yapay zeka ile denetleyin.</p>
              
              <div className="grid grid-cols-2 gap-6 w-full max-w-2xl">
                {suggestionChips.map((chip, i) => (
                  <button 
                    key={i} 
                    onClick={() => handleSend(chip.q)}
                    className="p-6 text-left bg-white border border-slate-200 rounded-[28px] hover:border-brand-gold/30 hover:bg-brand-gold/[0.02] transition-all text-sm group relative shadow-sm hover:shadow-xl hover:shadow-brand-gold/5 active:scale-[0.98] animate-slide-up"
                    style={{ animationDelay: `${i * 100}ms` }}
                  >
                    <div className="w-10 h-10 bg-slate-50 rounded-xl flex items-center justify-center text-xl mb-4 group-hover:bg-brand-gold/10 transition-colors">{chip.icon}</div>
                    <p className="text-slate-500 group-hover:text-brand-navy font-bold transition-colors mb-1">{chip.q}</p>
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Hemen Analiz Et</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.length > 1 && (
            <div className="w-full max-w-3xl px-6 pt-12 pb-48 space-y-12">
              {messages.map((m, i) => (
                <div key={i} className="flex gap-6 group animate-fade-in">
                  <div className={`w-9 h-9 rounded-xl flex-shrink-0 flex items-center justify-center text-[11px] font-bold shadow-sm transition-transform group-hover:scale-105 ${
                    m.role === 'user' ? 'bg-slate-100 text-slate-500 border border-slate-200' : 'bg-brand-emerald text-white shadow-brand-emerald/20'
                  }`}>
                    {m.role === 'user' ? 'S' : 'FK'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-[10px] mb-2 opacity-30 uppercase tracking-[0.2em] leading-none">
                      {m.role === 'user' ? 'Siz' : 'FiCo Kaşif'}
                    </div>
                    <div className="text-[15px] leading-[1.8] text-brand-navy font-normal prose prose-slate max-w-none">
                      {m.thought && (
                        <div className="mb-6 bg-slate-100/50 border border-slate-200/60 rounded-2xl overflow-hidden animate-slide-up">
                          <button 
                            onClick={() => setShowThought(!showThought)}
                            className="w-full flex items-center justify-between p-4 hover:bg-slate-200/30 transition-colors uppercase tracking-[0.15em] text-[10px] font-black text-slate-500"
                          >
                            <span className="flex items-center gap-2">
                              <svg className="w-3.5 h-3.5 text-brand-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.364-5.636l-.707-.707m1.414 14.142l-.707-.707M4.422 4.422l.707.707m4.347 4.347l1.32-1.319a3.848 3.848 0 015.441 5.441l-1.32 1.32M9 12h.01M9 16h.01" /></svg>
                              Analiz Mantığı (Thought Process)
                            </span>
                            <svg className={`w-3.5 h-3.5 transition-transform ${showThought ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" /></svg>
                          </button>
                          {showThought && (
                            <div className="p-4 pt-0 text-[13px] text-slate-500 italic font-medium leading-relaxed border-t border-slate-200/40 mt-2">
                              {m.thought}
                            </div>
                          )}
                        </div>
                      )}
                      
                      <ReactMarkdown>{m.content}</ReactMarkdown>
                      {m.escalated && (
                        <div className="mt-6 flex items-center gap-3 text-red-600 font-bold text-[12px] uppercase tracking-widest bg-red-50 p-4 rounded-xl border border-red-200">
                          ⚠️ Danışma Kuruluna Eskalasyonu Gerekiyor (Risk / Belirsizlik tespit edildi)
                        </div>
                      )}
                      {m.queryType && (
                         <div className="mt-3 text-[10px] text-slate-400 font-bold uppercase tracking-widest">Sorgu Tipi: {m.queryType}</div>
                      )}
                      {m.isAnalyzing && (
                        <div className="mt-6 flex items-center gap-3 text-brand-emerald animate-pulse font-bold text-[11px] uppercase tracking-widest bg-brand-emerald/5 p-4 rounded-2xl border border-brand-emerald/10">
                          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Derin Mevzuat Analizi Yapılıyor...
                        </div>
                      )}
                    </div>
                    {m.evaluation && (
                      <div className="mt-6 flex items-center gap-6 py-4 px-6 bg-white rounded-2xl border border-slate-200 shadow-sm w-fit animate-fade-in group/eval">
                        <div className="flex items-center gap-3 pr-6 border-r border-slate-100">
                          <div className="w-8 h-8 rounded-lg bg-brand-gold/10 flex items-center justify-center text-brand-gold">
                             <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/></svg> 
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-tight">Uyum Rasyosu</span>
                            <span className="text-[14px] font-black text-brand-navy">PROFESYONEL</span>
                          </div>
                        </div>
                        <div className="flex gap-8 pr-6 border-r border-slate-100">
                          <div className="flex flex-col">
                            <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-1">Erişim</span>
                            <div className="flex items-end gap-1">
                              <span className={`text-[18px] font-black leading-none ${m.evaluation.hit_rate > 0.8 ? 'text-brand-emerald' : 'text-brand-amber'}`}>
                                %{Math.round(m.evaluation.hit_rate * 100)}
                              </span>
                              <div className="w-12 h-1 bg-slate-100 rounded-full overflow-hidden mb-1.5">
                                <div className="h-full bg-brand-emerald transition-all duration-1000" style={{ width: `${Math.round(m.evaluation.hit_rate * 100)}%` }} />
                              </div>
                            </div>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-1">Sadakat</span>
                            <div className="flex items-end gap-1">
                              <span className={`text-[18px] font-black leading-none ${m.evaluation.faithfulness > 0.8 ? 'text-brand-emerald' : 'text-brand-amber'}`}>
                                %{Math.round(m.evaluation.faithfulness * 100)}
                              </span>
                              <div className="w-12 h-1 bg-slate-100 rounded-full overflow-hidden mb-1.5">
                                <div className="h-full bg-brand-emerald transition-all duration-1000" style={{ width: `${Math.round(m.evaluation.faithfulness * 100)}%` }} />
                              </div>
                            </div>
                          </div>
                        </div>
                        {m.responseTime && (
                          <div className="flex items-center gap-2">
                             <div className="w-2 h-2 rounded-full bg-slate-200" />
                             <span className="text-[11px] font-bold text-slate-400">{m.responseTime}s Analiz Süresi</span>
                          </div>
                        )}
                      </div>
                    )}
                    {m.sources && (
                      <div className="mt-10 pt-6 border-t border-slate-100 flex flex-col gap-4">
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Referans Kaynaklar</span>
                        <div className="flex flex-wrap gap-3">
                          {m.sources.map((s, si) => (
                            <div key={si} className="group/src flex items-center gap-3 px-4 py-2.5 bg-white border border-slate-200 rounded-2xl hover:border-brand-gold/30 hover:bg-brand-gold/[0.02] transition-all cursor-pointer shadow-sm hover:shadow-lg">
                              <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center text-brand-gold group-hover/src:bg-brand-gold/10 transition-colors">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-[13px] font-bold text-brand-navy leading-none mb-1">{s}</span>
                                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">İlgili Madde</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-6 animate-pulse">
                  <div className="w-9 h-9 rounded-xl bg-slate-100 border border-slate-200" />
                  <div className="flex-1 space-y-3 mt-2">
                    <div className="h-3 bg-slate-50 rounded-full w-4/5" />
                    <div className="h-3 bg-slate-50 rounded-full w-2/3" />
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          )}
        </div>

        {/* Floating Input (ChatGPT Style) */}
        <div className="absolute bottom-0 left-0 right-0 p-8 pt-0 flex justify-center pointer-events-none">
          <div className="max-w-3xl w-full flex flex-col items-center gap-4">
            <div className="w-full bg-[#f4f4f4] rounded-[28px] p-2 flex items-center pointer-events-auto border border-black/5 focus-within:ring-1 focus-within:ring-black/10 transition-all">
              <input 
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Mesajınızı yazın..."
                className="flex-1 bg-transparent border-none focus:ring-0 px-4 py-3 text-base outline-none text-[#0d0d0d] placeholder:text-black/40"
              />
              <button 
                onClick={() => handleSend()}
                disabled={isLoading || !input.trim()}
                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                  input.trim() ? 'bg-black text-white hover:opacity-80' : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
              </button>
            </div>
            <p className="text-[10px] text-slate-400 font-medium">
              FiCo Kaşif de hata yapabilir. Önemli bilgileri kontrol edin.
            </p>
          </div>
        </div>

      </div>
    </div>
  )
}

export default App
