import { useContext } from 'react'
import { AppCtx } from '../ctx'

const L: Record<string, [string, string, string]> = {
  PASSED: ['Passed', 'उत्तीर्ण', 'उत्तीर्ण'], FAILED: ['Failed', 'विफल', 'अनुत्तीर्ण'], MANUAL_REVIEW: ['Manual review', 'मैन्युअल समीक्षा', 'हस्त-तपासणी'],
  NOT_CONFIGURED: ['Not configured', 'विन्यस्त नहीं', 'संरचित नाही'], UNABLE_TO_VERIFY: ['Unable to verify', 'सत्यापन अक्षम', 'पडताळणी अशक्य'], CONFLICT: ['Conflict', 'विरोधाभास', 'विसंगती'],
}
/** Status is never colour-only: the words are always printed. Dashed = could not check. Double border = sources disagree. */
export function Stamp({ state, big = false }: { state: string; big?: boolean }) {
  const { lang } = useContext(AppCtx)
  const k = state.replace(/ /g, '_'); const t = L[k] ?? [state, state, state]
  return <span role="status" className={`stamp ${k} ${big ? 'big' : ''}`}>{lang === 'hi' ? t[1] : lang === 'mr' ? t[2] : t[0]}</span>
}
