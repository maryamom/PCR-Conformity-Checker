
# Système de Vérification de Conformité de PCR

## Description

Ce projet est un outil automatisé de vérification de conformité des lignes PCR (Plan de Contrôle de Référence) par rapport à des spécifications techniques.  
Il permet de détecter et valider les préfixes des lignes PCR, d'analyser la conformité des champs dans chaque ligne, en s’appuyant sur des modèles de langage (LLM) pour une détection intelligente.
L’interface utilisateur est réalisée avec **Streamlit**, tandis que la logique métier et les interactions avec les modèles LLM sont contenues dans un module backend dédié.
(voir le rapport pour plus de détails)

---

## Fonctionnalités principales

- Extraction des blocs de spécifications depuis un fichier `.docx` (paragraphe + tableau)  
- Détection automatique des préfixes des blocs à l’aide de modèles LLM (meta-llama, Mistral, etc.) via TogetherAI  
- Vérification de la conformité des lignes PCR en fonction des préfixes détectés  
- Analyse détaillée des champs : présence, format, contraintes, ordre  
- Suggestions de corrections en cas de non-conformité  
- Export du rapport de conformité au format JSON  

---

## Structure du projet

```

/systeme-verification-conformite-pcr
│
├── interface.py            # Interface utilisateur Streamlit
├── backend.py             # Logique métier et appels LLM
├── logo.jpeg              # Logo de l'entreprise affiché dans l’interface
├── /samples               # Données exemples (specifications .docx, lignes PCR .txt)
├── rapport.pdf            # Rapport PDF détaillé du projet
├── test.ipynb             # Notebook explicatif avec fonctions et outputs pour mieux expliquer la méthodologie
└── requirements.txt       # Dépendances Python

````

---

## Installation

1. Cloner le dépôt :  
```bash
git clone https://github.com/ton-utilisateur/systeme-verification-conformite-pcr.git
cd systeme-verification-conformite-pcr
````

2. Créer un environnement virtuel (recommandé) :

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

4. Lancer l’interface Streamlit :

```bash
streamlit run interface.py
```

---

## Usage

* Charger un fichier de spécifications `.docx` contenant les tableaux avec les contraintes
* Charger un fichier `.txt` contenant les lignes PCR à vérifier
* Cliquer sur "Lancer l’analyse" pour démarrer la vérification
* Consulter les résultats détaillés ligne par ligne dans l’interface
* Télécharger le rapport JSON complet pour archivage ou analyses ultérieures

---

## Technologies utilisées

* Python 3.10+
* [Streamlit](https://streamlit.io/) pour l’interface utilisateur
* [python-docx](https://python-docx.readthedocs.io/en/latest/) pour la lecture des fichiers `.docx`
* [TogetherAI](https://together.xyz/) pour les appels aux modèles de langage (meta-llama, Mistral, etc.)
* JSON pour la structuration des données et des résultats

---

## Limitations et perspectives

* Le système utilise actuellement TogetherAI avec une limite de 6000 tokens/minute et un délai de 3 secondes entre les appels, ce qui peut ralentir le traitement
* Les réponses des modèles LLM peuvent parfois être incomplètes ou incorrectes, nécessitant une supervision ou une future migration vers des API payantes comme Gemini pour plus de robustesse
* Possibilité d’ajouter une interface d’entrée manuelle du préfixe si la détection automatique échoue
* 
## Diagramme de Flux :

<img src="https://github.com/user-attachments/assets/ab3cb0b1-e254-4b8a-a5f1-9d778426c767" alt="Diagramme de flux" style="max-width:100%; height:auto;" />

---

## L'application :

<img src="https://github.com/user-attachments/assets/f749baa1-cb1c-407d-b2e1-e3bedd2e88bd" alt="App Screenshot 1" style="max-width:100%; height:auto;" />
<br>
<img src="https://github.com/user-attachments/assets/80d8b979-433c-4062-8924-38280eb983a6" alt="App Screenshot 2" style="max-width:100%; height:auto;" />
<br>
<img src="https://github.com/user-attachments/assets/b2da9a5e-4a96-4c84-a463-1da0af24f561" alt="App Screenshot 3" style="max-width:100%; height:auto;" />
<br>
<img src="https://github.com/user-attachments/assets/f2eed875-cc2d-4c39-ad27-7e4a390fbf61" alt="App Screenshot 4" style="max-width:100%; height:auto;" />
<br>
<img src="https://github.com/user-attachments/assets/844c8cd2-cb12-480b-b783-68c54e097203" alt="App Screenshot 5" style="max-width:100%; height:auto;" />
<br>
<img src="https://github.com/user-attachments/assets/bad2e3fe-4235-4f24-9bdf-280f590121d4" alt="App Screenshot 6" style="max-width:100%; height:auto;" />

## Auteur

**Mariem Omrani**
Étudiante en Master Big Data & Intelligence Artificielle


---



```
