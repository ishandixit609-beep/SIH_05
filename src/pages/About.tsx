const SRC: [string, string, string][] = [
  ['APAAR FAQs', 'https://apaar.education.gov.in/faqs', 'Academic identity, records, credit mobility and student lifecycle context.'],
  ['AICTE ONOD portal', 'https://onod.aicte-india.org/', 'AISHE code, open-API and higher-education reporting description.'],
  ['DigiLocker security architecture', 'https://www.digilocker.gov.in/web/security-architecture', 'Issuer and requester roles, digital signatures, access and consent.'],
  ['AICTE Approval Process Handbook 2024-27', 'https://www.aicte.gov.in/sites/default/files/APH%20Final.pdf', 'Application rules and scrutiny process. Check newer circulars and amendments.'],
  ['Controller of Certifying Authorities', 'https://www.cca.gov.in/index.php/signature_verification.html', 'Digital-signature verification fundamentals.'],
  ['PS5 statement (reference copy)', 'https://zaidsayyed.in/tools/sih-problem-statements/sih26261', 'Confirm the final wording with the official SIH portal or your SPOC.'],
]
export function About() {
  return (
    <main style={{ paddingTop: 18 }}>
      <div className="t xs up dim">Method · scope · sources</div><h1 style={{ fontSize: '1.8rem' }}>A useful layer, not another portal</h1>
      <p className="sm dim" style={{ maxWidth: 700 }}>SATYAPAN is a proposed product concept for application scrutiny. The gaps it targets are hypotheses to validate with real reviewers and the current rules, not confirmed faults in any existing portal.</p>
      <div className="grid2" style={{ marginTop: 14 }}>
        <div className="slip ink human" data-no="WHAT IT BUILDS ON" style={{ borderRightStyle: 'solid' }}>
          <p className="sm" style={{ margin: 0 }}>AICTE's approval process, DigiLocker's issuer-based documents and AICTE ONOD already cover identity, data sharing, digital documents and approval. SATYAPAN sits around them: evidence coverage, change-aware review, correction guidance and visible exceptions. It creates no new student ID and no new central repository.</p></div>
        <div className="slip ink rules" data-no="MVP BOUNDARY" style={{ borderRightStyle: 'solid' }}>
          <ul className="sm" style={{ margin: 0, paddingLeft: 18 }}><li>Synthetic data only. No real institution records without approval.</li><li>Issuer connectors are simulated and labelled. No live access is implied.</li><li>Quality is measured: recall, false positives, evidence completeness, reviewer time.</li><li>Flags are indicators. Authorised officers decide.</li></ul></div>
      </div>
      <div className="slip ink" data-no="WE DO NOT CLAIM" style={{ marginTop: 18, borderRightStyle: 'solid' }}>
        <ul className="sm" style={{ margin: 0, paddingLeft: 18 }}><li>That AI can universally detect fake documents.</li><li>That the system approves or rejects any institution.</li><li>That norms and clauses shown here are the official text. They are illustrative until copied from APH 2024-27.</li><li>Real time savings, until they are measured in a user test.</li></ul></div>
      <h3 style={{ marginTop: 22 }}>Official baseline references</h3>
      <table className="ledger sm" style={{ marginTop: 6 }}><thead><tr><th>source</th><th>link</th><th>used for</th></tr></thead><tbody>
        {SRC.map(([n, u, w]) => <tr key={u}><td>{n}</td><td className="t xs"><a href={u} target="_blank" rel="noreferrer">{u}</a></td><td>{w}</td></tr>)}</tbody></table>
    </main>
  )
}
