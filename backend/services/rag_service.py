import json
import os
import re
import asyncio
from typing import List, Dict, Any, AsyncGenerator
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories.sql import SQLChatMessageHistory

from core.config import settings
from .chroma_service import chroma_service
from .agent_tools import agent_tools
from .unified_eval_service import unified_eval_service

class ComplianceAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model="bazobehram/turkish-gemma-9b-t1", 
            temperature=0, 
            top_p=0.85,
            repeat_penalty=1.1,
            num_predict=1024
        )
        self.db_uri = settings.SQLALCHEMY_DATABASE_URI
        
        # Sert Filtreleme Sözlüğü (Sınıf düzeyinde tutmak için)
        self.replacements = {
            r'\brequired\b': 'gerekli',
            r'\bonly\b': 'sadece',
            r'\bfounder\b': 'bulunmaktadır',
            r'\bshared\b': 'paylaşılan',
            r'\bparty\b': 'taraf',
            r'\bpartie\b': 'taraf',
            r'\bwithinde\b': 'içerisinde',
            r'\bfunciona\b': 'işler / çalışır',
            r'\bmeaning\b': 'anlamına gelir',
            r'\boperationsinde\b': 'işlemlerinde',
            r'\bfounderedidir\b': 'bulunmaktadır',
            r'\bhargaını\b': 'fiyatını',
            r'm[uü]r[aâ]ha[h]+a': 'Murabaha',
            r'm[uü]r[aâ]ha[cç]a': 'Murabaha',
            r'\bdövret\b': 'dair',
            r'\bpayişine\b': 'paylaşımına',
            r'\bpayişin\b': 'paylaşımı',
            r'\bzorar\b': 'zarar',
            r'\bzorara\b': 'zarara',
            r'\bfinancier\b': 'banka / finansman kuruluşu',
            r'\bpartagerilmesini\b': 'paylaşılmasını',
            r'\bcontractında\b': 'sözleşmesinde',
            r'\bmeaningde\b': 'anlamında',
            r'\bterminatı\b': 'teminatı',
            r'\bterminatsı\b': 'teminatı',
            r'\bsharingi\b': 'paylaşımı',
            r'\bsharinginin\b': 'paylaşımının',
            r'\bsharing\b': 'paylaşım',
            r'\bcontract\b': 'sözleşme',
            r'\bexpertise\b': 'uzmanlık',
            r'\bfinance\b': 'finans',
            r'\bisum\b': '',
        }

    def _clean_agent_output(self, text: str) -> str:
        """Markdown başlıklarını, teknik etiketleri ve yasaklı sembolleri temizler."""
        # 1. Sert Kelime Filtresi
        for pattern, replacement in self.replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # 2. Yasaklı Teknik İbareler, ID'ler ve Düşünce Blokları
        patterns = [
            r'<think>.*?</think>', 
            r'\b(std|internal|pub)_\d+\b', # Teknik ID'leri temizle (Örn: internal_115)
            r'\[(std|internal|pub)_\d+\]', # Köşeli parantez içindekileri temizle (Örn: [std_066])
            r'ID: \w+', r'Uyum Skoru: \d+', 
            r'Bağlam:', r'İçerik:', r'Geçmiş:', r'Context:',
            r'Atıf:', 
        ]
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

        # 3. Hiyerarşi ve Dekorasyon Temizliği (###, ##, ---, ***, > temizliği)
        # Markdown başlık işaretlerini kaldır (# karakterlerini sil)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        # Dekoratif çizgileri ve blok alıntılarını sil
        text = re.sub(r'[\-\*]{3,}', '', text)
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
        
        # 4. Gereksiz boşlukları temizle
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _get_history(self, session_id: str):
        return SQLChatMessageHistory(
            session_id=session_id,
            connection=self.db_uri
        )

    async def _route_query(self, text: str) -> str:
        """Soruyu türüne göre sınıflandırır."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Sen bir yönlendiricisin. Verilen soruyu 'GENEL' veya 'KARMASIK' olarak sınıflandır. Sadece kelimeyi döndür."),
            ("human", "{text}")
        ])
        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({"text": text})
        return "KARMASIK" if "KARMASIK" in result.upper() else "GENEL"

    async def query(self, text: str, user_id: str = "default_user") -> Dict[str, Any]:
        """FiCO Uyum Analisti ReAct Döngüsü."""

        history = self._get_history(user_id)

        # 1. Thought (Düşünce) - route, thought ve retrieval paralel çalışır
        thought_prompt = ChatPromptTemplate.from_messages([
            ("system", "Sen Katılım Bankacılığı Uyum Analisti ajansısın. Kullanıcı sorusuna cevap vermeden önce "
                       "Hangi mevzuata (AAOIFI/TKBB) bakman gerektiğini ve hangi araçları kullanacağını düşün. "
                       "Düşünceni 'Düşünce:' etiketiyle Türkçe olarak yaz."),
            ("human", "Soru: {text}")
        ])
        thought_chain = thought_prompt | self.llm | StrOutputParser()

        # Sequentialize independent tasks to avoid flooding Ollama
        route   = await self._route_query(text)
        thought = await thought_chain.ainvoke({"text": text})
        context = await agent_tools.document_retriever(text)
        
        if route == "KARMASIK":
            categories = ["Mudaraba", "Murabaha", "Sarf", "Teverruk", "Kripto", "Zekat", "Sukuk", "İjarah", "Muşaraka"]
            text_lower = text.lower()
            detected_cat = next((cat for cat in categories if cat.lower() in text_lower), "Genel")
            policy_context = await agent_tools.policy_aggregator(detected_cat)
            context += "\n\n### Mevzuat Birleşimi ###\n" + policy_context

        # 3. Nihai Cevap (Sadeleştirilmiş ve Kesin Prompt)
        answer_prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen Katılım Bankacılığı alanında uzman bir 'Uyum Denetçisi'sin.
 
 KURALLAR VE KESİN KISITLAMALAR:
 0. KRİTİK BAĞLAM KİLİDİ: SADECE sana verilen 'Bağlam' içindeki bilgileri kullan. Eğer sorunun cevabı Bağlam içinde DOĞRUDAN VE NET olarak yoksa, kesinlikle yorum yapma ve HİÇBİR AÇIKLAMA EKLEMEDEN Rule 6'yı uygula.
 1. KESİN TÜRKÇE KİLİDİ: Tüm cevabını SADECE akıcı ve doğal bir TÜRKÇE ile ver. 
 2. HİYERARŞİ: Başlıklar için asla ### veya ## gibi Markdown işaretleri kullanma. Başlıkları tamamen BÜYÜK HARF VE BOLD olarak yaz.
 3. SADELİK: ***, --- veya > gibi ayırıcı semboller kullanma. Doğrudan bilgiye odaklan.
 4. ATIF STİLİ: Metin içerisinde asla [std_1] gibi teknik ID'leri yazma. Bunun yerine tüm cevap bittikten sonra en alta **KAYNAK DÖKÜMANLAR:** başlığı aç ve kullandığın tüm kaynakların TAM ADINI buraya listele.
 5. YÖNLENDİRME (REFERRAL) MESAJI: "Bu konu mevzuat ve banka politikalarında henüz netlik kazanmamış özel bir inceleme gerektirmektedir. Lütfen bankanızın **Danışma Kurulu'na** başvurun."
 6. MUTLAK DOĞRUDANLIK: Eğer bağlamdaki bilgiler kullanıcının sorusuna NET CEVAP VERMİYORSA (Örn: Gelecek tahmini, Metaverse vb.), aradaki hiçbir bilgiyi özetleme. Hiçbir ön açıklama yapma. SADECE Rule 5'teki cümleyi yaz ve dur.
 
 Bağlam:
 {context}
 
 Geçmiş:
 {history}
 """),
            ("human", "{question}")
        ])
        
        answer_chain = answer_prompt | self.llm | StrOutputParser()
        answer = await answer_chain.ainvoke({
            "context": context,
            "history": history.messages[-5:] if history.messages else "Geçmiş yok.",
            "question": text
        })

        # Metadata extraction (Before cleaning)
        source_ids = list(set(re.findall(r"(?:\[)?\b(std_\d+|internal_\d+|pub_\d+)\b(?:\])?", answer)))

        # Post-processing temizliği
        answer = self._clean_agent_output(answer)

        # 4. Compliance Validation & Evaluation (SEQUENTIAL)
        validation = await agent_tools.compliance_validator(answer, context)
        eval_results = await evaluation_service.evaluate_response(text, answer, context)

        # Geçmişe ekle
        history.add_user_message(text)
        history.add_ai_message(answer)

        return {
            "answer_text": answer,
            "thought": thought,
            "route": route,
            "validation": validation,
            "evaluation": eval_results,
            "source_urls": source_ids,
            "faithfulness": eval_results["faithfulness"],
            "confidence_score": eval_results["composite_compliance_score"]
        }

    async def stream_query(self, text: str, user_id: str = "default_user") -> AsyncGenerator[str, None]:
        """FiCO Uyum Analisti Streaming (Akış) Döngüsü."""
        
        route = await self._route_query(text)
        history = self._get_history(user_id)
        
        # 1. Retrieval (Hızlı Başlatmak için Thought kısmını pas geçiyoruz veya paralel alıyoruz)
        context = await agent_tools.document_retriever(text)
        if route == "KARMASIK":
            detected_cat = "Genel"
            policy_context = await agent_tools.policy_aggregator(detected_cat)
            context += "\n\n### Mevzuat Birleşimi ###\n" + policy_context
        
        thought = "Analiz süreci başlatıldı..." # Geriye dönük uyum için

        # 2. Nihai Cevap (Sadeleştirilmiş Akış)
        answer_prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen Katılım Bankacılığı alanında uzman bir 'Uyum Denetçisi'sin.
 
 KURALLAR VE KESİN KISITLAMALAR:
 0. KRİTİK BAĞLAM KİLİDİ: SADECE sana verilen 'Bağlam' içindeki bilgileri kullan. Eğer sorunun cevabı Bağlam içinde DOĞRUDAN VE NET olarak yoksa, HİÇBİR AÇIKLAMA EKLEMEDEN Rule 6'yı uygula.
 1. KESİN TÜRKÇE KİLİDİ: Tüm cevabını SADECE akıcı ve doğal bir TÜRKÇE ile ver. 
 2. HİYERARŞİ: Başlıklar için asla ### veya ## gibi Markdown işaretleri kullanma. Başlıkları tamamen BÜYÜK HARF VE BOLD olarak yaz.
 3. SADELİK: ***, --- veya > gibi ayırıcı semboller kullanma. Doğrudan bilgiye odaklan.
 4. ATIF STİLİ: Metin içinde atıf yapma. Cevabın en sonunda **KAYNAK DÖKÜMANLAR:** başlığı altında kullandığın kaynakların tam isimlerini listele. Teknik döküman ID'lerini asla kullanıcıya gösterme.
 5. YÖNLENDİRME (REFERRAL) MESAJI: "Bu konu mevzuat ve banka politikalarında henüz netlik kazanmamış özel bir inceleme gerektirmektedir. Lütfen bankanızın **Danışma Kurulu'na** başvurun."
 6. MUTLAK DOĞRUDANLIK: Eğer bağlamdaki bilgiler kullanıcının sorusuna NET CEVAP VERMİYORSA, aradaki hiçbir bilgiyi özetleme. Hiçbir ön açıklama yapmadan SADECE Rule 5'teki YÖNLENDİRME MESAJI'nı yaz ve bitir.
 
 Bağlam:
 {context}
 
 Geçmiş:
 {history}
 """),
            ("human", "{question}")
        ])
        
        answer_chain = answer_prompt | self.llm | StrOutputParser()
        
        full_answer = ""
        seen_sentences = set()
        is_thinking = False
        
        # Bozuk Geçmiş Koruması: Eğer son mesajlar devasa bir döngü içeriyorsa geçmişi yoksay
        history_messages = history.messages[-3:] if history.messages else []
        if any(len(m.content) > 800 for m in history_messages):
            history_messages = [] # Bozuk geçmişi taklit etmesini engelle
            
        async for chunk in answer_chain.astream({
            "context": context,
            "history": history_messages if history_messages else "Geçmiş yok.",
            "question": text
        }):
            full_answer += chunk
            
            # <think> bloğu kontrolü
            if "<think>" in chunk or is_thinking:
                if "<think>" in chunk:
                    is_thinking = True
                if "</think>" in chunk:
                    is_thinking = False
                    # </think> sonrası kısmı işle
                    remaining = chunk.split("</think>")[-1]
                    if not remaining:
                        continue
                    chunk = remaining
                else:
                    continue

            # Akış anında saptanan kelimeleri temizle
            clean_chunk = chunk
            for pattern, replacement in self.replacements.items():
                clean_chunk = re.sub(pattern, replacement, clean_chunk, flags=re.IGNORECASE)
            
            # Anti-Loop Guard: Cümle bazlı döngü tespiti
            if "." in clean_chunk:
                sentences = full_answer.split(".")
                last_sentence = sentences[-2].strip() if len(sentences) > 1 else ""
                if len(last_sentence) > 20: # Kısa cümleleri (örn: Evet.) yoksay
                    if last_sentence in seen_sentences:
                        yield "... [Döngü Tespit Edildi, Akış Kesildi]"
                        break
                    seen_sentences.add(last_sentence)
            
            yield clean_chunk

        yield "\n[GENERATION_DONE]\n"

        # 3. Consolidated Post-Processing (SINGLE CALL)
        # Replacing multiple sequential/parallel calls with one unified call for max performance
        eval_results = await unified_eval_service.evaluate_full(text, full_answer, context)
        validation = {"status": eval_results["status"], "reason": eval_results["reason"]}

        # 4. Geçmişe Ekle
        history.add_user_message(text)
        history.add_ai_message(full_answer)

        # 5. Metadata'yı gönder
        metadata = {
            "type": "metadata",
            "thought": thought,
            "validation": validation,
            "evaluation": eval_results,
            "source_urls": eval_results.get("sources", []),
            "confidence_score": eval_results["composite_compliance_score"]
        }
        yield f"\n[METADATA]{json.dumps(metadata)}"

compliance_agent = ComplianceAgent()
# Geriye dönük uyumluluk için rag_service adıyla export et
class RAGServiceWrapper:
    async def query(self, text: str) -> Dict[str, Any]:
        return await compliance_agent.query(text)
    
    async def stream_query(self, text: str) -> AsyncGenerator[str, None]:
        async for chunk in compliance_agent.stream_query(text):
            yield chunk

rag_service = RAGServiceWrapper()
