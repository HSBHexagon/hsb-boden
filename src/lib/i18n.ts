// Zentrale Übersetzungen. Deutsch ist die Vollversion; alle weiteren Sprachen
// erhalten eine eigenständige Landingpage unter /<lang>/ mit Kontaktweg.
// Erweitern = neuen Eintrag in `landing` + `languages` ergänzen.

export const SUPPORTED_LANGS = ["de", "en", "tr", "nl", "pl", "fr"] as const;
export type Lang = (typeof SUPPORTED_LANGS)[number];

export const languages: { code: Lang; label: string; href: string; title: string }[] = [
  { code: "de", label: "DE", href: "/", title: "Deutsch" },
  { code: "en", label: "EN", href: "/en/", title: "English" },
  { code: "tr", label: "TR", href: "/tr/", title: "Türkçe" },
  { code: "nl", label: "NL", href: "/nl/", title: "Nederlands" },
  { code: "pl", label: "PL", href: "/pl/", title: "Polski" },
  { code: "fr", label: "FR", href: "/fr/", title: "Français" },
];

export const homeAlternates = languages.map((language) => ({ lang: language.code, path: language.href }));

export const ui: Record<Lang, { skip: string; cookieSettings: string }> = {
  de: { skip: "Zum Inhalt springen", cookieSettings: "Cookie-Einstellungen" },
  en: { skip: "Skip to content", cookieSettings: "Cookie settings" },
  tr: { skip: "İçeriğe atla", cookieSettings: "Çerez ayarları" },
  nl: { skip: "Naar inhoud", cookieSettings: "Cookie-instellingen" },
  pl: { skip: "Przejdź do treści", cookieSettings: "Ustawienia cookies" },
  fr: { skip: "Aller au contenu", cookieSettings: "Paramètres des cookies" },
};

export interface CookieTexts {
  title: string;
  intro: string;
  acceptAll: string;
  necessaryOnly: string;
  settings: string;
  save: string;
  necessaryTitle: string;
  necessaryDesc: string;
  analyticsTitle: string;
  analyticsDesc: string;
  alwaysOn: string;
  privacyLink: string;
}

