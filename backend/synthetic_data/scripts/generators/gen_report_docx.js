// Generates incident_initial_report.docx (synthetic). Run: node gen_report_docx.js
const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
        WidthType, ShadingType, LevelFormat } = require("docx");

const out = path.resolve(__dirname, "../../dataset/raw/documents/incident_initial_report.docx");
const P = (t) => new Paragraph({ children: [new TextRun(t)], spacing: { after: 120 } });
const H = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const B = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun(t)] });
const W = [2800, 6226];
const cell = (t, i, head) => new TableCell({
  width: { size: W[i], type: WidthType.DXA },
  shading: head ? { type: ShadingType.CLEAR, fill: "DDE4EE", color: "auto" } : undefined,
  children: [new Paragraph({ children: [new TextRun({ text: t, bold: !!head })] })] });
const row = (a, b, head) => new TableRow({ children: [cell(a, 0, head), cell(b, 1, head)] });

const doc = new Document({
  creator: "Priya Nair (fictional)", title: "INC-2026-1042 Initial Incident Report",
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
    style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 } } }, children: [
    new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("Initial Incident Report: INC-2026-1042")] }),
    P("ShopSphere Engineering. Fictional document for a synthetic dataset."),
    new Table({ width: { size: 9026, type: WidthType.DXA }, columnWidths: W, rows: [
      row("Field", "Value", true),
      row("Incident ID", "INC-2026-1042"),
      row("Report written", "2026-10-23 10:18 UTC"),
      row("Author", "Priya Nair, platform engineer (first responder)"),
      row("Status", "Investigating"),
      row("Severity", "SEV-2 (customer payments failing)"),
      row("Services", "payment-service, order-service"),
    ] }),
    H("1. Summary"),
    P("Since about 10:05 UTC, most checkout payments are failing. payment-service returns error code PAY-401. " +
      "The PaymentFailureRateHigh alert fired at 10:09 UTC. payment-service version 2.4.0 was deployed shortly before (around 10:02 UTC)."),
    H("2. Impact So Far"),
    B("Roughly 3 out of 4 orders end in PAYMENT_FAILED."),
    B("Some payments still succeed. Not yet known which ones."),
    B("Customers see a generic \"payment could not be completed\" message."),
    H("3. Suspected Cause"),
    P("PAY-401 looks like an unauthorized error. My first guess is an authentication or credential problem between " +
      "order-service and payment-service, for example an expired or rotated API key that 2.4.0 now checks more strictly. " +
      "This is not verified yet."),
    H("4. Actions Taken"),
    B("Opened the incident at 10:15 UTC and paged the payments and order-service owners."),
    B("Started an incident call for 10:20 UTC."),
    H("5. Next Steps"),
    B("Check when the order-service to payment-service API key was last rotated."),
    B("Check whether failures are linked to the 2.4.0 deploy."),
    B("Decide whether to roll back."),
    H("6. Open Questions"),
    B("Why do some payments still succeed?"),
    B("Is the latency increase on the order-service dashboard related?"),
  ] }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("docx ok", out); });
