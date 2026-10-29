import { useEffect, useRef, useState } from 'react'
import * as pdfjs from 'pdfjs-dist'
pdfjs.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url).toString()

export interface Box { field: string; text: string; box: [number, number, number, number] }

/** Document viewer. Renders one PDF page and marks the evidence the way a reviewer would on paper:
    the rest of the page dims (spotlight), the exact text is ringed, a tag names the field, and one scan line
    sweeps across it. Boxes are PyMuPDF coordinates (PDF points, origin top-left), scaled to the canvas. */
export function PdfViewer({ doc, page, box }: { doc: string; page: number; box?: Box | null }) {
  const ref = useRef<HTMLCanvasElement>(null)
  const [dim, setDim] = useState<{ w: number; h: number } | null>(null)
  const [pages, setPages] = useState(0); const [zoom, setZoom] = useState(1); const [spot, setSpot] = useState(true)
  const [missing, setMissing] = useState(false)
  useEffect(() => {
    let dead = false; setMissing(false)
    ;(async () => {
      try {
        const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api'
        let pdf: any
        try { pdf = await pdfjs.getDocument(`${BASE}/documents/${doc}/file`).promise }
        catch { pdf = await pdfjs.getDocument(`/fixtures/pdfs/${doc}.pdf`).promise }
        const pg = await pdf.getPage(Math.min(page, pdf.numPages))
        const vp = pg.getViewport({ scale: 1.6 }); const c = ref.current; if (!c || dead) return
        c.width = vp.width; c.height = vp.height
        await pg.render({ canvasContext: c.getContext('2d')!, viewport: vp }).promise
        if (!dead) { setDim({ w: vp.width / 1.6, h: vp.height / 1.6 }); setPages(pdf.numPages) }
      } catch { if (!dead) setMissing(true) }
    })()
    return () => { dead = true }
  }, [doc, page])
  if (missing) return <div className="slip" style={{ marginTop: 12 }}><b>{doc}</b> is not in the 8-document sample set.<div className="xs dim">The real backend serves every uploaded file from /documents/{'{id}'}/file.</div></div>
  const pad = 4
  const g = box && dim ? { l: ((box.box[0] - pad) / dim.w) * 100, t: ((box.box[1] - pad) / dim.h) * 100, w: ((box.box[2] - box.box[0] + pad * 2) / dim.w) * 100, h: ((box.box[3] - box.box[1] + pad * 2) / dim.h) * 100 } : null
  return (
    <div className="pdfwrap">
      <div className="pdfbar">
        <span className="pdfname t">{doc}</span><span className="xs dim">page {page}{pages ? ` of ${pages}` : ''}</span><span className="sp" />
        {box && <button className={`btn mini ${spot ? 'on' : ''}`} onClick={() => setSpot(s => !s)} aria-pressed={spot}>Spotlight</button>}
        <button className="btn mini" onClick={() => setZoom(z => Math.max(0.7, +(z - 0.15).toFixed(2)))} aria-label="Zoom out">−</button>
        <span className="t xs" style={{ minWidth: 38, textAlign: 'center' }}>{Math.round(zoom * 100)}%</span>
        <button className="btn mini" onClick={() => setZoom(z => Math.min(2, +(z + 0.15).toFixed(2)))} aria-label="Zoom in">+</button>
        <button className="btn mini" onClick={() => setZoom(1)}>Fit</button>
      </div>
      <div className="pdfscroll"><div className="pdfpage" style={{ width: `${zoom * 100}%` }}>
        <canvas ref={ref} />
        {g && box && <div key={`${doc}-${page}-${box.text}`} className={`ev ${spot ? 'spot' : ''} ${g.t < 9 ? 'below' : ''}`} aria-label={`Evidence: ${box.text}`} style={{ left: `${g.l}%`, top: `${g.t}%`, width: `${g.w}%`, height: `${g.h}%` }}>
          <span className="scan" /><span className="ev-tag">Evidence · {box.field}</span></div>}
      </div></div>
      {box && <div className="pdffoot"><span className="who rules">evidence</span><b>{box.field}</b><span className="t">{box.text}</span><span className="xs dim">· found in the PDF text layer</span></div>}
    </div>
  )
}
