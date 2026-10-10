(() => {
    const modal = document.getElementById('profile-dialog');
    const body = document.getElementById('profile-body');
    let busy = false;

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
            body.querySelector('summary, input')?.focus();
        } catch {
            body.querySelector('[data-load-error]')?.remove();

            const error = document.createElement('p');
            error.dataset.loadError = '';
            error.setAttribute('role', 'alert');
            error.textContent =
                'Не вдалося завантажити профіль. Спробуйте ще раз.';

            body.prepend(error);
        } finally {
            buttons.forEach(button => button.disabled = false);
            busy = false;
        }
    }

    document.addEventListener('click', event => {
        const opener = event.target.closest('[data-profile-url]');
        if (!opener || !modal) return;

        event.preventDefault();
        body.textContent = 'Завантаження...';

        if (!modal.open) modal.showModal();

        load(opener.dataset.profileUrl);

    });

    modal?.querySelector('[data-profile-close]')
    .addEventListener('click', () => modal.close());

    modal?.addEventListener('submit', event => {
        const form = event.target;

        if (!form.matches('[data-profile-form]')) return;

        event.preventDefault();

        load(form.getAttribute('action'), {
            method: 'POST',
            body: new FormData(form)
            });
        });

    document
        .querySelectorAll('[data-auto-dialog]')
        .forEach(dialog => dialog.showModal());

    document.querySelector('[data-profile-auto]')?.click();
})();