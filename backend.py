api_key="ta_clé"

import hashlib
from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
import os
import json
import time
from together import Together

def iter_block_items(parent):
    for child in parent.element.body:
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def get_table_paragraph_context_with_data(docx_path):
    doc = Document(docx_path)
    blocks = list(iter_block_items(doc))
    result = []
    last_para = None

    for block in blocks:
        if isinstance(block, Paragraph):
            if block.text.strip():
                last_para = block.text.strip()
        elif isinstance(block, Table):
            table = block
            rows = table.rows
            if not rows:
                continue

            headers = [cell.text.strip().lower().replace('\n', ' ') for cell in rows[0].cells]
            headers = [h for h in headers if h]
            champs = []
            for row in rows[1:]:
                champ = {headers[i]: cell.text.strip() for i, cell in enumerate(row.cells) if i < len(headers)}
                champs.append(champ)
            result.append({
                "context_paragraph": last_para,
                "table_data": champs,
                "block_index": len(result)
            })
    return result







client = Together(api_key=api_key)
MODEL_NAME = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"


def build_prompt_json_ready(block_json):
    block_index = block_json.get("block_index", -1)
    instruction = f"""
Tu es un assistant intelligent chargé d'analyser un bloc issu d’un document de spécifications.

Ce bloc contient :
- Un paragraphe d’introduction (`context_paragraph`) décrivant le contexte du tableau.
- Un tableau structuré (`table_data`) contenant des informations techniques sous forme de lignes, avec des champs tels que "champ", "format attendu", "contraintes supplémentaires", etc.
- Un identifiant de bloc (`block_index`).

---

🎯 **Ton objectif** :
Détecter un **préfixe attendu** pour ce bloc.  
UN PRÉFIXE EXISTE TOUJOURS, MÊME S’IL EST IMPLICITE.

Un préfixe est une suite de lettres ou chiffres (souvent 2 à 5 caractères) utilisée comme début standardisé d’un identifiant ou d’un champ. Il peut être :
- clairement mentionné (explicite)
- déduit du format ou d’un motif répété dans les champs (implicite)

Même si le préfixe n’est pas formulé directement dans les textes, tu dois en **déduire le plus probable**, basé sur les exemples donnés.

🚫 Tu ne dois JAMAIS répondre `null` : déduis toujours un préfixe probable à partir des indices visibles.
---
📌 **Où peut-on trouver un préfixe ?**
- Dans le `context_paragraph`, par exemple :
  - "Le préfixe attendu est ABC"
  - "Chaque identifiant commence par AZE"
  - Sous format d'un mot isolé par exemple "04T"
- Dans le `table_data`, par exemple dans les colonnes :
  - "Format attendu" : "CBE + 8 chiffres"
  - "Contraintes supplémentaires" : "doit commencer par CLT001"
  - ou IMPLICITEMENT !! 

✅ **Exemples valides de préfixes** :
- `CBE`
- `AZE`
- `032`
- `CLT001`
- `PRD`

🧠 Exemple implicite :  
Si dans la colonne `"format attendu"` tu vois `"023 + 15 chiffres"`, alors le préfixe attendu est `"023"`.

❗Tu dois répondre UNIQUEMENT avec le JSON demandé, sans aucune explication ni phrase en dehors du bloc JSON.
🔒 La réponse doit être strictement :
- au format JSON valide
- sans texte avant ou après
- sans Markdown (` ```json ` etc.)

📤 **Format de réponse strictement attendu (JSON uniquement)** :
{{
  "block_index": {block_index},
  "prefixe_detecte": "..."
}}

Voici le bloc à analyser :
{json.dumps(block_json, indent=2, ensure_ascii=False)}
"""
    return instruction.strip()



#  Fonction de détection via LLaMA

def detect_prefix_llama_direct(block):
    prompt = build_prompt_json_ready(block)
    response_text = ""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.choices[0].message.content.strip()
        print(f"{block['block_index']}:\n{response_text}")
        return json.loads(response_text)
    except Exception as e:
     print(f"❌ Erreur de parsing pour bloc {block.get('block_index')}: {e}")
     return {
         "block_index": block.get("block_index", -1),
         "prefixe_detecte": "UNKNOWN",  # Jamais None
         "error": str(e),
         "raw_response": response_text
    }







def run_prefix_detection_on_doc(docx_path):
    blocks = get_table_paragraph_context_with_data(docx_path)
    results = []
    for block in blocks:
        result = detect_prefix_llama_direct(block)
        prefix = result.get("prefixe_detecte")

        # Format final simplifié pour la suite du pipeline

        results.append({
            "prefixe_detecte": prefix,
            "table_data": block.get("table_data", []),
            "block_index": block.get("block_index", -1)
        })
        time.sleep(3)
    return results





