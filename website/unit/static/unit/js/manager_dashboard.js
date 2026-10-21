document.addEventListener('DOMContentLoaded', () => {
    const page = document.querySelector('.manager-page');
    if (!page) return;

    const normalize = (value) => value.normalize('NFKC').toLocaleLowerCase('uk-UA').trim().replace(/\s+/g, ' ');

    const setupSearch = ({ inputId, itemSelector, countId, emptyId, listId, noun }) => {
        const input = document.getElementById(inputId);
        if (!input) return;

        const items = [...page.querySelectorAll(itemSelector)];
        const count = document.getElementById(countId);
        const empty = document.getElementById(emptyId);
        const list = listId ? document.getElementById(listId) : null;
        const haystacks = items.map((item) => normalize(item.dataset.search || item.textContent));

        const update = () => {
            const query = normalize(input.value);
            const terms = query ? query.split(' ') : [];
            let visible = 0;

            items.forEach((item, index) => {
                const matches = terms.every((term) => haystacks[index].includes(term));
                item.hidden = !matches;
                if (matches) visible += 1;
            });

            if (count) count.textContent = query ? `Знайдено: ${visible} із ${items.length}` : `${noun}: ${items.length}`;
            if (empty) empty.hidden = !query || visible !== 0 || items.length === 0;
            if (list) list.hidden = Boolean(query && visible === 0 && items.length > 0);
        };

        input.addEventListener('input', update);
        update();
    };

    setupSearch({
        inputId: 'department-search',
        itemSelector: '[data-department-card]',
        countId: 'department-search-count',
        emptyId: 'department-no-results',
        listId: null,
        noun: 'Підрозділів',
    });
    setupSearch({
        inputId: 'worker-search',
        itemSelector: '[data-worker-row]',
        countId: 'worker-search-count',
        emptyId: 'worker-no-results',
        listId: 'worker-table-wrapper',
        noun: 'Працівників',
    });

    const openModal = (id) => {
        const dialog = document.getElementById(id);
        if (!dialog || typeof dialog.showModal !== 'function') return false;
        if (!dialog.open) dialog.showModal();
        const firstField = dialog.querySelector('[aria-invalid="true"]') || dialog.querySelector('[data-modal-focus]') || dialog.querySelector('input:not([type="hidden"]), select, textarea');
        if (firstField) firstField.focus();
        return true;
    };

    page.querySelectorAll('a[data-open-modal], button[data-open-modal]').forEach((trigger) => {
        trigger.addEventListener('click', (event) => {
            if (openModal(trigger.dataset.openModal)) event.preventDefault();
        });
    });

    page.querySelectorAll('.manager-modal').forEach((dialog) => {
        dialog.querySelectorAll('[data-close-modal]').forEach((button) => {
            button.addEventListener('click', () => dialog.close());
        });
        dialog.addEventListener('click', (event) => {
            if (event.target === dialog) dialog.close();
        });
    });

    if (page.dataset.openModal) openModal(page.dataset.openModal);
});
