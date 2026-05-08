import csv
import os
import re

input_file = "knowledge/Libro1.csv"
output_file = "data/CANALES_LISTOS.csv"

if not os.path.exists(input_file):
    print(f"Error: No encuentro {input_file}")
    exit()

with open(input_file, 'r', encoding='utf-8-sig') as infile, \
     open(output_file, 'w', encoding='utf-8', newline='') as outfile:
    
    writer = csv.writer(outfile)
    writer.writerow(["Nombre", "Handle", "URL", "Categoria"])
    
    count = 0
    for line in infile:
        line = line.strip()
        if not line: continue
        
        if " - " in line:
            parts = line.split(" - ", 1)
            handle_raw = parts[0].strip()
            nombre = parts[1].strip()
            
            # Limpiar handle de caracteres invisibles
            handle_clean = re.sub(r'[\u200b-\u200f\u2028-\u202f]', '', handle_raw)
            handle_clean = handle_clean.strip()
            
            if not handle_clean.startswith("@"):
                handle_clean = f"@{handle_clean}"
            
            url = f"https://www.youtube.com/{handle_clean}"
            
            writer.writerow([nombre, handle_clean, url, "General"])
            count += 1

print(f"OK - {count} canales convertidos a '{output_file}'")