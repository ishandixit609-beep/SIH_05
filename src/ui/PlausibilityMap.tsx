/** Offline schematic (no map tiles): campus at the centre, rings in km on a square-root scale, photos placed by distance.
    Photos with no GPS sit in a neutral tray. Location is a hint, never proof. */
export function PlausibilityMap({ ph }: { ph: any }) {
  const R = (km: number) => 14 + Math.sqrt(km) * 21
  const withGps = ph.photos.filter((p: any) => p.status !== 'no_location_data')
  const none = ph.photos.filter((p: any) => p.status === 'no_location_data')
  return (
    <svg viewBox="0 0 700 340" width="100%" role="img" aria-label="Photo locations relative to campus">
      <g transform="translate(220 170)">
        {[1, 5, 20, 40].map(km => <g key={km}><circle r={R(km)} fill="none" stroke="var(--rule)" strokeDasharray="3 4" /><text x={R(km) + 3} y="-3" fontFamily="var(--type)" fontSize="9" fill="var(--ink-2)">{km} km</text></g>)}
        <rect x="-16" y="-12" width="32" height="24" fill="var(--manila)" stroke="var(--ink)" strokeWidth="1.5" /><text y="4" textAnchor="middle" fontFamily="var(--type)" fontSize="9" fontWeight="700">CAMPUS</text>
        {withGps.map((p: any, i: number) => {
          const ang = (-0.9 + i * 0.5) + (p.status === 'far_from_campus' ? 0.8 : 0), r = p.km ? R(p.km) : 30
          const x = Math.cos(ang) * r, y = Math.sin(ang) * r, far = p.status === 'far_from_campus'
          return <g key={p.photo} transform={`translate(${x} ${y})`}><circle r="8" fill={far ? 'var(--stamp)' : 'var(--ok)'} stroke="var(--ink)" /><text y="3.5" textAnchor="middle" fontFamily="var(--type)" fontSize="9" fill="#fff" fontWeight="700">{p.photo}</text></g>
        })}
      </g>
      <g transform="translate(470 40)">
        <text fontFamily="var(--serif)" fontWeight="700" fontSize="13">Photo location, six uploads</text>
        {ph.photos.map((p: any, i: number) => (
          <g key={p.photo} transform={`translate(0 ${24 + i * 24})`}><circle cx="8" cy="0" r="7" fill={p.status === 'far_from_campus' ? 'var(--stamp)' : p.status === 'inside_campus' ? 'var(--ok)' : 'var(--paper-lo)'} stroke="var(--ink)" strokeDasharray={p.status === 'no_location_data' ? '2 2' : ''} />
            <text x="22" y="4" fontFamily="var(--type)" fontSize="11">#{p.photo} {p.status === 'no_location_data' ? 'no location data (neutral)' : p.status === 'inside_campus' ? 'inside campus' : `${p.km} km from campus`}</text></g>
        ))}
        <text y="196" fontFamily="var(--type)" fontSize="10" fill="var(--ink-2)">{none.length} photos carry no GPS: shown neutrally.</text>
        <text y="212" fontFamily="var(--type)" fontSize="10" fill="var(--ink-2)">Distance is a hint: ask for geo-tagged photos first.</text>
      </g>
    </svg>
  )
}
