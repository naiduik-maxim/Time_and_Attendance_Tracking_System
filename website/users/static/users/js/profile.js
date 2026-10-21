(() => {
    const modal = document.getElementById('profile-dialog');
    const body = document.getElementById('profile-body');
    let busy = false;
    let profileUrl = '';

    async function load(url, option = {}) {
        if (busy) return;
        busy = true;

        const buttons = [
            ...modal.querySelectorAll('button[type="submit"]')
        ];

        buttons.forEach(button => button.disabled = true);

        try {
            const response = await fetch(url, {
                ...option,
                credentials: 'same-origin'
            });

            if (response.redirected) {
                location.assign(response.url);
                return;
            }

            if (
                !response.headers
                    .get('content-type')
                    ?.includes('application/json')
            ) {
                throw new Error();
            }

            const data = await response.json();

            if(typeof data.html !== 'string'){
                throw new Error();
            }

            body.innerHTML = data.html;
            (body.querySelector('[aria-invalid="true"]') || body.querySelector('summary, input:not([type="hidden"])'))?.focus();
        } catch {
            body.querySelector('[data-load-error]')?.remove();

            const error = document.createElement('p');
            error.dataset.loadError = '';
            error.className = 'alert alert-error';
            error.setAttribute('role', 'alert');
            error.textContent =
                'Не вдалося завантажити профіль. Спробуйте ще раз.';

            body.prepend(error);
            body.querySelector('[data-profile-loading]')?.remove();
        } finally {
            buttons.forEach(button => button.disabled = false);
            busy = false;
        }
    }

    document.addEventListener('click', event => {
        const opener = event.target.closest('[data-profile-url]');
        if (!opener || !modal || busy) return;

        event.preventDefault();
        profileUrl = opener.dataset.profileUrl;
        body.innerHTML = '<div class="profile-card-header profile-loading-header"><h2>Мій профіль</h2><button type="button" class="profile-close-btn" data-profile-close aria-label="Закрити">&times;</button></div><p class="profile-loading" data-profile-loading role="status">Завантаження профілю…</p>';

        if (!modal.open) modal.showModal();

        load(profileUrl);

    });

    document.addEventListener("click", function(event) {
        const closeButton = event.target.closest("[data-profile-close]");

        if (!closeButton) return;

        event.preventDefault();
        event.stopPropagation();

        const dialog = document.getElementById("profile-dialog");

        if (dialog) {
            if (dialog.open) {
                dialog.close();
            } else {
                dialog.removeAttribute("open");
            }
        }
    });

    modal?.addEventListener('submit', event => {
        const form = event.target;

        if (!form.matches('[data-profile-form]')) return;

        event.preventDefault();

        load(form.getAttribute('action') || profileUrl, {
            method: 'POST',
            body: new FormData(form)
            });
        });

    document
        .querySelectorAll('[data-auto-dialog]')
        .forEach(dialog => dialog.showModal());

    document.querySelector('[data-profile-auto]')?.click();
})();
