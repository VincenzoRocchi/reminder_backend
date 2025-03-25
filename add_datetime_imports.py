"""
Script per aggiungere l'importazione 'import datetime' a tutti i file Python in app/api/endpoints/.
"""
import os
import re

def add_datetime_import(directory):
    """Aggiunge l'importazione datetime a tutti i file Python nella directory specificata."""
    files_updated = 0
    
    for filename in os.listdir(directory):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(directory, filename)
            
            # Leggi il contenuto del file
            with open(file_path, 'r') as file:
                content = file.read()
            
            # Verifica se datetime è già importato
            if 'import datetime' not in content and 'from datetime import' not in content:
                # Trova la prima importazione e aggiungi datetime dopo
                import_pattern = r'(import [^\n]+)'
                match = re.search(import_pattern, content)
                
                if match:
                    # Aggiungi l'importazione dopo la prima importazione trovata
                    position = match.end()
                    new_content = content[:position] + '\nimport datetime' + content[position:]
                else:
                    # Se non trova importazioni, aggiungi all'inizio del file
                    new_content = 'import datetime\n\n' + content
                
                # Scrivi il contenuto aggiornato
                with open(file_path, 'w') as file:
                    file.write(new_content)
                    
                print(f"Aggiunta importazione datetime a {filename}")
                files_updated += 1
    
    return files_updated

if __name__ == "__main__":
    endpoints_dir = os.path.join('app', 'api', 'endpoints')
    models_dir = os.path.join('app', 'models')
    
    print(f"Aggiunta importazione datetime ai file in {endpoints_dir}")
    endpoints_updated = add_datetime_import(endpoints_dir)
    
    print(f"Aggiunta importazione datetime ai file in {models_dir}")
    models_updated = add_datetime_import(models_dir)
    
    print(f"\nAggiornati {endpoints_updated} file endpoint e {models_updated} file modello.")