export const cookieTexts: Record<Lang, CookieTexts> = {
  de: {
    title: "Cookies & Datenschutz",
    intro:
      "Wir verwenden technisch notwendige Cookies für den Betrieb der Seite. Statistik-Cookies setzen wir nur, wenn Sie zustimmen – Sie können Ihre Auswahl jederzeit über „Cookie-Einstellungen“ im Footer ändern.",
    acceptAll: "Alle akzeptieren",
    necessaryOnly: "Nur notwendige",
    settings: "Einstellungen",
    save: "Auswahl speichern",
    necessaryTitle: "Notwendig",
    necessaryDesc: "Erforderlich für Grundfunktionen wie das Kontaktformular und das Speichern dieser Cookie-Auswahl. Immer aktiv.",
    analyticsTitle: "Statistik",
    analyticsDesc: "Hilft uns zu verstehen, wie die Seite genutzt wird (z. B. Google Analytics). Wird erst nach Ihrer Zustimmung geladen.",
    alwaysOn: "immer aktiv",
    privacyLink: "Datenschutzerklärung",
  },
  en: {
    title: "Cookies & privacy",
    intro:
      "We use technically necessary cookies to run this site. Statistics cookies are only set with your consent – you can change your choice at any time via “Cookie settings” in the footer.",
    acceptAll: "Accept all",
    necessaryOnly: "Necessary only",
    settings: "Settings",
    save: "Save selection",
    necessaryTitle: "Necessary",
    necessaryDesc: "Required for core functions such as the contact form and storing this cookie choice. Always active.",
    analyticsTitle: "Statistics",
    analyticsDesc: "Helps us understand how the site is used (e.g. Google Analytics). Only loaded after your consent.",
    alwaysOn: "always active",
    privacyLink: "Privacy policy",
  },
  tr: {
    title: "Çerezler ve gizlilik",
    intro:
      "Bu siteyi çalıştırmak için teknik olarak gerekli çerezler kullanıyoruz. İstatistik çerezleri yalnızca onayınızla etkinleştirilir – seçiminizi alt bilgideki “Çerez ayarları” üzerinden istediğiniz zaman değiştirebilirsiniz.",
    acceptAll: "Tümünü kabul et",
    necessaryOnly: "Yalnızca gerekli",
    settings: "Ayarlar",
    save: "Seçimi kaydet",
    necessaryTitle: "Gerekli",
    necessaryDesc: "İletişim formu ve bu çerez seçiminin saklanması gibi temel işlevler için gereklidir. Her zaman etkin.",
    analyticsTitle: "İstatistik",
    analyticsDesc: "Sitenin nasıl kullanıldığını anlamamıza yardımcı olur (ör. Google Analytics). Yalnızca onayınızdan sonra yüklenir.",
    alwaysOn: "her zaman etkin",
    privacyLink: "Gizlilik politikası",
  },
  nl: {
    title: "Cookies & privacy",
    intro:
      "Wij gebruiken technisch noodzakelijke cookies voor het functioneren van deze site. Statistiekcookies plaatsen we alleen met uw toestemming – u kunt uw keuze altijd wijzigen via “Cookie-instellingen” in de footer.",
    acceptAll: "Alles accepteren",
    necessaryOnly: "Alleen noodzakelijke",
    settings: "Instellingen",
    save: "Keuze opslaan",
    necessaryTitle: "Noodzakelijk",
    necessaryDesc: "Vereist voor basisfuncties zoals het contactformulier en het opslaan van deze cookiekeuze. Altijd actief.",
    analyticsTitle: "Statistieken",
    analyticsDesc: "Helpt ons te begrijpen hoe de site wordt gebruikt (bijv. Google Analytics). Wordt pas na uw toestemming geladen.",
    alwaysOn: "altijd actief",
    privacyLink: "Privacyverklaring",
  },
  pl: {
    title: "Pliki cookie i prywatność",
    intro:
      "Używamy technicznie niezbędnych plików cookie do działania strony. Cookies statystyczne ustawiamy tylko za Twoją zgodą – wybór możesz zmienić w każdej chwili w „Ustawieniach cookies” w stopce.",
    acceptAll: "Zaakceptuj wszystkie",
    necessaryOnly: "Tylko niezbędne",
    settings: "Ustawienia",
    save: "Zapisz wybór",
    necessaryTitle: "Niezbędne",
    necessaryDesc: "Wymagane do podstawowych funkcji, takich jak formularz kontaktowy i zapisanie tego wyboru. Zawsze aktywne.",
    analyticsTitle: "Statystyka",
    analyticsDesc: "Pomaga nam zrozumieć, jak strona jest używana (np. Google Analytics). Ładowane dopiero po Twojej zgodzie.",
    alwaysOn: "zawsze aktywne",
    privacyLink: "Polityka prywatności",
  },
  fr: {
    title: "Cookies & confidentialité",
    intro:
      "Nous utilisons des cookies techniquement nécessaires au fonctionnement du site. Les cookies statistiques ne sont déposés qu'avec votre consentement – vous pouvez modifier votre choix à tout moment via « Paramètres des cookies » en bas de page.",
    acceptAll: "Tout accepter",
    necessaryOnly: "Nécessaires uniquement",
    settings: "Paramètres",
    save: "Enregistrer le choix",
    necessaryTitle: "Nécessaires",
    necessaryDesc: "Requis pour les fonctions de base comme le formulaire de contact et l'enregistrement de ce choix. Toujours actifs.",
    analyticsTitle: "Statistiques",
    analyticsDesc: "Nous aide à comprendre l'utilisation du site (p. ex. Google Analytics). Chargés uniquement après votre consentement.",
    alwaysOn: "toujours actifs",
    privacyLink: "Politique de confidentialité",
  },
};

export interface LandingContent {
  meta: { seoTitle: string; description: string };
  hero: { eyebrow: string; h1: string; text: string; ctaContact: string; ctaGerman: string };
  systems: { title: string; intro: string; items: { title: string; text: string }[] };
  industries: { title: string; intro: string; items: string[] };
  reference: { title: string; name: string; text: string };
  process: { title: string; steps: { title: string; text: string }[] };
  contact: { title: string; text: string; phoneLabel: string; emailLabel: string; languagesNote: string };
  germanNote: string;
}

