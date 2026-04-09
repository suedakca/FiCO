import json
import os
import re
from typing import List, Dict, Any, AsyncGenerator
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories.sql import SQLChatMessageHistory

from core.config import settings
from .chroma_service import chroma_service
from .agent_tools import agent_tools
from .evaluation_service import evaluation_service

class ComplianceAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model="llama3.2", 
            temperature=0, 
            top_p=0.85,
            repeat_penalty=1.3,
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
            r'\bisum\b': '',
        }

    def _clean_agent_output(self, text: str) -> str:
        """ID'leri ve teknik etiketleri temizler, İngilizce sızıntıları Türkçeleştirir."""
        # Sert Kelime Filtresi (Model sızıntılarını önlemek için)
        pass # self.replacements kullanılacak
        for pattern, replacement in self.replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Yasaklı teknik ibareler ve ID'ler
        patterns = [
            r'ID: \w+', r'Uyum Skoru: \d+', r'Kaynak:', 
            r'Bağlam:', r'İçerik:', r'Geçmiş:', r'Context:',
            r'Atıf:', r'\*\*', 
        ]
        for pattern in patterns:
            text = re.sub(pattern, '', text)
        
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _get_history(self, session_id: str):
        return SQLChatMessageHistory(
            session_id=session_id, 
            connection_string=self.db_uri
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
        
        route = await self._route_query(text)
        history = self._get_history(user_id)
        
        # 1. Thought (Düşünce)
        thought_prompt = ChatPromptTemplate.from_messages([
            ("system", "Sen Katılım Bankacılığı Uyum Analisti ajansısın. Kullanıcı sorusuna cevap vermeden önce "
                       "Hangi mevzuata (AAOIFI/TKBB) bakman gerektiğini ve hangi araçları kullanacağını düşün. "
                       "Düşünceni 'Düşünce:' etiketiyle Türkçe olarak yaz."),
            ("human", "Soru: {text}")
        ])
        thought_chain = thought_prompt | self.llm | StrOutputParser()
        thought = await thought_chain.ainvoke({"text": text})

        # 2. Action (Eylem) - Bilgi Getirme
        context = await agent_tools.document_retriever(text)
        
        if route == "KARMASIK":
            # Karmaşık analizde politika birleştiriciyi de kullan
            # Kategori tespiti (basit regex veya LLM ile de yapılabilir)
            categories = ["Mudaraba", "Murabaha", "Sarf", "Teverruk", "Kripto"]
            detected_cat = next((cat for cat in categories if cat.lower() in text.lower()), "Genel")
            policy_context = await agent_tools.policy_aggregator(detected_cat)
            context += "\n\n### Mevzuat Birleşimi ###\n" + policy_context

        # 3. Nihai Cevap (Sadeleştirilmiş ve Kesin Prompt)
        answer_prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen Katılım Bankacılığı alanında uzman bir 'Uyum Denetçisi'sin.

HUKUKİ VE DİLSEL KURALLAR:
1. SADECE TÜRKÇE: Teknik terimler hariç sadece akıcı Türkçe kullan. Yabancı kelime uydurma.
2. DÖKÜMAN SADAKATİ: Sadece 'Bağlam' içinde verilen bilgileri kullan. Kavramları (Örn: Sarf ve Mudaraba) birbirine karıştırma.
3. SADELİK: Doğrudan cevabı ver. Teknik etiketler kullanma.
4. RESMİ ÜSLUP: Kurumsal ve ciddi bir ton kullan.

Bağlam:
{context}

Geçmiş:
{history}"""),
            ("human", "{question}")
        ])
        
        answer_chain = answer_prompt | self.llm | StrOutputParser()
        answer = await answer_chain.ainvoke({
            "context": context,
            "history": history.messages[-5:] if history.messages else "Geçmiş yok.",
            "question": text
        })

        # Post-processing temizliği
        answer = self._clean_agent_output(answer)

        # 4. Compliance Validation (Uyum Doğrulama)
        validation = await agent_tools.compliance_validator(answer, context)
        
        # 5. Evaluation (Değerlendirme)
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
            "source_urls": list(set(re.findall(r"\[(std_\d+|internal_\d+|pub_\d+)\]", answer))),
            "faithfulness": eval_results["faithfulness"],
            "confidence_score": eval_results["composite_compliance_score"]
        }

    async def stream_query(self, text: str, user_id: str = "default_user") -> AsyncGenerator[str, None]:
        """FiCO Uyum Analisti Streaming (Akış) Döngüsü."""
        
        route = await self._route_query(text)
        history = self._get_history(user_id)
        
        # 1. Thought & Retrieval (Arka planda hızlıca yap)
        thought_prompt = ChatPromptTemplate.from_messages([
            ("system", "Hangi mevzuata (AAOIFI/TKBB) bakman gerektiğini düşün ve kısa bir not çıkar."),
            ("human", "{text}")
        ])
        thought_chain = thought_prompt | self.llm | StrOutputParser()
        thought = await thought_chain.ainvoke({"text": text})

        context = await agent_tools.document_retriever(text)
        if route == "KARMASIK":
            detected_cat = "Genel"
            policy_context = await agent_tools.policy_aggregator(detected_cat)
            context += "\n\n### Mevzuat Birleşimi ###\n" + policy_context

        # 2. Nihai Cevap (Sadeleştirilmiş Akış)
        answer_prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen Katılım Bankacılığı Uyum Denetçisisin.

KURALLAR:
1. Sadece akıcı Türkçe kullan.
2. Dokümanlardaki hükümleri (peşinlik, zarar vb.) hatasız aktar. Kripto ve Mudaraba konularını karıştırma.
3. Teknik başlık kullanmadan doğrudan cevaba gir.

Bağlam:
{context}

Geçmiş:
{history}"""),
            ("human", "{question}")
        ])
        
        answer_chain = answer_prompt | self.llm | StrOutputParser()
        
        full_answer = ""
        seen_sentences = set()
        
        # Bozuk Geçmiş Koruması: Eğer son mesajlar devasa bir döngü içeriyorsa geçmişi yoksay
        history_messages = history.messages[-3:] if history.messages else []
        if any(len(m.content) > 800 for m in history_messages):
            history_messages = [] # Bozuk geçmişi taklit etmesini engelle
            
        async for chunk in answer_chain.astream({
            "context": context,
            "history": history_messages if history_messages else "Geçmiş yok.",
            "question": text
        }):
            # Akış anında saptanan kelimeleri temizle
            clean_chunk = chunk
            for pattern, replacement in self.replacements.items():
                clean_chunk = re.sub(pattern, replacement, clean_chunk, flags=re.IGNORECASE)
            
            full_answer += clean_chunk
            
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

        # 3. Post-Processing & Validation
        validation = await agent_tools.compliance_validator(full_answer, context)
        eval_results = await evaluation_service.evaluate_response(text, full_answer, context)

        # Geçmişe ekle
        history.add_user_message(text)
        history.add_ai_message(full_answer)

        # Metadata'yı gönder
        metadata = {
            "type": "metadata",
            "thought": thought,
            "validation": validation,
            "evaluation": eval_results,
            "source_urls": list(set(re.findall(r"\[(std_\d+|internal_\d+|pub_\d+)\]", full_answer))),
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
