import os
from pathlib import Path
import argparse

# TO LAUNCH: python command/module_create.py <module_name>

def create_module(module_name):
    # Définir les sous-dossiers à créer dans le module
    subfolders = ['routers', 'models', 'dto', 'services']

    # Obtenir le chemin du dossier contenant le script actuel
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Construire le chemin vers le dossier du module
    module_path = os.path.join(script_dir, '..', 'src', module_name)

    # Vérifier si le dossier du module existe déjà
    if os.path.exists(module_path):
        print(f"Module {module_name} already exists.")
        return

    # Créer le dossier du module
    os.makedirs(module_path, exist_ok=True)

    # Créer un fichier __init__.py à la racine du module
    Path(os.path.join(module_path, '__init__.py')).touch()

    # Créer chaque sous-dossier et le fichier __init__.py à l'intérieur
    for subfolder in subfolders:
        os.makedirs(os.path.join(module_path, subfolder), exist_ok=True)
        Path(os.path.join(module_path, subfolder, '__init__.py')).touch()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a new module.')
    parser.add_argument('module_name', type=str, help='The name of the module to create')

    args = parser.parse_args()

    create_module(args.module_name)