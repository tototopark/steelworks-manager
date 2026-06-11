document.addEventListener("DOMContentLoaded", function() {
    // Global Login Guard
    const token = localStorage.getItem("admin_token") || localStorage.getItem("auth_token");
    const currentPath = window.location.pathname;
    
    // If no token, and not on login page, redirect to login
    if (!token && currentPath !== "/login.html") {
        window.location.href = "/login.html";
        return;
    }

    const rightLevel = parseInt(localStorage.getItem("right_level")) || 0;

    const navContainer = document.getElementById("main-nav");
    if (!navContainer) return;

    // Define menu items and their required access levels
    // Home, Whiteboard, Holidays, Punch Clock, Admin are available to everyone
    // Admin(10) gets everything.
    const menuItems = [
        { name: "Home", href: "/", allowedLevels: "all" },
        { name: "Jobs", href: "/jobs.html", allowedLevels: [10, 6, 4, 5] },
        { name: "QA Dashboard", href: "/qa_dashboard.html", allowedLevels: [10, 6] },
        { name: "Monthly Notes", href: "/weekly.html", allowedLevels: [10, 6] },
        { name: "Whiteboard", href: "/whiteboard.html", allowedLevels: "all" },
        { name: "Employees", href: "/employees.html", allowedLevels: [10] },
        { name: "Vehicles", href: "/vehicles.html", allowedLevels: [10, 6] }, // Transport might need it too? Only admins for now based on previous rules. Let's make it 10, 6
        { name: "Holidays", href: "/holidays.html", allowedLevels: "all" },
        { name: "Punch Clock", href: "/punch.html", allowedLevels: "all" },
        { name: "Admin", href: "/login.html", allowedLevels: "all", style: "float:right; background:#d9534f;" }
    ];

    let navHtml = `<div class="brand-logo">⚙️ STEELWORKS</div>\n`;

    menuItems.forEach(item => {
        let isAllowed = false;
        
        if (item.allowedLevels === "all") {
            isAllowed = true;
        } else if (Array.isArray(item.allowedLevels) && item.allowedLevels.includes(rightLevel)) {
            isAllowed = true;
        } else if (rightLevel >= 10) { // Admin fallback (Admin is >= 10, e.g. GM is 68)
            isAllowed = true;
        }

        if (isAllowed) {
            // Check if active
            let isActive = false;
            if (item.href === "/") {
                isActive = (currentPath === "/" || currentPath === "/index.html");
            } else {
                isActive = currentPath.includes(item.href);
            }
            
            const activeClass = isActive ? ' class="active"' : '';
            // If it's the admin logout button, place it at the bottom via margin-top
            let extraStyle = "";
            if (item.name === "Admin") {
                extraStyle = ' style="margin-top: auto; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px; color:#f64e60;"';
            }

            navHtml += `<a href="${item.href}"${activeClass}${extraStyle}>${item.name}</a>\n`;
        }
    });

    navContainer.innerHTML = navHtml;
});
