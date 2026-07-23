export type Language = 'pt' | 'en' | 'fr' | 'it' | 'es' | 'pl';

export interface Translations {
  greetingMorning: string;
  greetingAfternoon: string;
  greetingEvening: string;
  greetingQuestion: string;
  fatherTitle: string;
  brotherTitle: string;
  researcherTitle: string;
  homeTitle: string;
  homeSubtitle1: string;
  homeSubtitle2: string;
  suggestionsLabel: string;
  shuffleBtn: string;
  inputPlaceholder: string;
  sendBtn: string;
  newChatBtn: string;
  historyTitle: string;
  profileTitle: string;
  logoutBtn: string;
  copyBtn: string;
  copiedBtn: string;
  shareBtn: string;
  sharedBtn: string;
  referencesBtn: string;
  exportABNT: string;
  relatedQuestionsLabel: string;
  footerDeveloper: string;
  languageSelectLabel: string;
}

export const translations: Record<Language, Translations> = {
  pt: {
    greetingMorning: 'Bom dia',
    greetingAfternoon: 'Boa tarde',
    greetingEvening: 'Boa noite',
    greetingQuestion: 'Como posso ajudar em sua pesquisa hoje?',
    fatherTitle: 'Padre',
    brotherTitle: 'Fr.',
    researcherTitle: 'Pesquisador',
    homeTitle: 'Biblioteca Dehoniana',
    homeSubtitle1: 'Para <strong>tempos novos, obras novas</strong>.',
    homeSubtitle2: 'A inteligência a serviço <strong>do Coração</strong>.',
    suggestionsLabel: 'Sugestões de Pesquisa',
    shuffleBtn: 'Girar 🎲',
    inputPlaceholder: 'Pergunte sobre a vida, cartas ou teologia de Padre Dehon...',
    sendBtn: 'Enviar mensagem',
    newChatBtn: 'Nova Pesquisa',
    historyTitle: 'Histórico de Pesquisas',
    profileTitle: 'Perfil & Definições',
    logoutBtn: 'Sair da Sessão',
    copyBtn: 'Copiar',
    copiedBtn: 'Copiado!',
    shareBtn: 'Partilhar',
    sharedBtn: 'Link Copiado!',
    referencesBtn: 'Referências',
    exportABNT: 'Exportar (.ris + ABNT)',
    relatedQuestionsLabel: 'Perguntas Relacionadas',
    footerDeveloper: 'Sistema de Alta Pesquisa desenvolvido por',
    languageSelectLabel: 'Idioma da Interface',
  },
  en: {
    greetingMorning: 'Good morning',
    greetingAfternoon: 'Good afternoon',
    greetingEvening: 'Good evening',
    greetingQuestion: 'How can I assist your research today?',
    fatherTitle: 'Father',
    brotherTitle: 'Br.',
    researcherTitle: 'Researcher',
    homeTitle: 'Dehonian Library',
    homeSubtitle1: 'For <strong>new times, new works</strong>.',
    homeSubtitle2: 'Intelligence at the service <strong>of the Heart</strong>.',
    suggestionsLabel: 'Research Suggestions',
    shuffleBtn: 'Shuffle 🎲',
    inputPlaceholder: 'Ask about Father Dehon\'s life, letters, or theology...',
    sendBtn: 'Send message',
    newChatBtn: 'New Research',
    historyTitle: 'Research History',
    profileTitle: 'Profile & Settings',
    logoutBtn: 'Sign Out',
    copyBtn: 'Copy',
    copiedBtn: 'Copied!',
    shareBtn: 'Share',
    sharedBtn: 'Link Copied!',
    referencesBtn: 'References',
    exportABNT: 'Export (.ris + ABNT)',
    relatedQuestionsLabel: 'Related Questions',
    footerDeveloper: 'Advanced Research System developed by',
    languageSelectLabel: 'Interface Language',
  },
  fr: {
    greetingMorning: 'Bonjour',
    greetingAfternoon: 'Bonjour',
    greetingEvening: 'Bonsoir',
    greetingQuestion: 'Comment puis-je vous aider dans votre recherche aujourd\'hui?',
    fatherTitle: 'Père',
    brotherTitle: 'Fr.',
    researcherTitle: 'Chercheur',
    homeTitle: 'Bibliothèque Dehonienne',
    homeSubtitle1: 'Pour des <strong>temps nouveaux, des œuvres nouvelles</strong>.',
    homeSubtitle2: 'L\'intelligence au service <strong>du Cœur</strong>.',
    suggestionsLabel: 'Suggestions de recherche',
    shuffleBtn: 'Tourner 🎲',
    inputPlaceholder: 'Posez une question sur la vie, les lettres ou la théologie du Père Dehon...',
    sendBtn: 'Envoyer le message',
    newChatBtn: 'Nouvelle Recherche',
    historyTitle: 'Historique des recherches',
    profileTitle: 'Profil & Paramètres',
    logoutBtn: 'Déconnexion',
    copyBtn: 'Copier',
    copiedBtn: 'Copié!',
    shareBtn: 'Partager',
    sharedBtn: 'Lien copié!',
    referencesBtn: 'Références',
    exportABNT: 'Exporter (.ris + ABNT)',
    relatedQuestionsLabel: 'Questions Connexes',
    footerDeveloper: 'Système de haute recherche développé par',
    languageSelectLabel: 'Langue de l\'interface',
  },
  it: {
    greetingMorning: 'Buongiorno',
    greetingAfternoon: 'Buon pomeriggio',
    greetingEvening: 'Buonasera',
    greetingQuestion: 'Come posso aiutarti nella tua ricerca oggi?',
    fatherTitle: 'Padre',
    brotherTitle: 'Fra',
    researcherTitle: 'Ricercatore',
    homeTitle: 'Biblioteca Dehoniana',
    homeSubtitle1: 'Per <strong>tempi nuovi, opere nuove</strong>.',
    homeSubtitle2: 'L\'intelligenza al servizio <strong>del Cuore</strong>.',
    suggestionsLabel: 'Suggerimenti di ricerca',
    shuffleBtn: 'Ruota 🎲',
    inputPlaceholder: 'Chiedi sulla vita, le lettere o la teologia di Padre Dehon...',
    sendBtn: 'Invia messaggio',
    newChatBtn: 'Nuova Ricerca',
    historyTitle: 'Cronologia ricerche',
    profileTitle: 'Profilo & Impostazioni',
    logoutBtn: 'Esci',
    copyBtn: 'Copia',
    copiedBtn: 'Copiato!',
    shareBtn: 'Condividi',
    sharedBtn: 'Link Copiato!',
    referencesBtn: 'Riferimenti',
    exportABNT: 'Esporta (.ris + ABNT)',
    relatedQuestionsLabel: 'Domande Correlate',
    footerDeveloper: 'Sistema di alta ricerca sviluppato da',
    languageSelectLabel: 'Lingua dell\'interfaccia',
  },
  es: {
    greetingMorning: 'Buenos días',
    greetingAfternoon: 'Buenas tardes',
    greetingEvening: 'Buenas noches',
    greetingQuestion: '¿Cómo puedo ayudarte en tu investigación hoy?',
    fatherTitle: 'Padre',
    brotherTitle: 'Hno.',
    researcherTitle: 'Investigador',
    homeTitle: 'Biblioteca Dehoniana',
    homeSubtitle1: 'Para <strong>tiempos nuevos, obras nuevas</strong>.',
    homeSubtitle2: 'La inteligencia al servicio <strong>del Corazón</strong>.',
    suggestionsLabel: 'Sugerencias de Investigación',
    shuffleBtn: 'Girar 🎲',
    inputPlaceholder: 'Pregunta sobre la vida, cartas o teología del Padre Dehon...',
    sendBtn: 'Enviar mensaje',
    newChatBtn: 'Nueva Investigación',
    historyTitle: 'Historial de búsquedas',
    profileTitle: 'Perfil y Configuración',
    logoutBtn: 'Cerrar Sesión',
    copyBtn: 'Copiar',
    copiedBtn: '¡Copiado!',
    shareBtn: 'Compartir',
    sharedBtn: '¡Enlace Copiado!',
    referencesBtn: 'Referencias',
    exportABNT: 'Exportar (.ris + ABNT)',
    relatedQuestionsLabel: 'Preguntas Relacionadas',
    footerDeveloper: 'Sistema de Alta Investigación desarrollado por',
    languageSelectLabel: 'Idioma de la Interfaz',
  },
  pl: {
    greetingMorning: 'Dzień dobry',
    greetingAfternoon: 'Dzień dobry',
    greetingEvening: 'Dobry wieczór',
    greetingQuestion: 'Jak mogę pomóc w Twoich badaniach dzisiaj?',
    fatherTitle: 'Ksiądz',
    brotherTitle: 'Brat',
    researcherTitle: 'Badacz',
    homeTitle: 'Biblioteka Dehoniańska',
    homeSubtitle1: 'Na <strong>nowe czasy, nowe dzieła</strong>.',
    homeSubtitle2: 'Inteligencja w służbie <strong>Serca</strong>.',
    suggestionsLabel: 'Sugestie wyszukiwania',
    shuffleBtn: 'Losuj 🎲',
    inputPlaceholder: 'Zapytaj o życie, listy lub teologię o. Dehona...',
    sendBtn: 'Wyślij wiadomość',
    newChatBtn: 'Nowe Badanie',
    historyTitle: 'Historia wyszukiwania',
    profileTitle: 'Profil i Ustawienia',
    logoutBtn: 'Wyloguj się',
    copyBtn: 'Kopiuj',
    copiedBtn: 'Skopiowano!',
    shareBtn: 'Udostępnij',
    sharedBtn: 'Link skopiowany!',
    referencesBtn: 'Odnośniki',
    exportABNT: 'Eksportuj (.ris + ABNT)',
    relatedQuestionsLabel: 'Powiązane Pytania',
    footerDeveloper: 'Zaawansowany system badawczy opracowany przez',
    languageSelectLabel: 'Język interfejsu',
  }
};
