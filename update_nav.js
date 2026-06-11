const fs = require('fs');
const path = require('path');

const dir = 'f:/pe/public_html/steelworks-manager/static';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.html'));

files.forEach(file => {
    const p = path.join(dir, file);
    let html = fs.readFileSync(p, 'utf8');

    // Skip login as it doesn't need nav (well, it didn't have one)
    if (file === 'login.html') return;

    // We want to replace the whole <div class="nav-menu"...>...</div> block
    // with <div class="nav-menu" id="main-nav"></div>
    const regex = /<div class="nav-menu"( id="main-nav")?>[\s\S]*?<\/div>/;
    
    if (regex.test(html)) {
        html = html.replace(regex, '<div class="nav-menu" id="main-nav"></div>');
        
        // Add script before </body>
        if (!html.includes('<script src="/js/nav.js"></script>')) {
            html = html.replace('</body>', '<script src="/js/nav.js"></script>\n</body>');
        }

        fs.writeFileSync(p, html, 'utf8');
        console.log('Updated ' + file);
    }
});
