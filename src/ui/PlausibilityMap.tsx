import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { photoSrc } from './PhotoEvidence'

/** Real interactive map (OpenStreetMap tiles, loaded in the browser). Pins are the photos' own coordinates, the dashed box is the
    declared campus polygon, the red line is the gap. Location is a hint, never proof. Tiles need internet; pins and polygon do not. */
const pin = (n: number, bad: boolean, on: boolean) => L.divIcon({ className: '', iconSize: [30, 38], iconAnchor: [15, 36],
  html: `<div class="gpin ${bad ? 'bad' : 'ok'} ${on ? 'on' : ''}"><span>${n}</span></div>` })

export function PlausibilityMap({ ph, sel, onSel }: { ph: any; sel?: number | null; onSel?: (n: number) => void }) {
  const el = useRef<HTMLDivElement>(null); const map = useRef<L.Map | null>(null); const marks = useRef<Record<number, L.Marker>>({})
  const poly: [number, number][] = ph.campus_polygon
  const lat0 = poly.reduce((a, p) => a + p[0], 0) / poly.length, lon0 = poly.reduce((a, p) => a + p[1], 0) / poly.length
  const gps: any[] = ph.photos.filter((p: any) => p.lat != null)

  useEffect(() => {
    if (!el.current) return
    try {
      const m = L.map(el.current, { scrollWheelZoom: false, zoomControl: true, attributionControl: true }).setView([lat0, lon0], 12); map.current = m
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(m)
      L.polygon(poly, { color: '#2F7BFF', weight: 2, dashArray: '6 4', fillOpacity: 0.18 }).addTo(m).bindTooltip('Declared campus', { permanent: false })
      L.circleMarker([lat0, lon0], { radius: 9, color: '#fff', weight: 3, fillColor: '#2F7BFF', fillOpacity: 1 }).addTo(m).bindTooltip('Declared campus', { permanent: true, direction: 'right', offset: [10, 0] })
      const far = gps.filter(p => p.status === 'far_from_campus')
      far.forEach(p => L.polyline([[lat0, lon0], [p.lat, p.lon]], { color: '#D23A30', weight: 2, dashArray: '8 6' }).addTo(m))
      gps.forEach(p => {
        const k = L.marker([p.lat + (p.status === 'inside_campus' ? (p.photo - 3.5) * 0.0004 : (p.photo - 5.5) * 0.004), p.lon + (p.status === 'inside_campus' ? (p.photo - 3.5) * 0.0004 : (p.photo - 5.5) * 0.02)], { icon: pin(p.photo, p.status === 'far_from_campus', false) }).addTo(m)
        k.bindPopup(`<div class="gpop"><img src="${photoSrc(p.photo)}" alt=""/><b>Photo #${p.photo}</b><br/>${p.status === 'inside_campus' ? 'Inside the declared campus' : `${p.km} km from the declared campus`}</div>`)
        k.on('click', () => onSel?.(p.photo)); marks.current[p.photo] = k
      })
      m.fitBounds(L.latLngBounds([[lat0, lon0], ...gps.map(p => [p.lat, p.lon] as [number, number])]).pad(0.15))
      setTimeout(() => m.invalidateSize(), 200)
    } catch { /* map is a bonus: never break the case desk */ }
    return () => { map.current?.remove(); map.current = null; marks.current = {} }
  }, [ph])

  useEffect(() => {
    const m = map.current; if (!m || sel == null) return
    Object.entries(marks.current).forEach(([n, k]) => { const p = gps.find(x => x.photo === +n); k.setIcon(pin(+n, p?.status === 'far_from_campus', +n === sel)) })
    const k = marks.current[sel]; if (k) { m.flyTo(k.getLatLng(), sel > 4 ? 11 : 16, { duration: 0.8 }); k.openPopup() }
  }, [sel])

  const near = () => map.current?.flyTo([lat0, lon0], 16, { duration: 0.8 })
  const all = () => map.current?.fitBounds(L.latLngBounds([[lat0, lon0], ...gps.map(p => [p.lat, p.lon] as [number, number])]).pad(0.15))
  return (
    <div className="mapbox">
      <div className="mapbar"><span className="t xs up dim">live map · {gps.length} photos with GPS · {ph.photos.length - gps.length} without</span>
        <span className="row" style={{ gap: 6 }}><button className="btn" onClick={all}>All photos</button><button className="btn" onClick={near}>Campus</button></span></div>
      <div ref={el} className="leaf" role="application" aria-label="Map of photo locations" />
      <div className="xs dim" style={{ padding: '8px 12px', borderTop: '1px solid var(--rule)' }}>Distance is a hint, not proof: a missing GPS tag is neutral, so the officer asks for geo-tagged photos first.</div>
    </div>
  )
}
