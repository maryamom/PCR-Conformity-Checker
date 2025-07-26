import streamlit as st
import json
import tempfile
from backend import verify_conformity_with_llm, run_prefix_detection_on_doc

st.set_page_config(page_title="Vérification de Conformité PCR", layout="wide")

st.image("logo.jpeg", width=160)
st.title(" Vérification de Conformité des Lignes PCR")

st.markdown("""
    <style>
        .conforme {
            background-color: #d4edda;
            color: #155724;
            padding: 6px;
            border-radius: 5px;
            margin-top: 5px;
        }
        .non-conforme {
            background-color: #f8d7da;
            color: #721c24;
            padding: 6px;
            border-radius: 5px;
            margin-top: 5px;
        }
        pre {
            background-color: #f5f5f5 !important;
            padding: 10px !important;
            border-radius: 5px !important;
            font-size: 14px !important;
        }
        .stProgress > div > div > div > div {
            background-color: #e67e22 !important;
        }
    </style>
""", unsafe_allow_html=True)

st.sidebar.header("📁 Fichiers")
docx_file = st.sidebar.file_uploader("Fichier de Spécification (.docx)", type=["docx"])
txt_file = st.sidebar.file_uploader("Fichier des Lignes PCR (.txt)", type=["txt"])

if st.sidebar.button("🚀 Lancer l'analyse") and docx_file and txt_file:
    docx_file.seek(0)
    txt_file.seek(0)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
        tmp_docx.write(docx_file.read())
        docx_path = tmp_docx.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_txt:
        tmp_txt.write(txt_file.read())
        txt_path = tmp_txt.name

    st.markdown("### 🔄 Analyse de conformité en cours...")
    prefixes = run_prefix_detection_on_doc(docx_path)

    with st.expander(" Préfixes détectés", expanded=False):
        for prefix in prefixes:
            st.code(json.dumps({
                "block": prefix["block_index"] + 1,
                "prefixe_detecte": prefix["prefixe_detecte"]
            }, indent=2, ensure_ascii=False), language="json")

    results = verify_conformity_with_llm(prefixes, txt_path)

    st.success("✅ Analyse terminée")

    for idx, res in enumerate(results):
        with st.expander(f"🧾 Ligne {idx + 1}", expanded=False):
            st.code(res.get("line", "[Ligne non définie]"))

            # ✅ Corriger la conformité globale (gère les valeurs booléennes ou texte)
            conforme_global = str(res.get("conforme", "")).lower().strip() == "oui"
            st.markdown(f"**Conforme :** {'✅ OUI' if conforme_global else '❌ NON'}")

            # ✅ Afficher erreurs éventuelles
            if "erreurs" in res:
                for err in res["erreurs"]:
                    st.error(f"❗ {err}")

            # ✅ Détails des champs
            if "champs" in res:
                st.markdown("###  Détails des Champs")
                with st.container():
                    st.dataframe(
                        [{
                            "Champ": champ["nom"],
                            "Valeur": champ["valeur"],
                            "Conforme": champ["conforme"],
                            "Erreur": champ["erreur"],
                            "Longueur Attendue": champ.get("longueur_attendue")
                        } for champ in res["champs"]],
                        use_container_width=True,
                        height=200
                    )

            # ✅ Ordre des champs
            if "ordre_champs" in res:
                oc = res["ordre_champs"]
                conforme_ordre = str(oc.get("conforme", "")).strip().lower() in ["oui", "yes", "true"]
                st.markdown("###  Ordre des Champs")
                st.write(f"**Conforme :** {'✅ OUI' if conforme_ordre else '❌ NON'}")
                st.write(f"**Ordre attendu :** {oc['ordre_attendu']}")
                st.write(f"**Ordre lu :** {oc['ordre_lu']}")
                if oc.get("suggestion_ordre_corrige"):
                    st.write(f"**Suggestion :** {oc['suggestion_ordre_corrige']}")

            # ✅ Ligne corrigée
            if "ligne_corrigee" in res:
                st.markdown("### ✍️ Ligne PCR Corrigée")
                st.code(res["ligne_corrigee"])

    st.markdown("---")
    st.download_button(
        label="📥 Télécharger le rapport JSON",
        data=json.dumps(results, ensure_ascii=False, indent=2),
        file_name="rapport_conformite_pcr.json",
        mime="application/json"
    )
