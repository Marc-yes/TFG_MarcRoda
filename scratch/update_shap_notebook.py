import json
import os

paths = [
    'Principals/explicabilitat_shap.ipynb',
    'Codi_Projecte/ai/explicabilitat_shap.ipynb'
]

for p in paths:
    if not os.path.exists(p):
        continue
    with open(p, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    updated = False
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            new_source = []
            for line in cell['source']:
                if 'X_trans_chronic = preprocessor.transform(X_chronic)' in line:
                    new_source.append('preprocessor_s2 = model_s2.named_steps["preprocessor"]\n')
                    new_source.append('X_trans_chronic = preprocessor_s2.transform(X_chronic)\n')
                    new_source.append('feature_names_clean_s2 = [f.replace("num__", "").replace("cat__", "") for f in preprocessor_s2.get_feature_names_out()]\n')
                    updated = True
                elif 'X_trans_chronic_df = pd.DataFrame(X_trans_chronic, columns=feature_names_clean)' in line:
                    new_source.append('X_trans_chronic_df = pd.DataFrame(X_trans_chronic, columns=feature_names_clean_s2)\n')
                    updated = True
                else:
                    new_source.append(line)
            cell['source'] = new_source
    
    if updated:
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
            f.write('\n')
        print(f'Successfully updated {p}')
