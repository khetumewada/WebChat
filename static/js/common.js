console.log("SCRIPT LOADED");
let userMenuVisible = false;

function toggleUserMenu() {
    const menu = document.getElementById('userMenu');
    const menuBtn = document.getElementById('menuBtn');

    if (!menu) {
        console.error('Menu element not found');
        return;
    }

    userMenuVisible = !userMenuVisible;

    if (userMenuVisible) {
        menu.classList.add('show');
        menuBtn.style.background = 'rgba(255,255,255,0.2)';
    } else {
        menu.classList.remove('show');
        menuBtn.style.background = 'transparent';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM loaded, initializing menu');

    // Ensure menu button works
    const menuBtn = document.getElementById('menuBtn');
    if (menuBtn) {
        menuBtn.addEventListener('click', function (e) {
            console.log('clicked');
            e.preventDefault();
            e.stopPropagation();
            toggleUserMenu();
        });
    }

    // Close menu when clicking outside
    document.addEventListener('click', function (e) {
        const menu = document.getElementById('userMenu');
        const menuBtn = document.getElementById('menuBtn');

        if (menu && menuBtn && !menu.contains(e.target) && !menuBtn.contains(e.target) && userMenuVisible) {
            menu.classList.remove('show');
            menuBtn.style.background = 'transparent';
            userMenuVisible = false;
        }
    });

    // Close menu with Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && userMenuVisible) {
            const menu = document.getElementById('userMenu');
            const menuBtn = document.getElementById('menuBtn');
            if (menu) {
                menu.classList.remove('show');
                menuBtn.style.background = 'transparent';
                userMenuVisible = false;
            }
        }
    });
});

// Enhanced search functionality
document.getElementById('searchInput').addEventListener('input', function () {
    const query = this.value.trim();
    const resultsDiv = document.getElementById('searchResults');

    if (query.length > 0) {
        fetch(`/api/search-users/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                resultsDiv.innerHTML = '';

                if (data.users.length > 0) {
                    data.users.forEach(user => {
                        const userDiv = document.createElement('div');
                        userDiv.style.cssText = 'display: flex; align-items: center; padding: 12px 16px; cursor: pointer; border-bottom: 1px solid var(--border-color); transition: var(--transition);';

                        const colors = [
                            "linear-gradient(135deg, #ff6b6b, #ee5a24)",
                            "linear-gradient(135deg, #a29bfe, #6c5ce7)",
                            "linear-gradient(135deg, #fd79a8, #e84393)",
                            "linear-gradient(135deg, #fdcb6e, #e17055)",
                            "linear-gradient(135deg, #74b9ff, #0984e3)",
                            "linear-gradient(135deg, #55a3ff, #3742fa)",
                            "linear-gradient(135deg, #26de81, #20bf6b)",
                            "linear-gradient(135deg, #f7b731, #fa8231)",
                        ];
                        const avatarColor = colors[user.id % colors.length];

                        userDiv.innerHTML = `
                            <div style="width: 40px; height: 40px; border-radius: 50%; background: ${avatarColor}; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; margin-right: 12px; position: relative; box-shadow: 0 2px 8px rgba(0,0,0,0.1); font-size: 14px;">
                                ${user.initials}
                                ${user.is_online ? '<div style="width: 12px; height: 12px; background-color: var(--secondary-color); border-radius: 50%; border: 2px solid white; position: absolute; bottom: 0; right: 0;"></div>' : ''}
                            </div>
                            <div style="flex: 1;">
                                <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 2px; font-size: 13px;">${user.full_name}</div>
                                <div style="font-size: 11px; color: var(--text-secondary);">@${user.username} ${user.is_online ? '• <span style="color: var(--secondary-color);">Online</span>' : ''}</div>
                            </div>
                        `;

                        userDiv.addEventListener('mouseenter', () => {
                            userDiv.style.backgroundColor = 'var(--hover-color)';
                        });
                        userDiv.addEventListener('mouseleave', () => {
                            userDiv.style.backgroundColor = 'transparent';
                        });
                        userDiv.addEventListener('click', () => {
                            window.location.href = `/start-chat/${user.id}/`;
                        });

                        resultsDiv.appendChild(userDiv);
                    });
                    resultsDiv.style.display = 'block';
                } else {
                    resultsDiv.innerHTML = '<div style="padding: 24px; text-align: center; color: var(--text-secondary); font-size: 12px;">No users found</div>';
                    resultsDiv.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Search error:', error);
                resultsDiv.innerHTML = '<div style="padding: 24px; text-align: center; color: #ff6b6b; font-size: 12px;">Search failed. Please try again.</div>';
                resultsDiv.style.display = 'block';
            });
    } else {
        resultsDiv.style.display = 'none';
    }
});

// Hide search results when clicking outside
document.addEventListener('click', function (e) {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');

    if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.style.display = 'none';
    }
});

// Clear search when pressing Escape
document.getElementById('searchInput').addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        this.value = '';
        document.getElementById('searchResults').style.display = 'none';
    }
});