def extract_pcr_lines(txt_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def match_pcr_lines_to_blocks_by_prefix(blocks_with_prefixes, txt_path):
    #blocks_with_prefixes = get_cached_prefix_detection(docx_path)
    pcr_lines = extract_pcr_lines(txt_path)
    matched_lines = []
    for i, line in enumerate(pcr_lines):
        for block in blocks_with_prefixes:
            prefix = block.get("prefixe_detecte")
            if prefix and line.startswith(prefix):
                matched_lines.append({
                    "line_index": i,
                    "line": line,
                    "matched_block": block
                })
                break #dés qu'un bloc matche , on passe à la ligne suivante
        else:
            matched_lines.append({
                "line_index": i,
                "line": line,
                "matched_block_index": None
            })
    return matched_lines

def build_conformity_prompt(line, matched_block):
    return f"""
Tu es un assistant intelligent et rigoureux chargé de vérifier la conformité d’une ligne issue d’un fichier de Transactions PCR (Plan de Contrôle de Référence) avec les spécifications fournies.

---
Voici la ligne à analyser et ses spécifications :

Informations disponibles :  
- Ligne PCR à analyser :  
\"{line}\"

- Spécifications du bloc associé :  
{json.dumps(matched_block["table_data"], indent=2, ensure_ascii=False)}

---

Ta mission est de :
1. Vérifier que tous les champs listés dans les spécifications sont présents dans la ligne PCR.

2. Pour chaque champ, contrôler que la valeur extraite respecte strictement les spécifications (type, longueur, préfixe, contraintes, etc.).

3. Vérifier que l’ordre des champs dans la ligne PCR correspond exactement à l’ordre défini dans les spécifications.

4. Si l’ordre est incorrect, proposer l’ordre corrigé sous forme d’une liste ordonnée des noms des champs.

5. Proposer une suggestion de ligne PCR corrigée qui respecte à la fois l’ordre, les longueurs, et les contraintes.

---

Consignes importantes :
- Ta réponse doit être strictement un objet JSON au format suivant, sans aucun texte ni explication supplémentaire.
- Utilise les clés exactes suivantes :
  - "line" : la ligne PCR analysée (chaîne de caractères)
  - "conforme" : "oui" ou "non", selon la conformité globale de la ligne

  - "champs" : une liste d’objets, un par champ, contenant :  
    - "nom" : nom du champ (ex: "Code Partenaire")  
    - "valeur" : valeur extraite du champ dans la ligne PCR  
    - "conforme" : "oui" ou "non"  
    - "erreur" : description précise de l’erreur (ou null si conforme)  
    - "longueur_attendue" : nombre entier (longueur attendue du champ)


  - Objet "ordre_champs" : 
  . Vérifie si l’ordre des champs dans la ligne PCR correspond exactement à l’ordre défini dans les spécifications.

   - Compare la position des champs dans la ligne par rapport à l’ordre attendu indiqué dans le tableau des spécifications.
   - Si l’ordre est exactement le même, indique `"conforme": "oui"`.

   - Si l’ordre est différent, indique `"conforme": "non"` et fournis obligatoirement :
     - `"ordre_attendu"` : liste ordonnée des noms des champs selon les spécifications.
     - `"ordre_lu"` : liste ordonnée des noms des champs tels qu’ils apparaissent dans la ligne PCR.
     - `"suggestion_ordre_corrige"` : liste ordonnée des noms des champs dans le bon ordre.

   ⚠️ Très important :
   - Ne JAMAIS inclure `"suggestion_ordre_corrige"` si `"conforme"` est `"oui"`.
   - Inclure `"suggestion_ordre_corrige"` uniquement quand l’ordre des champs est incorrect.

    voila  un Exemple ne généralise pas ça!!!
    JSON attendu pour "ordre_champs" :

    "ordre_champs": {{
    "conforme": "non",
    "ordre_attendu": ["Champ 1", "Champ 2", "Champ 3"],
    "ordre_lu": ["Champ 2", "Champ 1", "Champ 3"],
    "suggestion_ordre_corrige": ["Champ 1", "Champ 2", "Champ 3"]
    }}

    Et si l'ordre est correct :


    "ordre_champs": {{
    "conforme": "oui",
    "ordre_attendu": ["Champ 1", "Champ 2", "Champ 3"],
    "ordre_lu": ["Champ 1", "Champ 2", "Champ 3"]
    }}



  - objet "ligne_corrigee" : chaîne de caractères correspondant à la ligne PCR corrigée

Sois précis, rigoureux et concis dans ta réponse JSON.


"""

def verify_conformity_with_llm(blocks_with_prefixes, txt_path):
    client = Together(api_key=api_key)
    matched = match_pcr_lines_to_blocks_by_prefix(blocks_with_prefixes, txt_path)
    results = []
    for line_obj in matched:
        line = line_obj["line"]
        matched_block = line_obj.get("matched_block")
        if not matched_block:
            results.append({
                "line": line,
                "conforme": False,
                "erreurs": ["Aucun bloc associé à cette ligne."],
                "debug": {
                    #"prefixes_detectes": [b.get("prefixe_detecte") for b in run_prefix_detection_on_doc (docx_path)],
                    "ligne_originale": line,
                    "ligne_sans_espaces": line.strip().replace(" ", "")
                }
            })
            continue
        prompt = build_conformity_prompt(line, matched_block)
        try:
            response = client.chat.completions.create(
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.choices[0].message.content.strip()
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                result = {
                    "line": line,
                    "conforme": False,
                    "erreurs": ["Réponse JSON invalide du LLM."],
                    "raw_response": response_text
                }
            results.append(result)
        except Exception as e:
            results.append({
                "line": line,
                "conforme": False,
                "erreurs": [f"Erreur LLM : {str(e)}"]
            })
        time.sleep(2)
    return results
