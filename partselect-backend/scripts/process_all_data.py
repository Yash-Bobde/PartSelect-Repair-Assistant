"""
Process both refrigerator and dishwasher data files
Complete standalone script
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import re


class DataProcessor:
    def __init__(self, input_file: str):
        self.input_file = Path(input_file)
        self.data = self._load_data()
        
    def _load_data(self) -> List[Dict]:
        print(f"📂 Loading data from {self.input_file}")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Loaded {len(data)} products")
        return data
    
    def clean_price(self, price_str: str) -> Optional[float]:
        if not price_str or price_str == "N/A":
            return None
        price_cleaned = re.sub(r'[^\d.]', '', str(price_str))
        try:
            return float(price_cleaned)
        except ValueError:
            return None
    
    def parse_category(self, product_types: str) -> str:
        if not product_types:
            return "dishwasher"
        product_types_lower = product_types.lower()
        if "refrigerator" in product_types_lower or "freezer" in product_types_lower:
            return "refrigerator"
        elif "dishwasher" in product_types_lower:
            return "dishwasher"
        else:
            return "dishwasher"
    
    def parse_symptoms(self, symptoms_str: str) -> List[str]:
        if not symptoms_str or symptoms_str == "N/A":
            return []
        symptoms = [s.strip() for s in symptoms_str.split('\n') if s.strip()]
        return symptoms
    
    def parse_replace_parts(self, replace_parts_str: str) -> List[str]:
        if not replace_parts_str or replace_parts_str == "N/A":
            return []
        parts = [p.strip() for p in replace_parts_str.split(',') if p.strip()]
        return parts
    
    def parse_install_difficulty(self, difficulty_str: str) -> Optional[str]:
        if not difficulty_str or difficulty_str == "N/A":
            return "moderate"
        difficulty_lower = str(difficulty_str).lower()
        if "easy" in difficulty_lower or "simple" in difficulty_lower:
            return "easy"
        elif "hard" in difficulty_lower or "difficult" in difficulty_lower:
            return "hard"
        else:
            return "moderate"
    
    def parse_install_time(self, time_str: str) -> Optional[int]:
        if not time_str or time_str == "N/A":
            return 30
        time_lower = str(time_str).lower()
        minutes = re.findall(r'\d+', time_lower)
        if not minutes:
            return 30
        time_value = int(minutes[0])
        if "hour" in time_lower:
            time_value *= 60
        return time_value
    
    def generate_description(self, item: Dict) -> str:
        parts = []
        if item.get("part_name"):
            parts.append(item["part_name"])
        if item.get("symptoms") and item["symptoms"] != "N/A":
            symptoms = self.parse_symptoms(item["symptoms"])
            if symptoms:
                parts.append(f"Fixes: {', '.join(symptoms[:3])}")
        if item.get("brand"):
            parts.append(f"Brand: {item['brand']}")
        if item.get("product_types"):
            parts.append(f"For: {item['product_types']}")
        return ". ".join(parts)
    
    def process_products(self) -> pd.DataFrame:
        print("\n📦 Processing products...")
        products = []
        
        for item in self.data:
            product = {
                "part_number": item.get("part_id"),
                "name": item.get("part_name"),
                "description": self.generate_description(item),
                "category": self.parse_category(item.get("product_types")),
                "brand": item.get("brand"),
                "price": self.clean_price(item.get("part_price")),
                "in_stock": str(item.get("availability", "")).lower() == "in stock",
                "specifications": json.dumps({
                    "mpn": item.get("mpn_id"),
                    "replace_parts": self.parse_replace_parts(item.get("replace_parts", "")),
                    "product_url": item.get("product_url"),
                    "symptoms": self.parse_symptoms(item.get("symptoms", ""))
                }),
                "image_urls": json.dumps([]),
                "rating": None,
                "reviews_count": 0
            }
            products.append(product)
        
        df = pd.DataFrame(products)
        df = df.drop_duplicates(subset=['part_number'], keep='first')
        df = df[df['part_number'].notna()]
        df = df[df['name'].notna()]
        df = df[df['price'].notna()]
        
        print(f"✓ Processed {len(df)} products")
        return df
    
    def process_installation_guides(self) -> pd.DataFrame:
        print("\n🔧 Processing installation guides...")
        guides = []
        
        for item in self.data:
            has_video = item.get("install_video_url") and item["install_video_url"] != "N/A"
            has_difficulty = item.get("install_difficulty") and item["install_difficulty"] != "N/A"
            has_time = item.get("install_time") and item["install_time"] != "N/A"
            
            if has_video or has_difficulty or has_time:
                guide = {
                    "part_number": item.get("part_id"),
                    "difficulty": self.parse_install_difficulty(item.get("install_difficulty")),
                    "estimated_time_minutes": self.parse_install_time(item.get("install_time")),
                    "tools_required": json.dumps(["screwdriver"]),
                    "video_url": item.get("install_video_url") if has_video else None,
                    "pdf_url": None,
                    "chromadb_doc_id": f"install_{item.get('part_id')}"
                }
                guides.append(guide)
        
        df = pd.DataFrame(guides) if guides else pd.DataFrame()
        if len(df) > 0:
            df = df.drop_duplicates(subset=['part_number'], keep='first')
        
        print(f"✓ Processed {len(df)} installation guides")
        return df
    
    def process_troubleshooting_kb(self) -> pd.DataFrame:
        print("\n🔍 Processing troubleshooting knowledge base...")
        symptom_to_parts = {}
        
        for item in self.data:
            symptoms = self.parse_symptoms(item.get("symptoms", ""))
            part_number = item.get("part_id")
            category = self.parse_category(item.get("product_types"))
            brand = item.get("brand")
            
            for symptom in symptoms:
                key = f"{category}:{symptom}"
                
                if key not in symptom_to_parts:
                    symptom_to_parts[key] = {
                        "appliance_type": category,
                        "issue_title": symptom,
                        "symptoms": [symptom],
                        "brands": set(),
                        "parts": []
                    }
                
                if brand:
                    symptom_to_parts[key]["brands"].add(brand)
                symptom_to_parts[key]["parts"].append(part_number)
        
        kb_entries = []
        for key, data in symptom_to_parts.items():
            entry = {
                "appliance_type": data["appliance_type"],
                "brand": ", ".join(sorted(data["brands"])) if data["brands"] else None,
                "issue_title": data["issue_title"],
                "symptoms": json.dumps(data["symptoms"]),
                "possible_causes": json.dumps([]),
                "diagnostic_steps": json.dumps([]),
                "recommended_parts": json.dumps(data["parts"][:10]),
                "chromadb_doc_id": f"troubleshoot_{abs(hash(key)) % 100000}"
            }
            kb_entries.append(entry)
        
        df = pd.DataFrame(kb_entries) if kb_entries else pd.DataFrame()
        print(f"✓ Processed {len(df)} troubleshooting entries")
        return df
    
    def process_chromadb_documents(self) -> pd.DataFrame:
        print("\n📝 Processing ChromaDB documents...")
        documents = []
        
        for item in self.data:
            part_number = item.get("part_id")
            
            # Product document
            product_doc = {
                "doc_id": f"product_{part_number}",
                "doc_type": "product",
                "part_number": part_number,
                "content": self.generate_description(item),
                "metadata": json.dumps({
                    "category": self.parse_category(item.get("product_types")),
                    "brand": item.get("brand"),
                    "price": self.clean_price(item.get("part_price"))
                })
            }
            documents.append(product_doc)
            
            # Installation document
            if item.get("install_video_url") and item["install_video_url"] != "N/A":
                install_doc = {
                    "doc_id": f"install_{part_number}",
                    "doc_type": "installation",
                    "part_number": part_number,
                    "content": f"Installation guide for {item.get('part_name')}. "
                               f"Difficulty: {item.get('install_difficulty', 'moderate')}. "
                               f"Estimated time: {item.get('install_time', '30 minutes')}. "
                               f"Video tutorial available.",
                    "metadata": json.dumps({
                        "category": self.parse_category(item.get("product_types")),
                        "video_url": item.get("install_video_url")
                    })
                }
                documents.append(install_doc)
            
            # Troubleshooting document
            symptoms = self.parse_symptoms(item.get("symptoms", ""))
            if symptoms:
                trouble_doc = {
                    "doc_id": f"troubleshoot_{part_number}",
                    "doc_type": "troubleshooting",
                    "part_number": part_number,
                    "content": f"{item.get('part_name')} is recommended for these issues: {', '.join(symptoms)}. "
                               f"This is a {self.parse_category(item.get('product_types'))} part from {item.get('brand')}.",
                    "metadata": json.dumps({
                        "category": self.parse_category(item.get("product_types")),
                        "symptoms": symptoms
                    })
                }
                documents.append(trouble_doc)
        
        df = pd.DataFrame(documents)
        print(f"✓ Processed {len(df)} ChromaDB documents")
        return df
    
    def process_all(self) -> Dict[str, pd.DataFrame]:
        print("=" * 60)
        print("🚀 Starting Data Processing Pipeline")
        print("=" * 60)
        
        results = {
            "products": self.process_products(),
            "installation_guides": self.process_installation_guides(),
            "troubleshooting_kb": self.process_troubleshooting_kb(),
            "chromadb_documents": self.process_chromadb_documents()
        }
        
        print("\n" + "=" * 60)
        print("✓ Processing Complete!")
        print("=" * 60)
        
        print("\nSummary:")
        for name, df in results.items():
            print(f"  {name}: {len(df)} records")
        
        return results
    
    def save_processed_data(self, output_dir: str = "data/processed"):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = self.process_all()
        
        print("\n💾 Saving processed data...")
        
        for name, df in results.items():
            if len(df) > 0:
                filepath = output_path / f"{name}.csv"
                df.to_csv(filepath, index=False)
                print(f"  ✓ Saved {filepath}")
        
        print("\n🎉 All data saved successfully!")
        print("\nNext: Run 'python scripts/load_to_database.py'")


def main():
    # File paths
    fridge_file = "data/raw/refrigerator_parts.json"
    dishwasher_file = "data/raw/dishwasher_parts.json"
    combined_file = "data/raw/all_parts.json"
    
    # Check files exist
    if not Path(fridge_file).exists():
        print(f"❌ Not found: {fridge_file}")
        return
    
    if not Path(dishwasher_file).exists():
        print(f"❌ Not found: {dishwasher_file}")
        return
    
    print("=" * 60)
    print("🚀 Processing All PartSelect Data")
    print("=" * 60)
    print()
    
    # Combine files
    print(f"📂 Combining data files...")
    data1 = json.load(open(fridge_file, 'r', encoding='utf-8'))
    data2 = json.load(open(dishwasher_file, 'r', encoding='utf-8'))
    
    print(f"  Refrigerator: {len(data1)} items")
    print(f"  Dishwasher: {len(data2)} items")
    
    combined = data1 + data2
    print(f"  Combined: {len(combined)} items")
    
    # Save combined
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2)
    print(f"✓ Saved to {combined_file}\n")
    
    # Process
    processor = DataProcessor(combined_file)
    processor.save_processed_data()


if __name__ == "__main__":
    main()