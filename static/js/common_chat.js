let userMenuVisible = false;

function toggleUserMenu() {
    const menu = document.getElementById('userMenu');
    const btn = document.getElementById('menuBtn');

    userMenuVisible = !userMenuVisible;
    menu.classList.toggle('show', userMenuVisible);
    btn.classList.toggle('active', userMenuVisible);
}

document.addEventListener('DOMContentLoaded', () => {

    const menuBtn = document.getElementById('menuBtn');
    if (menuBtn) {
        menuBtn.addEventListener('click', e => {
            e.stopPropagation();
            toggleUserMenu();
        });
    }

    document.addEventListener('click', e => {
        const menu = document.getElementById('userMenu');
        if (menu && userMenuVisible && !menu.contains(e.target)) {
            menu.classList.remove('show');
            userMenuVisible = false;
        }
    });

    /* SEARCH – LOGIC SAME */
    const searchInput = document.getElementById('searchInput');
    const resultsDiv = document.getElementById('searchResults');

    if (!searchInput) return;

    searchInput.addEventListener('input', () => {
        const q = searchInput.value.trim();
        if (!q) {
            resultsDiv.style.display = 'none';
            return;
        }

        fetch(`/api/search-users/?q=${encodeURIComponent(q)}`)
            .then(res => res.json())
            .then(data => {
                resultsDiv.innerHTML = '';
                if (!data.users.length) {
                    resultsDiv.innerHTML =
                        `<div class="dropdown-item">No users found</div>`;
                }2

                // data.users.forEach(user => {
                //     const div = document.createElement('div');
                //     div.className = 'dropdown-item';
                //     div.textContent = user.full_name;
                //     div.onclick = () => location.href = `/start-chat/${user.id}/`;
                //     resultsDiv.appendChild(div);
                // });
                data.users.forEach(user => {
                        const div = document.createElement('div');
                        div.className = 'dropdown-item search-result-item';

                        const avatarHtml = user.profile_image
                        ? `<img src="${user.profile_image}" class="search-avatar-img" alt="">`
                        : `<div class="search-avatar-initials">${user.initials}</div>`;

                    div.innerHTML = `
                        <div class="search-avatar-container">
                            ${avatarHtml}
                            ${user.is_online ? '<div class="online-indicator-small"></div>' : ''}
                        </div>
                        <div class="search-info">
<!--                            <div class="search-name">${user.full_name}</div>-->
                            <div class="search-username">${user.username}</div>
                        </div>
                    `;
                    div.onclick = () => location.href = `/start-chat/${user.id}/`;
                    resultsDiv.appendChild(div);
                });

                resultsDiv.style.display = 'block';
            });
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            resultsDiv.style.display = 'none';
        }
    });
});

