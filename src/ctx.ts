import { createContext } from 'react'
export type Lang = 'en' | 'hi' | 'mr'
export const AppCtx = createContext<{ rev: number; bump: () => void; lang: Lang; setLang: (l: Lang) => void; say: (m: string) => void }>(
  { rev: 0, bump: () => {}, lang: 'en', setLang: () => {}, say: () => {} })
export const APP_ID = 'APP-0001'
