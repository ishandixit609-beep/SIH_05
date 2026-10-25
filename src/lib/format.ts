// India-first formatting. Always pin the zone: judges' laptops may be set to UTC.
export const inr = (n: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n) // ₹1,80,000
export const num = (n: number) => new Intl.NumberFormat('en-IN').format(n)                                                                   // 1,80,000
export const dateIN = (iso: string) => new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata' }).format(new Date(iso)) // 15 Nov 2026
export const dateTimeIST = (iso: string) => new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Kolkata' }).format(new Date(iso)) + ' IST'
/** Fixed demo clock so the video never drifts: 12 Jan 2027, 10:30 IST */
export const DEMO_NOW = '2027-01-12T10:30:00+05:30'
