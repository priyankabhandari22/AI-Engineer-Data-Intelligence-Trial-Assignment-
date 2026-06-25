import pandas as pd, os

d = 'data/exports'
for f in ['Startups.csv', 'Products.csv', 'Research Papers.csv', 'Jobs.csv', 'News.csv']:
    p = os.path.join(d, f)
    df = pd.read_csv(p)
    print(f'=== {f} ({len(df)} rows) ===')
    for c in df.columns:
        na = df[c].isna().sum()
        max_len = df[c].astype(str).str.len().max() if df[c].dtype == 'object' else 0
        sample = df[c].dropna().iloc[0] if not df[c].dropna().empty else ''
        print(f'  {c}: {na} nulls, max_len={max_len}, e.g. "{str(sample)[:60]}"')
    print()
