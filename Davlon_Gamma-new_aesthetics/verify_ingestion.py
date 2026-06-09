import asyncio
import os
from backend.csv_service import CsvIngestionService

# Mock Data
VALID_OFFICIAL_CSV = """Any,Codi_districte,Nom_districte,Codi_barri,Nom_barri,Seccio_censal,Desc_tipus_propietari,Concepte,Valor
2025,1,Ciutat Vella,1,el Raval,1,Subjecte físic,Valor_cadastral,40122662.42
2025,1,Ciutat Vella,1,el Raval,2,Subjecte físic,Valor_cadastral,37607885.44
"""

# "Mutant" CSV (English Headers) - Should trigger AI Learning
MUTANT_CSV = """Year,District_ID,District_Name,Nb_Code,Nb_Name,Section,Owner_Type,Concept,Value
2025,1,Ciutat Vella,1,el Raval,1,Person,Cadastral,99999.99
"""

async def test_hybrid_pipeline():
    service = CsvIngestionService()
    
    print("\n--- TEST 1: Official Barcelona CSV (Fast Path) ---")
    # Should work instantly via Pydantic using "Any", "Codi_districte" etc.
    result_official = await service.ingest_csv(VALID_OFFICIAL_CSV, "2025_Carrec_tipus_propietari.csv")
    print(result_official)
    
    if "40122662.42" in result_official:
        print("✅ TEST 1 PASSED: Fast Path extraction correct.")
    else:
        print("❌ TEST 1 FAILED.")

    print("\n--- TEST 2: Mutant CSV (AI Learning Path) ---")
    # Should trigger Gemini to map "District_ID" -> "Codi_districte"
    result_mutant = await service.ingest_csv(MUTANT_CSV, "2025_Carrec_Mutant.csv")
    print(result_mutant)
    
    # We check if it successfully extracted the Value column despite the name change
    if "99999.99" in result_mutant:
        print("✅ TEST 2 PASSED: AI Learning Path extraction correct.")
    else:
        print("❌ TEST 2 FAILED.")

    print("\n--- TEST 3: Stickiness Check ---")
    # Check if mapping file was created
    if os.path.exists("schema_mappings.json"):
        print("✅ TEST 3 PASSED: Schema mapping file created.")
    else:
        print("❌ TEST 3 FAILED: No mapping file found.")

if __name__ == "__main__":
    asyncio.run(test_hybrid_pipeline())
