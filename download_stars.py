"""
Execute uma vez para baixar e filtrar o catálogo estelar.
Gera o arquivo stars.csv que será commitado no repositório.
"""
import pandas as pd
import requests
import io

print("Baixando catálogo HYG...")

urls = [
    "https://raw.githubusercontent.com/astronexus/HYG-Database/main/hyg/CURRENT/hygdata_v41.csv",
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
    print("Não foi possível baixar o catálogo.")
    exit(1)

# Mantém ra, dec, mag e ci (índice de cor B-V para colorir as estrelas)
cols = [c for c in ['ra', 'dec', 'mag', 'ci'] if c in df.columns]
df = df[cols].dropna(subset=['ra', 'dec', 'mag'])
df = df[df['mag'] <= 7.5].reset_index(drop=True)
df.to_csv("stars.csv", index=False)

print(f"✅ stars.csv salvo com {len(df):,} estrelas!")
print("Agora rode: git add stars.csv && git commit -m 'atualiza stars.csv com cores' && git push")