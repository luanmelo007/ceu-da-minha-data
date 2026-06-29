"""
Execute uma vez para baixar e filtrar o catálogo estelar.
Gera o arquivo stars.csv que será commitado no repositório.
"""
import pandas as pd
import requests
import io

print("Baixando catálogo HYG...")

urls = [
    # Nova localização (GitHub, branch main)
    "https://raw.githubusercontent.com/astronexus/HYG-Database/main/hyg/CURRENT/hygdata_v41.csv",
    # Versão anterior ainda disponível em fork
    "https://raw.githubusercontent.com/kiloquad/__HYG-Database/master/hygdata_v3.csv",
]

df = None
for url in urls:
    try:
        print(f"Tentando: {url}")
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        print(f"✅ Baixado com sucesso!")
        break
    except Exception as e:
        print(f"❌ Falhou → {e}")

if df is None:
    print("\nNão foi possível baixar automaticamente.")
    print("Acesse https://astronexus.com/hyg e baixe manualmente o arquivo CSV.")
    print("Renomeie para 'hygdata_v41.csv' e coloque na pasta do projeto.")
    print("Depois rode novamente este script.")
    exit(1)

# Filtra apenas colunas necessárias e magnitude <= 7.5
df = df[['ra', 'dec', 'mag']].dropna()
df = df[df['mag'] <= 7.5].reset_index(drop=True)
df.to_csv("stars.csv", index=False)

print(f"✅ stars.csv salvo com {len(df):,} estrelas!")
print("Agora rode: git add stars.csv && git commit -m 'adiciona stars.csv' && git push")