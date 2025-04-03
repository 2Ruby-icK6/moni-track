import os
import pkg_resources
import re

# Step 1: Read packages from requirements.txt
requirements_file = "requirements/requirements.txt"

if not os.path.exists(requirements_file):
    print(f"Error: {requirements_file} not found.")
    exit()

with open(requirements_file, "r", encoding="utf-8") as file:
    required_packages = [line.strip().split("==")[0] for line in file.readlines() if line.strip()]

# Step 2: Locate Django settings file
project_dir = os.getcwd()  
settings_file = None

# Dynamically find settings.py
for root, dirs, files in os.walk(project_dir):
    if "settings.py" in files:
        settings_file = os.path.join(root, "settings.py")
        break

if not settings_file:
    print("Error: settings.py not found in the project.")
    exit()

# Step 3: Scan Python files for imported modules
imported_modules = set()

for root, _, files in os.walk(project_dir):
    for file in files:
        if file.endswith(".py"):  
            with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    match = re.match(r"(?:from|import) (\w+)", line)
                    if match:
                        imported_modules.add(match.group(1))

# Step 4: Extract INSTALLED_APPS from settings.py (Fixing `__file__` issue)
settings_globals = {"__file__": settings_file}  # Define __file__ manually

with open(settings_file, "r", encoding="utf-8", errors="ignore") as f:
    exec(f.read(), settings_globals)  # Load Django settings safely

if "INSTALLED_APPS" in settings_globals:
    installed_apps = set(settings_globals["INSTALLED_APPS"])
    imported_modules.update(installed_apps)

# Step 5: Handle packages with different import names
package_aliases = {
    "django-import-export": "import_export",
    "django-widget-tweaks": "widget_tweaks",
}

used_packages = []
unused_packages = []

for package in required_packages:
    try:
        distribution = pkg_resources.get_distribution(package)
        package_name = distribution.key  # Get normalized package name
    except pkg_resources.DistributionNotFound:
        unused_packages.append(package)
        continue

    # Check if actual package name or alias exists in imported modules
    if package_name in imported_modules or package_aliases.get(package_name) in imported_modules:
        used_packages.append(package)
    else:
        unused_packages.append(package)

# Step 6: Print the results
print("\n✅ Used Packages (Keep these):")
if used_packages:
    for package in used_packages:
        print(f"- {package}")
else:
    print("None detected.")

print("\n❌ Unused Packages (Consider removing these):")
if unused_packages:
    for package in unused_packages:
        print(f"- {package}")
else:
    print("None detected.")

print("\nTip: Remove unused packages from requirements.txt and re-install dependencies using:")
print("    pip uninstall -r requirements.txt -y && pip freeze > requirements.txt")
