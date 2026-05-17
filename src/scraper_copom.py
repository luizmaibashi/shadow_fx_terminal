# -*- coding: utf-8 -*-
"""
scraper_copom.py - Shadow FX Terminal (Fase 2)
================================================
Coleta automatica de Atas do Copom diretamente do site do Banco Central do Brasil.
Fonte: https://www.bcb.gov.br/publicacoes/atascopom
Custo: ZERO. Dados publicos e abertos do BCB.

Saida: 
    - Arquivos .txt em data/raw/atas_copom/
    - CSV consolidado em data/raw/atas_copom_index.csv (data, reuniao, url, texto_resumo)
"""

import re
import time
import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

# Path central do utils
import sys
sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_RAW

# Diretorio especifico para atas
ATAS_DIR = DATA_RAW / "atas_copom"
ATAS_DIR.mkdir(parents=True, exist_ok=True)

# Periodo de interesse (alinhado com o paper)
ANO_INICIO = 2022
ANO_FIM    = 2025

# Headers para simular um browser real e evitar bloqueio
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

BCB_BASE = "https://www.bcb.gov.br"
COPOM_URL = f"{BCB_BASE}/publicacoes/atascopom"


def listar_links_atas() -> list[dict]:
    """Acessa a pagina de listagem de atas do BCB e extrai os links de cada reuniao.
    
    Returns:
        Lista de dicts com 'data', 'reuniao', 'url' para cada ata disponivel.
    """
    print(f"[1/3] Acessando pagina de listagem: {COPOM_URL}")
    
    resp = requests.get(COPOM_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "lxml")
    
    links_atas = []
    
    # O BCB lista as atas em tabelas ou listas de links
    # Buscamos todos os links que contenham "copom" ou "reuniao" na URL
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        texto = a_tag.get_text(strip=True)
        
        # Filtro: links que apontam para reunioes do Copom
        if ("copom" in href.lower() or "reuniao" in href.lower()) and texto:
            # Tentar extrair o ano do texto ou da URL
            ano_match = re.search(r'20(2[2-9]|[3-9]\d)', href + texto)
            if ano_match:
                ano = int(ano_match.group(0))
                if ANO_INICIO <= ano <= ANO_FIM:
                    url_completa = href if href.startswith("http") else BCB_BASE + href
                    links_atas.append({
                        "texto"   : texto,
                        "url"     : url_completa,
                        "ano"     : ano,
                    })
    
    # Remover duplicatas pela URL
    vistos = set()
    links_unicos = []
    for item in links_atas:
        if item["url"] not in vistos:
            vistos.add(item["url"])
            links_unicos.append(item)
    
    print(f"   Encontrados {len(links_unicos)} links de atas para o periodo {ANO_INICIO}-{ANO_FIM}.")
    return links_unicos


def extrair_texto_ata(url: str) -> str:
    """Acessa a pagina de uma ata e extrai o texto principal.
    
    Args:
        url: URL completa da pagina da ata no site do BCB.
    
    Returns:
        Texto limpo da ata (sem HTML).
    """
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "lxml")
    
    # Tentar encontrar o container principal de conteudo
    conteudo = (
        soup.find("div", class_="conteudo-ata") or
        soup.find("article") or
        soup.find("div", class_="text-content") or
        soup.find("main")
    )
    
    if conteudo:
        texto = conteudo.get_text(separator="\n", strip=True)
    else:
        # Fallback: pegar todo o texto do body
        body = soup.find("body")
        texto = body.get_text(separator="\n", strip=True) if body else ""
    
    # Limpeza: remover linhas muito curtas (menus, rodapes) e linhas duplicadas
    linhas = [l.strip() for l in texto.split("\n") if len(l.strip()) > 30]
    texto_limpo = "\n".join(linhas)
    
    return texto_limpo


