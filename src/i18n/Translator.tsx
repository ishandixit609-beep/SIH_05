import { useEffect } from 'react'
import type { Lang } from '../ctx'
import { translate } from './dict'

/** Language layer. Every piece of English text on screen is looked up in the dictionary (src/i18n/dict*.ts)
    and swapped for Hindi or Marathi. It works on the DOM, so it covers every page, tab, modal and fixture string
    without touching component code; the original English is remembered and restored when you switch back to EN.
    A text that is not in the dictionary stays in English (never blank). Add the missing line to the dictionary. */
interface Rec { orig: string; shown: string }
const REC = new WeakMap<Text, Rec>()
const ATTRS = ['placeholder', 'title', 'aria-label', 'alt', 'data-no', 'data-tab']
const SKIP = 'script,style,textarea,input,[data-no-i18n],svg defs'

const origOf = (t: Text) => { const r = REC.get(t); return r && t.data === r.shown ? r.orig : t.data }
function applyRun(run: Text[], lang: Lang) {
  const origs = run.map(origOf); const full = origs.join('')
  if (!full.trim()) return
  const out = lang === 'en' ? null : translate(full, lang)
  if (out == null) {
    run.forEach((t, i) => { if (t.data !== origs[i]) t.data = origs[i]; REC.set(t, { orig: origs[i], shown: origs[i] }) })
    if (lang !== 'en' && run.length > 1) run.forEach(t => { const o = REC.get(t)!.orig; const tr = translate(o, lang); if (tr != null) { t.data = tr; REC.set(t, { orig: o, shown: tr }) } })
    return
  }
  const lead = full.match(/^\s*/)![0], trail = full.match(/\s*$/)![0]
  run.forEach((t, i) => { const shown = i === 0 ? lead + out + trail : ''; if (t.data !== shown) t.data = shown; REC.set(t, { orig: origs[i], shown }) })
}
function applyEl(el: Element, lang: Lang) {
  if (el.closest(SKIP)) return
  let run: Text[] = []
  const flush = () => { if (run.length) applyRun(run, lang); run = [] }
  el.childNodes.forEach(n => { if (n.nodeType === 3) run.push(n as Text); else flush() }); flush()
  for (const a of ATTRS) {
    if (!el.hasAttribute(a)) continue
    const k = `data-i18n-${a}`; const cur = el.getAttribute(a)!; const stored = el.getAttribute(k)
    const orig = stored !== null && cur === (el as any)[`__${a}`] ? stored : cur
    const out = lang === 'en' ? null : translate(orig, lang)
    const next = out ?? orig
    if (cur !== next) el.setAttribute(a, next)
    el.setAttribute(k, orig); (el as any)[`__${a}`] = next
  }
}
const all = (root: Node, lang: Lang) => { if (root.nodeType !== 1) return; const el = root as Element; applyEl(el, lang); el.querySelectorAll('*').forEach(e => applyEl(e, lang)) }

export function Translator({ lang }: { lang: Lang }) {
  useEffect(() => {
    document.documentElement.lang = lang
    const obs = new MutationObserver(recs => {
      obs.disconnect()
      const q = new Set<Node>()
      for (const r of recs) {
        if (r.type === 'characterData') { if (r.target.parentElement) q.add(r.target.parentElement) }
        else if (r.type === 'attributes') q.add(r.target)
        else { r.addedNodes.forEach(n => q.add(n.nodeType === 1 ? n : (n.parentElement as Node))); if (r.target.nodeType === 1) q.add(r.target) }
      }
      q.forEach(n => n && n.isConnected && (n.nodeType === 1) && (n === document.body ? all(n, lang) : (applyEl(n as Element, lang), (n as Element).querySelectorAll('*').forEach(e => applyEl(e, lang)))))
      watch()
    })
    const watch = () => obs.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS })
    all(document.body, lang); watch()
    // Developer helper: window.__i18nMissing() lists English text that has no translation on the current page.
    ;(window as any).__i18nMissing = () => {
      const miss = new Set<string>()
      document.body.querySelectorAll('*').forEach(el => {
        if (el.closest(SKIP)) return
        let run: Text[] = []; const flush = () => { if (run.length) { const o = run.map(origOf).join('').replace(/\s+/g, ' ').trim(); if (/[A-Za-z]{3,}/.test(o) && translate(o, 'hi') == null) miss.add(o) } run = [] }
        el.childNodes.forEach(n => { if (n.nodeType === 3) run.push(n as Text); else flush() }); flush()
      }); return [...miss]
    }
    return () => obs.disconnect()
  }, [lang])
  return null
}
