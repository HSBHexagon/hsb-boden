"""
engine/drive_ecosystem_config.py
Canonical Project Mapping and Scaffolding Specifications for Google Drive & GitHub.
"""

from typing import Any, Dict, Optional

PROJECT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "HSB-Boden": {
        "display_name": "HSB Hexagon Säurebau GmbH (HSB-Boden)",
        "folder_name": "HSB-Boden",
        "parent_hint": "root",
        "github_repos": [
            "https://github.com/HSBHexagon/hsb-boden",
            "https://github.com/HSBHexagon/hsb-sales-os",
        ],
        "local_paths": [
            "/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-boden",
            "/Users/joelcherinodiaz/KI-System/02_Projects/active/hsb-sales-os",
        ],
        "subfolders": [
            "01_Website_Cloudflare",
            "02_Sales_OS_CRM",
            "03_Brand_Assets",
            "04_Handoff_Audits",
            "05_Archiv",
        ],
        "description": "Ganzheitlicher Hub: Astro/React Webseite auf Cloudflare Pages & Sales OS CRM",
    },
    "Automobile_Quick": {
        "display_name": "Automobile Quick (auto-hub)",
        "folder_name": "Automobile_Quick",
        "parent_hint": "root",
        "github_repos": [
            "https://github.com/cherinojoel-lang/auto-hub",
            "https://github.com/cherinojoel-lang/auto-hub1",
        ],
        "local_paths": [
            "/Users/joelcherinodiaz/KI-System/02_Projects/active/auto-hub",
        ],
        "subfolders": [
            "01_Handoff_Audits",
            "02_Spezifikationen_Plaene",
            "03_Assets_Medien",
            "04_Exporte_Batches",
            "05_Archiv",
        ],
        "description": "Wix Remote Machine Hub – Fahrzeugbestand, VDP & LCP Web Vitals Hardening",
    },
    "HeadBlade_Germany": {
        "display_name": "HeadBlade Germany Commerce",
        "folder_name": "HeadBlade_Germany",
        "parent_hint": "root",
        "github_repos": [
            "https://github.com/cherinojoel-lang/headblade-germany-commerce",
        ],
        "local_paths": [
            "/Users/joelcherinodiaz/KI-System/02_Projects/active/headblade-germany-commerce",
        ],
        "subfolders": [
            "01_Handoff_Audits",
            "02_Spezifikationen_Plaene",
            "03_Assets_Medien",
            "04_Exporte_Batches",
            "05_Archiv",
        ],
        "description": "E-Commerce Shopware Plattform, Produktkatalog & Growth Audit",
    },
    "Energievergleich_NRW": {
        "display_name": "Energievergleich NRW",
        "folder_name": "Energievergleich_NRW",
        "parent_hint": "04_PROJEKTE",
        "github_repos": [
            "https://github.com/cherinojoel-lang/energievergleichnrwnew",
        ],
        "local_paths": [
            "/Users/joelcherinodiaz/KI-System/02_Projects/active/energievergleich-nrw",
        ],
        "subfolders": [
            "01_Handoff_Audits",
            "02_Spezifikationen_Plaene",
            "03_Assets_Medien",
            "04_Exporte_Batches",
            "05_Archiv",
        ],
        "description": "Tarifvergleichs- und Lead-Generierungs-Portal für NRW",
    },
    "KI_System_Platform": {
        "display_name": "KI-System Automation Platform",
        "folder_name": "01_KI_SYSTEM",
        "parent_hint": "04_PROJEKTE",
        "github_repos": [
            "https://github.com/cherinojoel-lang/n8n-ki-os",
            "https://github.com/cherinojoel-lang/notion-platform",
        ],
        "local_paths": [
            "/Users/joelcherinodiaz/KI-System/01_Platform",
        ],
        "subfolders": [
            "01_Handoff_Audits",
            "02_Spezifikationen_Plaene",
            "03_Assets_Medien",
            "04_Exporte_Batches",
            "05_Archiv",
        ],
        "description": "Zentrale n8n Control Plane, Notion Automation & Multi-Agent Governance",
    },
    "Ebay": {
        "display_name": "Ebay Operations",
        "folder_name": "Ebay",
        "parent_hint": "root",
        "github_repos": [],
        "local_paths": [],
        "subfolders": [
            "01_Handoff_Audits",
            "02_Spezifikationen_Plaene",
            "03_Assets_Medien",
            "04_Exporte_Batches",
            "05_Archiv",
        ],
        "description": "Ebay Account Operations, Listing Batches & Retouren-Management",
    },
}


def get_project_spec(key: str) -> Optional[Dict[str, Any]]:
    return PROJECT_DEFINITIONS.get(key)
