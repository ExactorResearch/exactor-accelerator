# Outbound Email Signatures & B2B Demo Scheduling Guide

This guide establishes the standardized outbound communication templates, corporate email signatures, and demo scheduling workflows for **Exactor Accelerator** across all commercial and technical touchpoints.

---

## 1. Official Contact & Scheduling Parameters

- **Official Commercial Inbox:** `contact@exactor.tech`
- **Direct Demo & Architecture Scheduling URL:** `https://cal.com/exactor-tech` (or `https://calendly.com/exactor-tech/architecture-review`)
- **Interactive Live Demos:**
  - **Exactor WAF Guardian:** `https://waf.exactor.ai`
  - **Exactor Sudoku Arena:** `https://sudoku.exactor.ai`
  - **Exactor Minesweeper:** `https://minesweeper.exactor.ai`
- **Tally Form ID:** `w2xD4P` (Embed & Modal)

---

## 2. Lead Capture Form Specification (4 Key B2B Fields)

Every inbound touchpoint across Tally, Typeform, and the 3 demo modals captures exactly 4 qualifying fields:

| Field Name | Input Type | Description & Purpose |
| :--- | :--- | :--- |
| **1. Full Name** | `Single-line Text` | Lead identification and personalized follow-up. |
| **2. Work Email** | `Email (Corporate)` | Verification of business domain and enterprise routing. |
| **3. Company & Role** | `Single-line Text` | Title & account qualification (e.g., *Acme Cloud — VP Engineering / SecOps Lead*). |
| **4. Use Case & Decision Volume** | `Multi-line Text` | Workload characterization (e.g., *WAF traffic at 50k req/s, Agent verification, SLA bottlenecks*). |

---

## 3. Outbound Email Signatures

### Variant A: Executive & Commercial (CEO / Head of Business Development)

#### Plain Text / Markdown:
```text
--
Alex Mercer
Founding Team & Commercial Lead | Exactor Accelerator
Sub-Millisecond Boolean Reflex Engine for Enterprise AI
Email: contact@exactor.tech
Web: https://exactor.tech

Book a 15-Min Technical Architecture Review:
👉 https://cal.com/exactor-tech

Explore Interactive Demos:
• WAF Guardian: https://waf.exactor.ai
• Neuro-Symbolic SAT Arena: https://minesweeper.exactor.ai
• Constraint Engine: https://sudoku.exactor.ai
```

#### Rich HTML (for Gmail, Outlook, Superhuman):
```html
<table style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.5; color: #1e293b; border-top: 2px solid #06b6d4; padding-top: 14px; margin-top: 16px;">
  <tr>
    <td style="vertical-align: top; padding-right: 18px;">
      <div style="width: 44px; height: 44px; background: linear-gradient(135deg, #06b6d4, #a855f7); border-radius: 10px; display: flex; align-items: center; justify-content: center; text-align: center; color: #ffffff; font-weight: 800; font-size: 20px; line-height: 44px;">
        ⚡
      </div>
    </td>
    <td style="vertical-align: top;">
      <div style="font-size: 15px; font-weight: 700; color: #0f172a;">Exactor Accelerator Team</div>
      <div style="font-size: 13px; color: #64748b; margin-bottom: 6px;">Enterprise AI Muscular Memory Layer • Deterministic Reflexes</div>
      <div style="font-size: 13px; margin-bottom: 10px;">
        <span style="color: #64748b;">Direct:</span> <a href="mailto:contact@exactor.tech" style="color: #0284c7; text-decoration: none; font-weight: 600;">contact@exactor.tech</a>
        <span style="color: #cbd5e1; margin: 0 6px;">|</span>
        <span style="color: #64748b;">Web:</span> <a href="https://exactor.tech" style="color: #0284c7; text-decoration: none;">exactor.tech</a>
      </div>
      <div style="margin-top: 8px;">
        <a href="https://cal.com/exactor-tech" style="display: inline-block; background: #0284c7; color: #ffffff; font-weight: 600; font-size: 12px; padding: 6px 14px; border-radius: 6px; text-decoration: none; margin-right: 8px;">
          📅 Schedule 15-Min Live Demo
        </a>
        <a href="https://waf.exactor.ai" style="display: inline-block; background: #f1f5f9; color: #334155; font-weight: 600; font-size: 12px; padding: 6px 12px; border-radius: 6px; text-decoration: none;">
          ⚡ Test Live Interactive WAF
        </a>
      </div>
    </td>
  </tr>
</table>
```

---

### Variant B: Solutions Architect & Applied AI Engineering

#### Plain Text / Markdown:
```text
--
Solutions Architecture & Core Systems
Exactor Accelerator (Rust 2024 Core)
Fast-Path Latency: 0.05ms | 100% Deterministic Glass-Box Verification
E: contact@exactor.tech | Cal.com: https://cal.com/exactor-tech

Interactive Testbenches:
- WAF Guardian: https://waf.exactor.ai
- Sudoku Solver Benchmark: https://sudoku.exactor.ai
- Minesweeper SAT vs Pure JEV: https://minesweeper.exactor.ai
```

---

## 4. Multi-Touchpoint Integration in the 3 Demos

All 3 demo applications have been equipped with:

1. **Header Contact Action:** A high-visibility button (`📅 Book Demo / Contact`) placed in the primary navigation header across all viewports.
2. **Direct Booking Link:** Integrated button redirecting directly to Cal.com for friction-free calendar reservations.
3. **Embedded Tally / Typeform:** Integration supporting one-click popups via Tally Widget SDK.
4. **Native In-App Evaluation Form:** A 4-field modal with local validation, dispatching asynchronously to the backend `/api/contact` endpoint and triggering an immediate pre-formatted `mailto:contact@exactor.tech` fallback.
