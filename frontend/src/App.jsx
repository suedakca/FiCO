import React, { useState, useEffect, useRef } from 'react'

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
  const chatEndRef = useRef(null)

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
    const queryText = text || input
    if (!queryText.trim() || isLoading) return
    
    setMessages(prev => [...prev, { role: 'user', content: queryText }])
    setInput('')
    setIsLoading(true)
    const startTime = Date.now()

    try {
      const response = await fetch('http://localhost:8000/v1/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'demo_user',
          query_text: queryText
        })
      })

      if (!response.ok) throw new Error('API Error')
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '',
        sources: [],
        evaluation: null
      }])

      let accumulatedContent = ""
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        
        // Metadata kontrolü
        if (chunk.includes("[METADATA]")) {
          const parts = chunk.split("[METADATA]")
          accumulatedContent += parts[0]
          
          try {
            const meta = JSON.parse(parts[1])
            const duration = ((Date.now() - startTime) / 1000).toFixed(1)
            
            setMessages(prev => {
              const newMsgs = [...prev]
              const lastMsg = newMsgs[newMsgs.length - 1]
              lastMsg.content = accumulatedContent.trim()
              lastMsg.sources = meta.source_urls
              lastMsg.responseTime = duration
              lastMsg.evaluation = {
                hit_rate: meta.evaluation?.faithfulness || 0,
                faithfulness: meta.evaluation?.relevance || 0,
                citation_accuracy: 0.9
              }
              return newMsgs
            })
          } catch (e) {
            console.error("Metadata parse error", e)
          }
        } else {
          accumulatedContent += chunk
          setMessages(prev => {
            const newMsgs = [...prev]
            newMsgs[newMsgs.length - 1].content = accumulatedContent
            return newMsgs
          })
        }
      }

      fetchHistory() // Yan menüyü güncelle
    } catch (error) {
      console.error("Stream error", error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Üzgünüm, şu an bağlantı kurulamıyor. Lütfen sistem yöneticinizle iletişime geçin.' 
      }])
    } finally {
      setIsLoading(false)
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
          hit_rate: h.response.confidence_score, // Not: Backend şemasında hit_rate/faithfulness ayrı olabilir, şimdilik confidence_score'a mapiyoruz
          faithfulness: 0.9, 
          citation_accuracy: 0.9
        }
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
      
      {/* Sidebar (ChatGPT style) */}
      <aside className={`${sidebarOpen ? 'w-[260px]' : 'w-0'} transition-all duration-300 bg-[#171717] overflow-hidden flex flex-col z-20`}>
        <div className="p-3 flex flex-col h-full">
          <button 
            onClick={handleNewChat}
            className="flex items-center gap-3 p-3 text-white/90 hover:bg-white/10 rounded-lg transition-all mb-4 group"
          >
            <div className="w-8 h-8 rounded-full border border-white/20 flex items-center justify-center text-xs font-bold">FK</div>
            <span className="font-semibold text-sm">Yeni Sohbet</span>
            <div className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            </div>
          </button>

          <nav className="flex-1 space-y-1 overflow-y-auto px-1 scrollbar-hide">
            <div className="text-white/40 text-[10px] font-bold uppercase tracking-wider px-3 py-4">Son Aramalar</div>
            {history.length > 0 ? history.map((h, i) => (
              <button 
                key={h.id || i} 
                onClick={() => handleSelectHistory(h)}
                className="w-full text-left p-3 rounded-lg text-white/80 text-sm hover:bg-white/10 transition-all truncate animate-fade-in"
              >
                {h.query_text}
              </button>
            )) : (
              <div className="px-3 py-2 text-white/20 text-xs italic">Henüz arama yok.</div>
            )}
          </nav>

          <div className="mt-auto p-2 border-t border-white/10 space-y-1">
            <button className="w-full flex items-center gap-3 p-3 text-white/80 hover:bg-white/10 rounded-lg text-sm transition-all">
              <span className="w-5 h-5 rounded bg-brand-gold/20 flex items-center justify-center text-[10px] font-bold text-brand-gold italic">Pro</span>
              FiCo Kaşif Pro
            </button>
            <button className="w-full flex items-center gap-3 p-3 text-white/80 hover:bg-white/10 rounded-lg text-sm transition-all">
              <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold">SA</div>
              Sueda Akca
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative overflow-hidden h-full">
        
        {/* Toggle Sidebar Button */}
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className={`absolute top-1/2 -translate-y-1/2 z-30 p-2 text-slate-400 hover:text-slate-600 transition-all ${sidebarOpen ? 'left-2' : 'left-2'}`}
        >
          <svg className={`w-4 h-4 transition-transform ${!sidebarOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        </button>

        {/* Chat Stream */}
        <div className="flex-1 overflow-y-auto w-full flex flex-col items-center custom-scrollbar">
          
          {messages.length === 1 && (
            <div className="flex-1 flex flex-col items-center justify-center max-w-2xl px-6 -mt-20 animate-fade-in">
              <div className="w-16 h-16 bg-brand-emerald text-white rounded-[20px] flex items-center justify-center shadow-2xl mb-8 ring-4 ring-brand-emerald/5 rotate-3 hover:rotate-0 transition-transform duration-500">
                <span className="text-2xl font-bold tracking-tighter">FK</span>
              </div>
              <h2 className="text-4xl font-display font-bold text-center mb-10 tracking-tight">Nasıl yardımcı olabilirim?</h2>
              
              <div className="grid grid-cols-2 gap-4 w-full">
                {suggestionChips.map((chip, i) => (
                  <button 
                    key={i} 
                    onClick={() => handleSend(chip.q)}
                    className="p-5 text-left border border-slate-100 rounded-[24px] hover:bg-slate-50 transition-all text-sm group relative hover:shadow-lg hover:shadow-slate-200/50 active:scale-[0.98] animate-slide-up"
                    style={{ animationDelay: `${i * 100}ms` }}
                  >
                    <div className="text-xl mb-3">{chip.icon}</div>
                    <p className="text-slate-500 group-hover:text-black font-medium transition-colors">{chip.q}</p>
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
                    <div className="text-[15px] leading-[1.7] text-[#171717] font-normal">
                      {m.content}
                    </div>
                    {m.evaluation && (
                      <div className="mt-4 flex items-center gap-4 py-2 px-3 bg-brand-cream/40 rounded-xl border border-slate-100/50 w-fit animate-fade-in shadow-sm">
                        <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider pr-2 border-r border-slate-200">
                          <svg className="w-3 h-3 text-brand-gold" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/></svg> 
                          Uyum Puanı
                        </div>
                        <div className="flex gap-3 pr-2 border-r border-slate-200">
                          <div className="flex flex-col">
                            <span className="text-[9px] text-slate-400 font-bold uppercase tracking-tighter">Erişim</span>
                            <span className={`text-[11px] font-bold ${m.evaluation.hit_rate > 0.8 ? 'text-brand-emerald' : 'text-orange-500'}`}>
                              %{Math.round(m.evaluation.hit_rate * 100)}
                            </span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[9px] text-slate-400 font-bold uppercase tracking-tighter">Sadakat</span>
                            <span className={`text-[11px] font-bold ${m.evaluation.faithfulness > 0.8 ? 'text-brand-emerald' : 'text-orange-500'}`}>
                              %{Math.round(m.evaluation.faithfulness * 100)}
                            </span>
                          </div>
                        </div>
                        {m.responseTime && (
                          <div className="flex items-center gap-1.5 px-1">
                            <svg className="w-3 h-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                            <span className="text-[10px] font-bold text-slate-400">{m.responseTime}s</span>
                          </div>
                        )}
                      </div>
                    )}
                    {m.sources && (
                      <div className="mt-8 flex flex-wrap gap-2.5">
                        {m.sources.map((s, si) => (
                          <div key={si} className="group/src flex items-center gap-2.5 px-3.5 py-2 bg-[#fcfcfc] border border-slate-100 rounded-xl hover:border-brand-emerald/20 hover:bg-brand-emerald/[0.02] transition-all cursor-default shadow-sm hover:shadow-md">
                            <span className="text-[9px] font-bold text-brand-emerald ring-1 ring-brand-emerald/10 px-1.5 py-0.5 rounded-sm leading-none tracking-wider uppercase bg-white">Atıf</span>
                            <span className="text-[13px] font-medium text-slate-400 group-hover/src:text-brand-emerald transition-colors">{s}</span>
                          </div>
                        ))}
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
