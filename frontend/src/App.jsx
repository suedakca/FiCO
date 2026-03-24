import React, { useState } from 'react'

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Merhaba! Ben FiCo Kaşif. Katılım bankacılığı, AAOIFI standartları ve iç mevzuat konularında size nasıl yardımcı olabilirim?' }
  ])
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim()) return
    setMessages([...messages, { role: 'user', content: input }])
    setInput('')
    // Simulate assistant response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Sorgunuz için teşekkürler: "${input}". Şu an RAG motoruna bağlanıyorum...`,
        sources: ['AAOIFI Standart No: 5', 'BDDK Karar 2024/1']
      }])
    }, 1000)
  }

  return (
    <div className="flex flex-col h-screen bg-slate-50 text-slate-800">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-4 bg-white border-b border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-lg">
            FK
          </div>
          <div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-blue-500">
              FiCo Kaşif
            </h1>
            <p className="text-xs text-slate-500 font-medium">Uyum ve Mevzuat Asistanı (v1.0)</p>
          </div>
        </div>
        <div className="flex gap-4">
          <button className="text-sm font-semibold text-slate-600 hover:text-blue-600 transition-colors">Dökümanlar</button>
          <button className="text-sm font-semibold px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-all shadow-md">Giriş Yap</button>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 max-w-4xl mx-auto w-full">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] p-4 rounded-2xl shadow-sm border ${
              m.role === 'user' 
                ? 'bg-blue-600 text-white border-blue-500 rounded-tr-none' 
                : 'bg-white text-slate-700 border-slate-200 rounded-tl-none'
            }`}>
              <p className="text-sm md:text-base leading-relaxed">{m.content}</p>
              {m.sources && (
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Kaynaklar</p>
                  <div className="flex flex-wrap gap-2">
                    {m.sources.map((s, si) => (
                      <span key={si} className="text-[11px] px-2 py-1 bg-slate-100 text-slate-600 rounded-md font-medium border border-slate-200">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </main>

      {/* Input Area */}
      <footer className="p-4 md:p-8 bg-gradient-to-t from-slate-50 to-transparent">
        <div className="max-w-3xl mx-auto relative group">
          <input 
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Sorunuzu buraya yazın (örn: Murabaha akdi şartları nelerdir?)"
            className="w-full p-4 pr-16 bg-white border border-slate-200 rounded-2xl shadow-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-700 placeholder:text-slate-400"
          />
          <button 
            onClick={handleSend}
            className="absolute right-3 top-3 bottom-3 px-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all shadow-lg active:scale-95 group-focus-within:shadow-blue-500/20"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>
        <p className="text-center text-[10px] text-slate-400 mt-4">
          FiCo Kaşif finansal tavsiye vermez. Tüm cevaplar resmi mevzuat dökümanlarından üretilmektedir.
        </p>
      </footer>
    </div>
  )
}

export default App
