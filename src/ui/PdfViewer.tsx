import { useEffect, useRef, useState } from 'react'
import * as pdfjs from 'pdfjs-dist'
pdfjs.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url).toString()

export interface Box { field: string; text: string; box: [number, number, number, number] }

/** Renders one PDF page to a canvas and overlays PyMuPDF boxes (PDF points, origin top-left) scaled to the canvas. */
export function PdfViewer({ doc, page, box }: { doc: string; page: number; box?: Box | null }) {
  const ref = useRef<HTMLCanvasElement>(null)
  const [dim, setDim] = useState<{ w: number; h: number } | null>(null)
  const [missing, setMissing] = useState(false)
  useEffect(() => {
    let dead = false; setMissing(false)
    ;(async () => {
      try {
        const pdf = await pdfjs.getDocument(`/fixtures/pdfs/${doc}.pdf`).promise
        const pg = await pdf.getPage(Math.min(page, pdf.numPages))
        const vp = pg.getViewport({ scale: 1.6 }); const c = ref.current; if (!c || dead) return
        c.width = vp.width; c.height = vp.height
        await pg.render({ canvasContext: c.getContext('2d')!, viewport: vp }).promise
        if (!dead) setDim({ w: vp.width / 1.6, h: vp.height / 1.6 })
      } catch { if (!dead) setMissing(true) }
    })()
    return () => { dead = true }
  }, [doc, page])
  if (missing) return <div className="slip" style={{ marginTop: 12 }}><b>{doc}</b> is not in the 8-document sample set.<div className="xs dim">The real backend serves every uploaded file from /documents/{'{id}'}/file.</div></div>
  return (
    <div className="pdfwrap">
      <canvas ref={ref} />
      {box && dim && <div className="hl" aria-label={`Evidence: ${box.text}`} style={{ left: `${(box.box[0] / dim.w) * 100}%`, top: `${(box.box[1] / dim.h) * 100}%`, width: `${((box.box[2] - box.box[0]) / dim.w) * 100}%`, height: `${((box.box[3] - box.box[1]) / dim.h) * 100}%` }} />}
      <div className="t xs" style={{ position: 'absolute', left: 6, bottom: 4, background: 'var(--paper-hi)', border: '1px solid var(--ink)', padding: '0 5px' }}>{doc} · page {page}</div>
    </div>
  )
}
