// Zentrale Übersetzungen. Deutsch ist die Vollversion; alle weiteren Sprachen
// erhalten eine eigenständige Landingpage unter /<lang>/ mit Kontaktweg.
// Erweitern = neuen Eintrag in `landing` + `languages` ergänzen.

export const SUPPORTED_LANGS = ["de", "en", "tr", "nl", "pl", "fr", "es"] as const;
export type Lang = (typeof SUPPORTED_LANGS)[number];

export const languages: { code: Lang; label: string; href: string; title: string }[] = [
  { code: "de", label: "DE", href: "/", title: "Deutsch" },
  { code: "en", label: "EN", href: "/en/", title: "English" },
  { code: "tr", label: "TR", href: "/tr/", title: "Türkçe" },
  { code: "nl", label: "NL", href: "/nl/", title: "Nederlands" },
  { code: "pl", label: "PL", href: "/pl/", title: "Polski" },
  { code: "fr", label: "FR", href: "/fr/", title: "Français" },
  { code: "es", label: "ES", href: "/es/", title: "Español" },
];

export const homeAlternates = languages.map((language) => ({ lang: language.code, path: language.href }));

export const ui: Record<Lang, { skip: string; cookieSettings: string }> = {
  de: { skip: "Zum Inhalt springen", cookieSettings: "Cookie-Einstellungen" },
  en: { skip: "Skip to content", cookieSettings: "Cookie settings" },
  tr: { skip: "İçeriğe atla", cookieSettings: "Çerez ayarları" },
  nl: { skip: "Naar inhoud", cookieSettings: "Cookie-instellingen" },
  pl: { skip: "Przejdź do treści", cookieSettings: "Ustawienia cookies" },
  fr: { skip: "Aller au contenu", cookieSettings: "Paramètres des cookies" },
  es: { skip: "Saltar al contenido", cookieSettings: "Configuración de cookies" },
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
  es: {
    "title": "Cookies y privacidad",
    "intro": "Utilizamos cookies técnicamente necesarias para el funcionamiento del sitio. Las cookies estadísticas solo se activan con su consentimiento. Puede cambiar su elección en «Configuración de cookies», al pie de la página.",
    "acceptAll": "Aceptar todas",
    "necessaryOnly": "Solo necesarias",
    "settings": "Configuración",
    "save": "Guardar selección",
    "necessaryTitle": "Necesarias",
    "necessaryDesc": "Permiten las funciones básicas y guardan su selección de cookies. Siempre activas.",
    "analyticsTitle": "Estadísticas",
    "analyticsDesc": "Nos ayudan a entender el uso del sitio, por ejemplo con Google Analytics. Solo se cargan con su consentimiento.",
    "alwaysOn": "siempre activas",
    "privacyLink": "Política de privacidad (alemán)"
  },
};


export { landing } from "../data/internationalLandings";
export type { LandingContent } from "../data/internationalLandings";