export const landing: Record<Exclude<Lang, "de">, LandingContent> = {
  en: {
    meta: {
      seoTitle: "Industrial Flooring & Acid Protection from Germany | HSB",
      description:
        "HSB Hexagon Säurebau: ceramic industrial flooring, acid protection, PU concrete, drainage and floor refurbishment for food, beverage, pharma and chemical production. Based in Gronau, Germany.",
    },
    hero: {
      eyebrow: "HSB Hexagon Säurebau · Gronau, Germany",
      h1: "Industrial flooring and acid protection for production-critical areas",
      text: "We plan and execute floor systems that withstand acids, hot water, cleaning chemistry and heavy traffic – engineered in Germany for food, beverage, pharmaceutical and chemical production.",
      ctaContact: "Request a project assessment",
      ctaGerman: "Visit the German site",
    },
    systems: {
      title: "Floor systems",
      intro: "Every recommendation starts from your load profile – chemical, thermal and mechanical – not from a catalogue.",
      items: [
        { title: "Acid protection systems", text: "Chemical-resistant linings and joint details for aggressive media." },
        { title: "Ceramic industrial flooring", text: "Vitrified tile systems for maximum durability and hygienic cleaning." },
        { title: "PU concrete flooring", text: "Polyurethane cement for thermal shock and wet production zones." },
        { title: "Epoxy floor coatings", text: "Seamless, cleanable surfaces for dry and light-wet areas." },
        { title: "Drainage & slope design", text: "Gullies, channels and falls planned as part of the floor system." },
        { title: "WHG-compliant sealing", text: "Certified containment sealing under German water protection law." },
        { title: "Refurbishment during production", text: "Section-by-section renovation aligned with your production windows." },
      ],
    },
    industries: {
      title: "Industries",
      intro: "Production environments we engineer floors for:",
      items: ["Food industry", "Dairies", "Breweries & beverages", "Chemical industry", "Pharmaceutical industry", "Bakery & commercial kitchens"],
    },
    reference: {
      title: "Approved reference",
      name: "Südzucker AG",
      text: "Refurbishment and detail engineering at a sugar production site in Saxony-Anhalt: acid protection system with durable joint and connection details for chemically loaded production areas.",
    },
    process: {
      title: "How we work",
      steps: [
        { title: "Assessment", text: "Analysis of the existing floor, loads and cleaning regime." },
        { title: "System selection", text: "Ceramic, PU concrete or epoxy – decided by load profile and budget." },
        { title: "Execution", text: "Documented installation including joints, drainage and connections." },
        { title: "Handover", text: "Clear maintenance logic and documentation for your operations team." },
      ],
    },
    contact: {
      title: "Contact",
      text: "Tell us about your production area – we will respond with a technical first assessment.",
      phoneLabel: "Phone",
      emailLabel: "Email",
      languagesNote: "We respond in English and German.",
    },
    germanNote: "Detailed technical pages are currently available in German.",
  },
  tr: {
    meta: {
      seoTitle: "Endüstriyel Zemin ve Asit Koruma Sistemleri | HSB Almanya",
      description:
        "HSB Hexagon Säurebau: gıda, içecek, ilaç ve kimya üretimi için seramik endüstriyel zeminler, asit koruması, PU-beton, drenaj ve zemin yenileme. Merkez: Gronau, Almanya.",
    },
    hero: {
      eyebrow: "HSB Hexagon Säurebau · Gronau, Almanya",
      h1: "Üretim alanları için endüstriyel zemin ve asit koruma sistemleri",
      text: "Asitlere, sıcak suya, temizlik kimyasallarına ve ağır trafiğe dayanıklı zemin sistemleri planlıyor ve uyguluyoruz – gıda, içecek, ilaç ve kimya üretimi için Alman mühendisliği.",
      ctaContact: "Proje değerlendirmesi isteyin",
      ctaGerman: "Almanca siteye git",
    },
    systems: {
      title: "Zemin sistemleri",
      intro: "Her öneri kataloğdan değil, yük profilinizden (kimyasal, termal, mekanik) yola çıkar.",
      items: [
        { title: "Asit koruma sistemleri", text: "Agresif kimyasallara dayanıklı kaplamalar ve derz detayları." },
        { title: "Seramik endüstriyel zeminler", text: "Maksimum dayanıklılık ve hijyenik temizlik için seramik sistemler." },
        { title: "PU-beton zeminler", text: "Termal şok ve ıslak üretim alanları için poliüretan çimento." },
        { title: "Epoksi zemin kaplamaları", text: "Kuru ve az ıslak alanlar için derzsiz, temizlenebilir yüzeyler." },
        { title: "Drenaj ve eğim planlaması", text: "Izgaralar, kanallar ve eğimler zemin sisteminin parçası olarak planlanır." },
        { title: "WHG uyumlu yalıtım", text: "Alman su koruma mevzuatına uygun sertifikalı yalıtım." },
        { title: "Üretim sürerken yenileme", text: "Üretim pencerelerinize göre bölüm bölüm zemin yenileme." },
      ],
    },
    industries: {
      title: "Sektörler",
      intro: "Zemin sistemleri tasarladığımız üretim ortamları:",
      items: ["Gıda endüstrisi", "Süt işleme tesisleri", "Bira ve içecek üretimi", "Kimya endüstrisi", "İlaç endüstrisi", "Unlu mamuller ve endüstriyel mutfaklar"],
    },
    reference: {
      title: "Onaylı referans",
      name: "Südzucker AG",
      text: "Saksonya-Anhalt'taki bir şeker üretim tesisinde yenileme ve detay mühendisliği: kimyasal yüke maruz üretim alanları için dayanıklı derz ve bağlantı detaylarına sahip asit koruma sistemi.",
    },
    process: {
      title: "Çalışma şeklimiz",
      steps: [
        { title: "Değerlendirme", text: "Mevcut zeminin, yüklerin ve temizlik rejiminin analizi." },
        { title: "Sistem seçimi", text: "Seramik, PU-beton veya epoksi – yük profili ve bütçeye göre." },
        { title: "Uygulama", text: "Derzler, drenaj ve bağlantılar dahil belgelenmiş montaj." },
        { title: "Teslim", text: "İşletme ekibiniz için net bakım mantığı ve dokümantasyon." },
      ],
    },
    contact: {
      title: "İletişim",
      text: "Üretim alanınızı bize anlatın – teknik bir ön değerlendirme ile dönüş yapalım.",
      phoneLabel: "Telefon",
      emailLabel: "E-posta",
      languagesNote: "İngilizce ve Almanca yanıt veriyoruz.",
    },
    germanNote: "Ayrıntılı teknik sayfalar şu anda Almanca olarak mevcuttur.",
  },
  nl: {
    meta: {
      seoTitle: "Industrievloeren & Zuurbescherming uit Duitsland | HSB",
      description:
        "HSB Hexagon Säurebau: keramische industrievloeren, zuurbescherming, PU-beton, afwatering en vloerrenovatie voor voedings-, dranken-, farma- en chemische productie. Gevestigd in Gronau, direct aan de Nederlandse grens.",
    },
    hero: {
      eyebrow: "HSB Hexagon Säurebau · Gronau, direct aan de grens",
      h1: "Industrievloeren en zuurbescherming voor productiekritische ruimtes",
      text: "Wij plannen en realiseren vloersystemen die bestand zijn tegen zuren, heet water, reinigingschemie en zwaar verkeer – Duitse engineering voor voedings-, dranken-, farma- en chemieproductie.",
      ctaContact: "Projectbeoordeling aanvragen",
      ctaGerman: "Naar de Duitse site",
    },
    systems: {
      title: "Vloersystemen",
      intro: "Elke aanbeveling vertrekt vanuit uw belastingsprofiel – chemisch, thermisch en mechanisch – niet vanuit een catalogus.",
      items: [
        { title: "Zuurbeschermingssystemen", text: "Chemisch resistente bekledingen en voegdetails voor agressieve media." },
        { title: "Keramische industrievloeren", text: "Keramische systemen voor maximale duurzaamheid en hygiënische reiniging." },
        { title: "PU-betonvloeren", text: "Polyurethaancement voor thermische schokken en natte productiezones." },
        { title: "Epoxy vloercoatings", text: "Naadloze, goed reinigbare oppervlakken voor droge en licht-natte zones." },
        { title: "Afwatering & afschot", text: "Putten, goten en afschot gepland als onderdeel van het vloersysteem." },
        { title: "WHG-conforme afdichting", text: "Gecertificeerde afdichting volgens de Duitse waterbeschermingswet." },
        { title: "Renovatie tijdens productie", text: "Vloerrenovatie in bouwfasen, afgestemd op uw productievensters." },
      ],
    },
    industries: {
      title: "Branches",
      intro: "Productieomgevingen waarvoor wij vloeren engineeren:",
      items: ["Voedingsindustrie", "Zuivelbedrijven", "Brouwerijen & drankenindustrie", "Chemische industrie", "Farmaceutische industrie", "Bakkerijen & grootkeukens"],
    },
    reference: {
      title: "Vrijgegeven referentie",
      name: "Südzucker AG",
      text: "Renovatie en detailengineering op een suikerproductielocatie in Saksen-Anhalt: zuurbeschermingssysteem met duurzame voeg- en aansluitdetails voor chemisch belaste productiezones.",
    },
    process: {
      title: "Onze werkwijze",
      steps: [
        { title: "Beoordeling", text: "Analyse van de bestaande vloer, belastingen en het reinigingsregime." },
        { title: "Systeemkeuze", text: "Keramiek, PU-beton of epoxy – bepaald door belastingsprofiel en budget." },
        { title: "Uitvoering", text: "Gedocumenteerde installatie inclusief voegen, afwatering en aansluitingen." },
        { title: "Oplevering", text: "Heldere onderhoudslogica en documentatie voor uw operationele team." },
      ],
    },
    contact: {
      title: "Contact",
      text: "Vertel ons over uw productieruimte – wij reageren met een technische eerste beoordeling.",
      phoneLabel: "Telefoon",
      emailLabel: "E-mail",
      languagesNote: "Wij reageren in het Nederlands, Engels en Duits.",
    },
    germanNote: "Gedetailleerde technische pagina's zijn momenteel beschikbaar in het Duits.",
  },
  pl: {
    meta: {
      seoTitle: "Posadzki Przemysłowe i Ochrona Kwasoodporna | HSB Niemcy",
      description:
        "HSB Hexagon Säurebau: ceramiczne posadzki przemysłowe, ochrona kwasoodporna, PU-beton, odwodnienia i renowacja posadzek dla produkcji spożywczej, napojów, farmacji i chemii. Siedziba: Gronau, Niemcy.",
    },
    hero: {
      eyebrow: "HSB Hexagon Säurebau · Gronau, Niemcy",
      h1: "Posadzki przemysłowe i ochrona kwasoodporna dla stref produkcyjnych",
      text: "Projektujemy i wykonujemy systemy posadzek odporne na kwasy, gorącą wodę, chemię czyszczącą i duży ruch – niemiecka inżynieria dla produkcji spożywczej, napojów, farmaceutycznej i chemicznej.",
      ctaContact: "Poproś o ocenę projektu",
      ctaGerman: "Przejdź do strony niemieckiej",
    },
    systems: {
      title: "Systemy posadzek",
      intro: "Każda rekomendacja wychodzi od Twojego profilu obciążeń – chemicznych, termicznych i mechanicznych – a nie z katalogu.",
      items: [
        { title: "Systemy ochrony kwasoodpornej", text: "Wykładziny i detale dylatacji odporne na agresywne media." },
        { title: "Ceramiczne posadzki przemysłowe", text: "Systemy ceramiczne o maksymalnej trwałości i higienicznym czyszczeniu." },
        { title: "Posadzki z PU-betonu", text: "Cement poliuretanowy do szoków termicznych i mokrych stref produkcji." },
        { title: "Powłoki epoksydowe", text: "Bezspoinowe, łatwe w czyszczeniu powierzchnie do stref suchych i lekko mokrych." },
        { title: "Odwodnienia i spadki", text: "Wpusty, kanały i spadki planowane jako część systemu posadzki." },
        { title: "Uszczelnienia zgodne z WHG", text: "Certyfikowane uszczelnienia według niemieckiego prawa wodnego." },
        { title: "Renowacja podczas produkcji", text: "Renowacja etapami, dopasowana do okien produkcyjnych zakładu." },
      ],
    },
    industries: {
      title: "Branże",
      intro: "Środowiska produkcyjne, dla których projektujemy posadzki:",
      items: ["Przemysł spożywczy", "Mleczarnie", "Browary i przemysł napojowy", "Przemysł chemiczny", "Przemysł farmaceutyczny", "Piekarnie i kuchnie przemysłowe"],
    },
    reference: {
      title: "Referencja z autoryzacją",
      name: "Südzucker AG",
      text: "Renowacja i inżynieria detali w zakładzie produkcji cukru w Saksonii-Anhalt: system ochrony kwasoodpornej z trwałymi detalami dylatacji i połączeń dla stref obciążonych chemicznie.",
    },
    process: {
      title: "Jak pracujemy",
      steps: [
        { title: "Ocena", text: "Analiza istniejącej posadzki, obciążeń i reżimu czyszczenia." },
        { title: "Dobór systemu", text: "Ceramika, PU-beton lub epoksyd – według profilu obciążeń i budżetu." },
        { title: "Wykonanie", text: "Udokumentowany montaż wraz z dylatacjami, odwodnieniem i połączeniami." },
        { title: "Przekazanie", text: "Czytelna logika konserwacji i dokumentacja dla zespołu utrzymania ruchu." },
      ],
    },
    contact: {
      title: "Kontakt",
      text: "Opisz nam swoją strefę produkcyjną – odpowiemy techniczną oceną wstępną.",
      phoneLabel: "Telefon",
      emailLabel: "E-mail",
      languagesNote: "Odpowiadamy po angielsku i niemiecku.",
    },
    germanNote: "Szczegółowe strony techniczne są obecnie dostępne w języku niemieckim.",
  },
  fr: {
    meta: {
      seoTitle: "Sols Industriels & Protection Anti-Acide | HSB Allemagne",
      description:
        "HSB Hexagon Säurebau : sols industriels céramiques, protection anti-acide, béton PU, drainage et rénovation de sols pour la production agroalimentaire, boissons, pharmaceutique et chimique. Siège : Gronau, Allemagne.",
    },
    hero: {
      eyebrow: "HSB Hexagon Säurebau · Gronau, Allemagne",
      h1: "Sols industriels et protection anti-acide pour zones de production critiques",
      text: "Nous concevons et réalisons des systèmes de sols résistants aux acides, à l'eau chaude, à la chimie de nettoyage et au trafic intense – ingénierie allemande pour la production agroalimentaire, boissons, pharmaceutique et chimique.",
      ctaContact: "Demander une évaluation de projet",
      ctaGerman: "Voir le site allemand",
    },
    systems: {
      title: "Systèmes de sols",
      intro: "Chaque recommandation part de votre profil de charges – chimiques, thermiques et mécaniques – pas d'un catalogue.",
      items: [
        { title: "Systèmes de protection anti-acide", text: "Revêtements et détails de joints résistants aux milieux agressifs." },
        { title: "Sols industriels céramiques", text: "Systèmes céramiques pour une durabilité maximale et un nettoyage hygiénique." },
        { title: "Sols en béton PU", text: "Ciment polyuréthane pour chocs thermiques et zones de production humides." },
        { title: "Revêtements époxy", text: "Surfaces sans joints, faciles à nettoyer, pour zones sèches et peu humides." },
        { title: "Drainage et pentes", text: "Siphons, caniveaux et pentes planifiés comme partie du système de sol." },
        { title: "Étanchéité conforme WHG", text: "Étanchéité certifiée selon la loi allemande sur la protection des eaux." },
        { title: "Rénovation en cours de production", text: "Rénovation par sections, alignée sur vos fenêtres de production." },
      ],
    },
    industries: {
      title: "Secteurs",
      intro: "Environnements de production pour lesquels nous concevons des sols :",
      items: ["Industrie agroalimentaire", "Laiteries", "Brasseries & boissons", "Industrie chimique", "Industrie pharmaceutique", "Boulangerie & cuisines collectives"],
    },
    reference: {
      title: "Référence autorisée",
      name: "Südzucker AG",
      text: "Rénovation et ingénierie de détails sur un site de production de sucre en Saxe-Anhalt : système de protection anti-acide avec détails de joints et de raccordements durables pour zones chimiquement sollicitées.",
    },
    process: {
      title: "Notre méthode",
      steps: [
        { title: "Évaluation", text: "Analyse du sol existant, des charges et du régime de nettoyage." },
        { title: "Choix du système", text: "Céramique, béton PU ou époxy – selon le profil de charges et le budget." },
        { title: "Exécution", text: "Pose documentée, joints, drainage et raccordements inclus." },
        { title: "Livraison", text: "Logique de maintenance claire et documentation pour votre équipe d'exploitation." },
      ],
    },
    contact: {
      title: "Contact",
      text: "Décrivez-nous votre zone de production – nous répondrons par une première évaluation technique.",
      phoneLabel: "Téléphone",
      emailLabel: "E-mail",
      languagesNote: "Nous répondons en anglais et en allemand.",
    },
    germanNote: "Les pages techniques détaillées sont actuellement disponibles en allemand.",
  },
};
