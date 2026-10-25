import { dateIN, num } from '../lib/format'
import { NumberBadge } from './NumberBadge'

export function DiffRibbon({ diff }: { diff: any }) {
  return (
    <div className="slip ink rules dbl" data-no="RE-SUBMISSION DIFF · v1 to v2" style={{ borderRightStyle: 'solid' }}>
      <div style={{ fontFamily: 'var(--serif)', fontSize: '1.1rem', fontWeight: 700 }}>{diff.ribbon}</div>
      <table className="ledger sm tight" style={{ marginTop: 6 }}><thead><tr><th>claim</th><th className="num">was</th><th className="num">now</th></tr></thead>
        <tbody>{diff.changed.map((c: any) => <tr key={c.key}><td className="t">{c.key}</td><td className="num">{num(c.from)}</td><td className="num"><b>{num(c.to)}</b></td></tr>)}</tbody></table>
      <div className="xs dim" style={{ marginTop: 6 }}>Re-run only: {diff.rules_rerun.join(', ')}. Resolved: {diff.findings_resolved.join(', ')}. Still pending: {diff.findings_pending.join(', ')}.</div>
    </div>
  )
}

export function BundleCard({ b, fins, lang }: { b: any; fins: any[]; lang: 'en' | 'hi' | 'mr' }) {
  const kids = fins.filter(f => b.finding_ids.includes(f.id))
  return (
    <div className="folder" data-tab={`BUNDLE ${b.id}`}>
      <div className="row between"><h3>{b.root_cause}</h3><span className="t xs">{kids.length} findings · 1 request</span></div>
      <div className="inner">{kids.map(k => <div key={k.id} className="t xs" style={{ padding: '2px 0', borderBottom: '1px dotted var(--rule)' }}>{k.id} {k.explanation.slice(0, 92)}…</div>)}</div>
      <div className="xs" style={{ marginTop: 8 }}><b>Cheapest next step:</b> {b.top_action.kind.replace(/_/g, ' ')} (cost {b.top_action.cost}). {b.top_action.why}.</div>
      <div className="slip ink ai" style={{ marginTop: 8, borderRightStyle: 'solid' }}><span className="who ai">AI-drafted · numbers checked · officer sends</span>
        <div className="sm" style={{ marginTop: 4 }}>{LETTER[lang] ?? b.letter_en}</div><NumberBadge text={LETTER[lang] ?? b.letter_en} fins={kids} /></div>
    </div>
  )
}
export const LETTER: Record<string, string> = {
  en: 'Your documents give the trust’s name in three different ways (affidavit, land record and AICTE record). Please upload one certified trust registration certificate that matches your AICTE record, or tell us which document is out of date. Refs: F-011, F-012, F-013 (TRUST_NAME_CONSISTENT, eoa_v1).',
  hi: 'आपके दस्तावेज़ों (शपथपत्र, भूमि अभिलेख और AICTE रिकॉर्ड) में ट्रस्ट का नाम तीन अलग-अलग रूपों में दिया गया है। कृपया AICTE रिकॉर्ड से मेल खाता एक प्रमाणित ट्रस्ट पंजीकरण प्रमाणपत्र अपलोड करें, या बताएँ कि कौन-सा दस्तावेज़ पुराना है। संदर्भ: F-011, F-012, F-013 (TRUST_NAME_CONSISTENT, eoa_v1)।',
  mr: 'तुमच्या कागदपत्रांमध्ये (प्रतिज्ञापत्र, जमीन अभिलेख आणि AICTE नोंद) ट्रस्टचे नाव तीन वेगवेगळ्या प्रकारे दिले आहे. कृपया AICTE नोंदीशी जुळणारे एक प्रमाणित ट्रस्ट नोंदणी प्रमाणपत्र अपलोड करा, किंवा कोणते कागदपत्र जुने आहे ते कळवा. संदर्भ: F-011, F-012, F-013 (TRUST_NAME_CONSISTENT, eoa_v1).',
}
