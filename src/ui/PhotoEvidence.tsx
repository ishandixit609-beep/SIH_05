/** Photo evidence grid. Six uploads, each tagged by what its location data says.
    A missing GPS tag is neutral, a far tag is flagged. Demo images: public/img/p1..p6.jpg (replace with real uploads). */
export const photoSrc = (n: number) => `/img/p${((n - 1) % 6) + 1}.jpg`
export function PhotoEvidence({ ph, sel, onSel }: { ph: any; sel: number | null; onSel: (n: number) => void }) {
  return (
    <div className="photos">
      {ph.photos.map((p: any) => {
        const kind = p.status === 'inside_campus' ? 'ok' : p.status === 'far_from_campus' ? 'bad' : 'none'
        const cap = kind === 'ok' ? 'Inside campus' : kind === 'bad' ? `${p.km} km away` : 'No GPS data'
        return (
          <button key={p.photo} className={`ph ${kind} ${sel === p.photo ? 'sel' : ''}`} onClick={() => onSel(p.photo)} aria-label={`Photo ${p.photo}: ${cap}`}>
            <span className="im" style={{ backgroundImage: `url(${photoSrc(p.photo)})` }}><b>#{p.photo}</b></span>
            <span className="cap">{cap}</span>
          </button>
        )
      })}
    </div>
  )
}
