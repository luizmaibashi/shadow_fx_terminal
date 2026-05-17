# -*- coding: utf-8 -*-
"""
agente_rag.py - Shadow FX Terminal (Fase 5)
===========================================
Agente de IA Generativa atuando como Juiz de Compliance (LLM-as-a-judge).
Padrão CS230: Filtro Cascata Camada 3.

Nota Técnica (RAG vs Context Injection):
    Este módulo implementa "Context Injection por data": buscamos a Ata do
    Copom mais próxima à transação usando filtro temporal, e injetamos esse
    texto como contexto no prompt do LLM.
    RAG completo (com embeddings e banco vetorial como FAISS/Chroma) seria o
    próximo passo de evolução deste agente para suportar buscas semânticas
    nas atas completas do BCB.

Fluxo:
    1. Busca (por data) a Ata do Copom anterior à transação.
    2. Constrói o prompt com dados da transação + contexto macro.
    3. Envia ao Gemini 2.5 Flash para julgamento e geração do COAF.
    4. Fallback heurístico se a API estiver indisponível.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_RAW

# Carrega chaves de API
load_dotenv(Path(__file__).parent.parent / ".env")
API_KEY = os.getenv("GEMINI_API_KEY")

# Inicializa o cliente com o SDK atual (google-genai >= 1.0)
client = genai.Client(api_key=API_KEY) if API_KEY else None

def recuperar_contexto_copom(data_transacao: pd.Timestamp) -> str:
    """Busca a Ata do Copom mais recente antes da transação (RAG simples)."""
    caminho_copom = DATA_RAW / "atas_copom_index.csv"
    if not caminho_copom.exists():
        return "Contexto Copom indisponível."
        
    df = pd.read_csv(caminho_copom, parse_dates=["data"])
    # Filtra atas anteriores à transação
    df_passado = df[df["data"] <= data_transacao].sort_values("data", ascending=False)
    
    if df_passado.empty:
        return "Nenhuma Ata do Copom encontrada anterior a esta data."
        
    ata = df_passado.iloc[0]
    score = ata.get('score_hawkish', 0.5)
    tom = ata.get('tom', 'neutro')
    
    # Como a base histórica pode não ter os textos completos salvos, usamos o tom para criar o contexto
    texto_contexto = ata.get('texto', f"O comitê decidiu adotar um tom {tom} nesta reunião. A decisão da Selic foi ajustada em {ata.get('decisao_selic', 0.0)}%.")
    
    resumo = (
        f"Ata do Copom de {ata['data'].strftime('%d/%m/%Y')}: "
        f"Tom = {'Hawkish (Rígido)' if score > 0.5 else 'Dovish (Brando)'} "
        f"(Score: {score:.2f}). "
        f"Contexto: {texto_contexto[:500]}"
    )
    return resumo

def julgar_transacao_llm(transacao: dict) -> str:
    """
    Envia a transação para o LLM atuar como juiz e gerar o COAF.
    """
    # 1. Recuperação (RAG)
    try:
        data_tx = pd.to_datetime(transacao.get("data", pd.Timestamp.now()))
    except:
        data_tx = pd.Timestamp.now()
        
    contexto_macro = recuperar_contexto_copom(data_tx)
    
    # 2. Construção do Prompt
    system_prompt = """Você é um Analista Sênior de Compliance AML/PLD em uma corretora de criptomoedas no Brasil.
Seu trabalho é analisar transações de Stablecoins (USDT) baseando-se nas Resoluções BCB 519, 520 e 521 de 2026.
Você deve distinguir entre "Poupador Assustado" (movimento legítimo de proteção devido ao risco fiscal) e "Fracionador/Smurfing" (crime financeiro de evasão de divisas).

Retorne SEMPRE no seguinte formato:
VEREDITO: [NORMAL, SUSPEITO, ou REQUER_INVESTIGACAO]
JUSTIFICATIVA: [Uma frase explicando o porquê]
RASCUNHO COAF: [Pequeno parágrafo técnico pronto para ser enviado ao COAF, se suspeito, ou "Não aplicável" se normal]"""

    user_prompt = f"""
=== DADOS DA TRANSAÇÃO ===
- Usuário: {transacao.get('user_id')}
- Valor: R$ {transacao.get('valor_brl', 0):,.2f}
- Hora: {transacao.get('hora', 0)}h
- Wallets destino: {transacao.get('wallets_unicas', 1)} diferentes no dia
- Score do Modelo (Isolation Forest): {transacao.get('score_ml', 0)}/100
- Flags: {transacao.get('razoes', 'Nenhuma')}

=== CONTEXTO MACROECONÔMICO (RAG Copom) ===
{contexto_macro}

Por favor, forneça seu julgamento técnico.
"""

    # 3. Geração (LLM Call) — SDK atual: google.genai
    try:
        if not client or not API_KEY or API_KEY == "SUA_API_KEY_AQUI":
            raise ValueError("API Key ausente ou inválida")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,  # baixo para respostas mais determinísticas em compliance
            ),
        )
        return response.text

    except Exception as e:
        # Graceful Degradation / Fallback MLOps
        print(f"[LLM Agent Fallback Ativado] Erro na API: {e}")
        return _fallback_heuristico(transacao)

def _fallback_heuristico(tx: dict) -> str:
    """Caso a API falhe, não quebramos o pipeline. Usamos uma árvore de decisão simples."""
    score = tx.get('score_ml', 0)
    wallets = tx.get('wallets_unicas', 1)
    
    if score >= 70 or wallets > 5:
        return (
            "VEREDITO: SUSPEITO (Fallback Mode)\n"
            "JUSTIFICATIVA: Transação apresenta alto score anômalo e multiplicidade de carteiras destino, sugerindo fracionamento.\n"
            "RASCUNHO COAF: Transação apresenta características tipológicas de evasão de divisas via smurfing em stablecoins, fragmentando o envio de valores. Encaminhado para bloqueio cautelar."
        )
    return (
        "VEREDITO: REQUER_INVESTIGACAO (Fallback Mode)\n"
        "JUSTIFICATIVA: O score é intermediário e a API do LLM falhou ao processar a nuance. Análise humana requerida.\n"
        "RASCUNHO COAF: Não aplicável ainda."
    )

if __name__ == "__main__":
    # Teste rápido do Agente
    print("🤖 Iniciando Agente RAG de Compliance...")
    tx_teste = {
        "user_id": "USR_TEST_SMURF",
        "data": "2024-09-15",
        "valor_brl": 9500.0,
        "hora": 3,
        "wallets_unicas": 12,
        "score_ml": 85.0,
        "razoes": "Possível fracionamento (smurfing) | Muitas wallets no dia | Madrugada"
    }
    
    print("\nEnviando caso suspeito para julgamento...")
    resultado = julgar_transacao_llm(tx_teste)
    print("\n" + "="*50)
    print("RESULTADO DO LLM:")
    print("="*50)
    print(resultado)
