import React, { createContext, useContext, useState } from 'react';
import { type Language, type Translations, TRANSLATIONS } from '../i18n/translations';

export type ViewMode = 'farmer' | 'expert';

interface ViewModeContextType {
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: keyof Translations) => string;
  selectedFarmerId: string | null;
  setSelectedFarmerId: (id: string | null) => void;
}

const ViewModeContext = createContext<ViewModeContextType | undefined>(undefined);

const VIEW_MODE_STORAGE_KEY = 'aquamedi_view_mode';
const LANGUAGE_STORAGE_KEY = 'aquamedi_language';

export const ViewModeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [viewMode, setViewModeState] = useState<ViewMode>(() => {
    try {
      const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
      if (saved === 'farmer' || saved === 'expert') {
        return saved;
      }
    } catch {
      // Storage access blocked or unavailable
    }
    // Farmer View is the default presentation mode
    return 'farmer';
  });

  const [language, setLanguageState] = useState<Language>(() => {
    try {
      const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY);
      if (saved === 'en' || saved === 'hi' || saved === 'gu') {
        return saved;
      }
    } catch {
      // Storage access blocked or unavailable
    }
    return 'en';
  });

  const [selectedFarmerId, setSelectedFarmerId] = useState<string | null>(null);

  const setViewMode = (mode: ViewMode) => {
    setViewModeState(mode);
    try {
      localStorage.setItem(VIEW_MODE_STORAGE_KEY, mode);
    } catch {
      // ignore
    }
  };

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    try {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
    } catch {
      // ignore
    }
  };

  const t = (key: keyof Translations): string => {
    const langDict = TRANSLATIONS[language] || TRANSLATIONS.en;
    return langDict[key] || TRANSLATIONS.en[key] || key;
  };

  return (
    <ViewModeContext.Provider
      value={{
        viewMode,
        setViewMode,
        language,
        setLanguage,
        t,
        selectedFarmerId,
        setSelectedFarmerId,
      }}
    >
      {children}
    </ViewModeContext.Provider>
  );
};

export function useViewMode(): ViewModeContextType {
  const context = useContext(ViewModeContext);
  if (!context) {
    throw new Error('useViewMode must be used within a ViewModeProvider');
  }
  return context;
}