def salvar_ata(texto: str, nome_arquivo: str) -> Path:
    """Salva o texto de uma ata em arquivo .txt."""
    caminho = ATAS_DIR / nome_arquivo
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def extrair_palavras_chave(texto: str) -> dict:
    """Analise simples de tom do Copom baseada em frequencia de palavras-chave.
    
    Esta e a versao 'heuristica' de classificacao de tom antes do Agente RAG.
    Serve como baseline e validacao da Fase 2.
    
    Returns:
        dict com contagens e score_hawkish (0=dovish/expansionista, 1=hawkish/restritivo)
    """
    texto_lower = texto.lower()
    
    # Palavras que indicam APERTO monetario (hawkish = ancora inflacionaria)
    hawkish = [
        "elevacao", "elevou", "ajuste", "aperto", "restricao",
        "inflacao", "meta", "convergencia", "acelerou", "pressao",
        "deterioracao", "risco fiscal", "dominancia fiscal",
        "alta de juros", "selic mais alta", "ambiente desafiador"
    ]
    
    # Palavras que indicam AFROUXAMENTO (dovish = risco de perda de ancora)
    dovish = [
        "reducao", "reduziu", "corte", "flexibilizacao", "estimulo",
        "atividade economica", "mercado de trabalho", "benigno",
        "arrefecimento", "desinflacao", "queda", "desaceleracao",
        "espaco para reducao"
    ]
    
    contagem_hawkish = sum(texto_lower.count(w) for w in hawkish)
    contagem_dovish  = sum(texto_lower.count(w) for w in dovish)
    total            = contagem_hawkish + contagem_dovish
    
    # Score de 0 (totalmente dovish) a 1 (totalmente hawkish)
    score_hawkish = contagem_hawkish / total if total > 0 else 0.5
    
    return {
        "contagem_hawkish" : contagem_hawkish,
        "contagem_dovish"  : contagem_dovish,
        "score_hawkish"    : round(score_hawkish, 3),
        "tom"              : "hawkish" if score_hawkish > 0.55 else ("dovish" if score_hawkish < 0.45 else "neutro")
    }


def coletar_todas_atas() -> pd.DataFrame:
    """Pipeline completo: lista, baixa e processa todas as atas do periodo.
    
    Returns:
        DataFrame com colunas: url, ano, texto, score_hawkish, tom.
    """
    links = listar_links_atas()
    
    if not links:
        print("\nNenhum link encontrado. Verifique se o site do BCB mudou sua estrutura.")
        print("Gerando base de dados historica ESTIMADA para prototypagem...")
        return _gerar_base_estimada()
    
    print(f"\n[2/3] Baixando e processando {len(links)} atas...")
    registros = []
    
    for i, item in enumerate(links):
        print(f"   [{i+1}/{len(links)}] {item['texto'][:60]}...")
        try:
            texto  = extrair_texto_ata(item["url"])
            analise = extrair_palavras_chave(texto)
            
            nome_arquivo = re.sub(r'[^a-zA-Z0-9_-]', '_', item["texto"][:50]) + ".txt"
            salvar_ata(texto, nome_arquivo)
            
            registros.append({
                "url"              : item["url"],
                "ano"              : item["ano"],
                "texto_tamanho"    : len(texto),
                **analise
            })
            
            # Respeitar o servidor: esperar entre requisicoes
            time.sleep(1.5)
            
        except Exception as e:
            print(f"   ERRO ao processar {item['url']}: {e}")
    
    df_atas = pd.DataFrame(registros)
    
    # Salvar index consolidado
    idx_path = DATA_RAW / "atas_copom_index.csv"
    df_atas.to_csv(idx_path, index=False, encoding="utf-8")
    print(f"\n[3/3] Index consolidado salvo em: {idx_path}")
    
    return df_atas


