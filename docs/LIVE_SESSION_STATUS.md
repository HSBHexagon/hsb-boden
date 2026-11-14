# HSB Sales OS - Live Session Status

> **Letzte Aktualisierung:** 2026-11-10T11:15:00Z  
> **Master Sheet ID:** `1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg`  
> **Repository:** `HSBHexagon/hsb-boden`

---

## 1. Heutiger Live-Versandstand (10.11.2026)

* **Joel Cherino Diaz (`j-cherino@hsb-boden.com`):**
  * Versendet heute: **99 E-Mails**
  * Status: Verifiziert im CRM (`ALL_LEADS`) mit UTC-Zeitstempel und Internet-Message-ID
  * Bounces: 1 Hard Bounce sauber erkannt (`PROVIDER_KNOWN_UNKNOWN`)
* **Jordi Post (`j-post@hsb-boden.com`):**
  * Versendet heute: **92 E-Mails**
  * Status: Verifiziert im CRM (`ALL_LEADS`) mit UTC-Zeitstempel und Internet-Message-ID
  * Bounces: 0
* **Gesamt heute zugestellt:** **191 echte Kunden-E-Mails**
* **Erfolgsquote:** **99,5% Zustellungsrate**

---

## 2. Limits & Kapazitäten

* **Neues Tageslimit:** 250 E-Mails pro Postfach (500 E-Mails/Tag gesamt)
* **Bereite Entwürfe im Sheet:**
  * Joel: > 2.700 verifizierte Entwürfe mit `Versandfreigabe = 'yes'`
  * Jordi: > 2.100 verifizierte Entwürfe mit `Versandfreigabe = 'yes'`
* **Sicherheitsjitter:** ~30–35 Sekunden zwischen Sendungen zum Schutz der Domain-Reputation bei Spamhaus / Microsoft / Google.

---

## 3. ChatGPT-Steuerung (OpenAPI Connector)

In ChatGPT (Custom GPT) kann der folgende Endpunkt per Action aufgerufen werden:

* **Endpoint:** `POST https://api.github.com/repos/HSBHexagon/hsb-boden/actions/workflows/sales-os-safety.yml/dispatches`
* **Header:** `Authorization: Bearer <GITHUB_PAT>`
* **Payload:**
  ```json
  {
    "ref": "main",
    "inputs": {
      "mode": "send",
      "count": "100"
    }
  }
  ```
