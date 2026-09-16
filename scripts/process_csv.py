#!/usr/bin/env python3
"""
Transform 226Multi_2.csv into optimized multilingual JSON structure.

Input: 226Multi_2.csv (semicolon-delimited, UTF-8, denormalized format)
Columns: Lingua, ID, Nome Modello, Descrizione, Colore Nome, Colore Codice, 
          Colore URL Immagine, Consigli di Vendita, Gestione Obiezioni

Output: src/data/models.json
Structure:
{
  "languages": ["IT", "EN", "RU"],
  "models": [
    {
      "id": 1,
      "name": "CANDIDO",
      "descriptions": { "IT": "...", "EN": "...", "RU": "..." },
      "salesAdvice": { "IT": "...", "EN": "...", "RU": "..." },
      "objectionHandling": { "IT": "...", "EN": "...", "RU": "..." },
      "colorVariants": [
        { "name": { "IT": "Bianco", "EN": "White", "RU": "..." }, 
          "code": "0101", 
          "imageUrl": "https://..." }
      ]
    }
  ]
}
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional


def clean_text(text: Optional[str]) -> str:
    """Clean and normalize text values."""
    if pd.isna(text) or text is None:
        return ""
    text = str(text).strip()
    return text if text else ""


def process_csv(csv_path: str, output_path: str) -> None:
    """
    Transform CSV into optimized multilingual JSON structure.
    
    Args:
        csv_path: Path to 226Multi_2.csv
        output_path: Path to write models.json
    """
    
    # Read CSV with semicolon delimiter and UTF-8 encoding
    df = pd.read_csv(csv_path, delimiter=';', encoding='utf-8')
    
    print(f"Loaded {len(df)} rows from {csv_path}")
    print(f"Columns: {list(df.columns)}")
    
    # Initialize data structures
    models_by_id: Dict[int, Dict[str, Any]] = defaultdict(
        lambda: {
            "id": None,
            "name": "",
            "descriptions": {},
            "salesAdvice": {},
            "objectionHandling": {},
            "colorVariants": []
        }
    )
    
    languages: set = set()
    color_variants_by_model: Dict[int, Dict[str, Any]] = defaultdict(dict)
    
    # Process each row
    for idx, row in df.iterrows():
        try:
            lingua = clean_text(row.get("Lingua", "")).upper()
            model_id = int(row.get("ID", 0))
            model_name = clean_text(row.get("Nome Modello", ""))
            descrizione = clean_text(row.get("Descrizione", ""))
            colore_nome = clean_text(row.get("Colore Nome", ""))
            colore_codice = clean_text(row.get("Colore Codice", ""))
            colore_url = clean_text(row.get("Colore URL Immagine", ""))
            consigli_vendita = clean_text(row.get("Consigli di Vendita", ""))
            gestione_obiezioni = clean_text(row.get("Gestione Obiezioni", ""))
            
            # Validate key fields
            if not lingua or not model_id or not model_name:
                print(f"⚠️  Skipping row {idx}: missing lingua={lingua}, id={model_id}, name={model_name}")
                continue
            
            languages.add(lingua)
            
            # Populate model base info
            model = models_by_id[model_id]
            model["id"] = model_id
            model["name"] = model_name
            
            # Add multilingual content
            model["descriptions"][lingua] = descrizione
            model["salesAdvice"][lingua] = consigli_vendita
            model["objectionHandling"][lingua] = gestione_obiezioni
            
            # Handle color variants (deduplicate by code per model)
            if colore_codice:
                variant_key = f"{model_id}_{colore_codice}"
                if variant_key not in color_variants_by_model:
                    color_variants_by_model[variant_key] = {
                        "code": colore_codice,
                        "name": {},
                        "imageUrl": colore_url if colore_url else None
                    }
                
                # Add translated color name
                if colore_nome:
                    color_variants_by_model[variant_key]["name"][lingua] = colore_nome
        
        except Exception as e:
            print(f"❌ Error processing row {idx}: {e}")
            continue
    
    # Build final models array with aggregated color variants
    models = []
    for model_id in sorted(models_by_id.keys()):
        model = models_by_id[model_id]
        
        # Aggregate color variants for this model
        color_variants = []
        for variant_key, variant in color_variants_by_model.items():
            if variant_key.startswith(f"{model_id}_"):
                color_variants.append({
                    "name": variant["name"],
                    "code": variant["code"],
                    "imageUrl": variant["imageUrl"]
                })
        
        model["colorVariants"] = color_variants
        models.append(model)
    
    # Sort languages for consistency
    sorted_languages = sorted(languages)
    
    # Create output structure
    output_data = {
        "languages": sorted_languages,
        "models": models
    }
    
    # Write JSON
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Successfully processed and wrote to {output_path}")
    print(f"   Languages: {sorted_languages}")
    print(f"   Models: {len(models)}")
    print(f"   Total color variants: {sum(len(m['colorVariants']) for m in models)}")


if __name__ == "__main__":
    import sys
    
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "226Multi_2.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "src/data/models.json"
    
    process_csv(csv_path, output_path)