def _gerar_base_estimada() -> pd.DataFrame:
    """Fallback: gera base historica estimada do tom do Copom 2022-2025.
    
    Baseado nas decisoes reais publicadas no site do BCB e no paper.
    Permite que o pipeline continue mesmo se o scraper falhar.
    """
    # Reunioes reais do Copom com tom estimado baseado na decisao de juros
    reunioes = [
        # 2022: Ciclo de alta da Selic (hawkish dominante)
        {"data": "2022-02-02", "decisao_selic": +1.50, "tom": "hawkish"},
        {"data": "2022-03-16", "decisao_selic": +1.00, "tom": "hawkish"},
        {"data": "2022-05-04", "decisao_selic": +1.00, "tom": "hawkish"},
        {"data": "2022-06-15", "decisao_selic": +0.50, "tom": "hawkish"},
        {"data": "2022-08-03", "decisao_selic": +0.50, "tom": "hawkish"},
        {"data": "2022-09-21", "decisao_selic":  0.00, "tom": "neutro"},
        {"data": "2022-10-26", "decisao_selic":  0.00, "tom": "neutro"},
        {"data": "2022-12-07", "decisao_selic":  0.00, "tom": "neutro"},
        # 2023: Inicio do ciclo de cortes (virada dovish)
        {"data": "2023-02-01", "decisao_selic":  0.00, "tom": "neutro"},
        {"data": "2023-03-22", "decisao_selic":  0.00, "tom": "neutro"},
        {"data": "2023-05-03", "decisao_selic":  0.00, "tom": "neutro"},
        {"data": "2023-06-21", "decisao_selic":  0.00, "tom": "neutro"},
        {"data": "2023-08-02", "decisao_selic": -0.50, "tom": "dovish"},
        {"data": "2023-09-20", "decisao_selic": -0.50, "tom": "dovish"},
        {"data": "2023-11-01", "decisao_selic": -0.50, "tom": "dovish"},
        {"data": "2023-12-13", "decisao_selic": -0.50, "tom": "dovish"},
        # 2024: Desaceleracao + reversao (fiscal piorando)
        {"data": "2024-01-31", "decisao_selic": -0.50, "tom": "dovish"},
        {"data": "2024-03-20", "decisao_selic": -0.50, "tom": "dovish"},
        {"data": "2024-05-08", "decisao_selic": -0.25, "tom": "neutro"},
        {"data": "2024-06-19", "decisao_selic":  0.00, "tom": "neutro"},
        {"data": "2024-07-31", "decisao_selic":  0.00, "tom": "neutro"},
        {"data": "2024-09-18", "decisao_selic": +0.25, "tom": "hawkish"},
        {"data": "2024-11-06", "decisao_selic": +0.50, "tom": "hawkish"},
        {"data": "2024-12-11", "decisao_selic": +1.00, "tom": "hawkish"},
        # 2025: Continuidade do aperto (dominancia fiscal)
        {"data": "2025-01-29", "decisao_selic": +1.00, "tom": "hawkish"},
        {"data": "2025-03-19", "decisao_selic": +1.00, "tom": "hawkish"},
        {"data": "2025-05-07", "decisao_selic": +0.50, "tom": "hawkish"},
    ]
    
    df = pd.DataFrame(reunioes)
    df["data"]          = pd.to_datetime(df["data"])
    df["score_hawkish"] = df["decisao_selic"].apply(
        lambda x: 0.8 if x > 0 else (0.2 if x < 0 else 0.5)
    )
    df["fonte"] = "estimativa_historica"
    
    # Salvar como CSV
    idx_path = DATA_RAW / "atas_copom_index.csv"
    df.to_csv(idx_path, index=False, encoding="utf-8")
    print(f"Base estimada salva em: {idx_path} ({len(df)} reunioes)")
    return df


if __name__ == "__main__":
    print("=" * 60)
    print("  SHADOW FX TERMINAL - Coleta de Atas do Copom (Fase 2)")
    print("=" * 60)
    
    df_atas = coletar_todas_atas()
    
    print("\n--- Resumo das Atas Coletadas ---")
    print(df_atas[["data", "tom", "score_hawkish", "decisao_selic"]].to_string() 
          if "decisao_selic" in df_atas.columns 
          else df_atas[["tom", "score_hawkish"]].value_counts().to_string())
    
    print("\n[OK] Fase 2 de coleta concluida.")
    print("     Proximo passo: Integrar o score_hawkish ao Indice de Risco Fiscal.")
