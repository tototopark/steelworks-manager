const fs = require('fs');
const path = require('path');

const dir = 'f:/pe/public_html/steelworks-manager/static';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.html'));

files.forEach(file => {
    const p = path.join(dir, file);
    let html = fs.readFileSync(p, 'utf8');

    // Remove the dashboard-container rule
    html = html.replace(/^[ \t]*\.dashboard-container\s*\{[^}]+\}\s*[\r\n]+/gm, '');

    // Remove the nav-menu rules
    html = html.replace(/^[ \t]*\.nav-menu\s*\{[^}]+\}\s*[\r\n]+/gm, '');
    html = html.replace(/^[ \t]*\.nav-menu\s+a\s*\{[^}]+\}\s*[\r\n]+/gm, '');
    html = html.replace(/^[ \t]*\.nav-menu\s+a\.active,\s*\.nav-menu\s+a:hover\s*\{[^}]+\}\s*[\r\n]+/gm, '');
    html = html.replace(/^[ \t]*\.nav-menu\s+a:hover\s*\{[^}]+\}\s*[\r\n]+/gm, '');

    fs.writeFileSync(p, html, 'utf8');
});
console.log('Removed inline container and nav styles');
