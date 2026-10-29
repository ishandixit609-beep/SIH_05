import type { Lang } from '../ctx'
import { CORE } from './dict.core'
import { PAGES } from './dict.pages'
import { DATA } from './dict.data'

/** Each entry: [English, Hindi, Marathi]. {name} marks a part that changes (numbers, ids, names). */
export type Entry = [string, string, string]
const norm = (s: string) => s.replace(/\s+/g, ' ').trim()
const EXACT = new Map<string, Entry>(); const PATTERNS: { re: RegExp; names: string[]; e: Entry; weight: number }[] = []
for (const e of [...CORE, ...PAGES, ...DATA]) {
  const key = norm(e[0]); if (!key.includes('{')) { EXACT.set(key, e); continue }
  const names: string[] = []; let src = ''; let weight = 0
  key.split(/(\{\w+\})/).forEach(part => { const m = /^\{(\w+)\}$/.exec(part); if (m) { names.push(m[1]); src += '(.+?)' } else { src += part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); weight += part.length } })
  PATTERNS.push({ re: new RegExp('^' + src + '$'), names, e, weight })
}
PATTERNS.sort((a, b) => b.weight - a.weight)

const MONTHS = {
  hi: ['जनवरी', 'फ़रवरी', 'मार्च', 'अप्रैल', 'मई', 'जून', 'जुलाई', 'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर'],
  mr: ['जानेवारी', 'फेब्रुवारी', 'मार्च', 'एप्रिल', 'मे', 'जून', 'जुलै', 'ऑगस्ट', 'सप्टेंबर', 'ऑक्टोबर', 'नोव्हेंबर', 'डिसेंबर'] }
const EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const localiseDates = (s: string, lang: 'hi' | 'mr') => s
  .replace(/(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\b/g, (_, d, m) => `${d} ${MONTHS[lang][EN.indexOf(m.slice(0, 3))]}`)
  .replace(/(\d{1,2}:\d{2}) (am|pm)\b/g, (_, t, ap) => `${t} ${ap === 'am' ? 'पूर्वाह्न' : 'अपराह्न'}`)
const cache = new Map<string, string | null>()
export function translate(s: string, lang: Lang): string | null {
  if (lang === 'en') return null
  const ck = lang + '|' + s; if (cache.has(ck)) return cache.get(ck)!
  const r = tr(s, lang as 'hi' | 'mr'); cache.set(ck, r); return r
}
function tr(s: string, lang: 'hi' | 'mr'): string | null {
  const key = norm(s); if (!key) return null; const i = lang === 'hi' ? 1 : 2
  const hit = EXACT.get(key); if (hit) return localiseDates(hit[i], lang)
  for (const p of PATTERNS) {
    const m = p.re.exec(key); if (!m) continue
    let out = p.e[i]; p.names.forEach((n, k) => { const v = m[k + 1]; out = out.split(`{${n}}`).join(tr(v, lang) ?? v) }); return localiseDates(out, lang)
  }
  const d = localiseDates(key, lang); return d !== key ? d : null
}
