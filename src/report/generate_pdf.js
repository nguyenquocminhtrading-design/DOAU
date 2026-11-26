/**
 * DOAU Management Report – PDF Generator
 * Uses wkhtmltopdf (must be installed and available on PATH)
 * Usage: node generate_pdf.js
 */
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const outputDir = path.resolve(__dirname, '..', '..', 'reports', 'generated');
const htmlFile = path.join(outputDir, 'DOAU_Management_Report_Oct2026.html');
const pdfFile = path.join(outputDir, 'DOAU_Management_Report_Oct2026.pdf');

if (!fs.existsSync(htmlFile)) {
  console.error('HTML file not found. Generate the HTML report first.');
  process.exit(1);
}

console.log('Generating PDF via wkhtmltopdf...');
const cmd = [
  'wkhtmltopdf',
  '--page-size A4',
  '--orientation Portrait',
  '--margin-top 0mm --margin-bottom 0mm --margin-left 0mm --margin-right 0mm',
  '--enable-local-file-access',
  '--dpi 150',
  '--javascript-delay 300',
  `"file://${htmlFile}"`,
  `"${pdfFile}"`
].join(' ');

try {
  execSync(cmd, { stdio: 'inherit' });
  const size = fs.statSync(pdfFile).size;
  console.log(`PDF generated: ${pdfFile} (${(size/1024).toFixed(1)} KB)`);
} catch (err) {
  console.error('wkhtmltopdf failed:', err.message);
  process.exit(1);
}
