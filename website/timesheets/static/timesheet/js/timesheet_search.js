document.addEventListener("DOMContentLoaded", function () {

    const searchInput = document.getElementById("worker-search");
    const table = document.getElementById("workers-table");

    const resultCount = document.getElementById(
        "search-result-count"
    );

    const noResults = document.getElementById(
        "search-no-results"
    );

    if (!searchInput || !table) {
        console.error("Не знайдено поле пошуку або таблицю!");
        return;
    }

    const rows = Array.from(
        table.querySelectorAll(".timesheet-worker-row")
    );

    function normalizeText(value) {
        return String(value)
            .toLocaleLowerCase("uk-UA")
            .replace(/\s+/g, " ")
            .trim();
    }

    function filterWorkers() {
        const query = normalizeText(searchInput.value);
        const words = query.split(" ").filter(Boolean);

        let visibleCount = 0;

        rows.forEach(row => {
            const workerData = normalizeText(
                row.dataset.search || ""
            );

            const matches = words.every(word =>
                workerData.includes(word)
            );

            row.hidden = !matches;
            row.style.display = matches ? "" : "none";

            if (matches) {
                visibleCount++;
            }
        });

        if (resultCount) {
            resultCount.textContent =
                `Знайдено: ${visibleCount} із ${rows.length}`;
        }

        if (noResults) {
            const showNoResults =
                visibleCount === 0 && rows.length > 0;

            noResults.hidden = !showNoResults;
            noResults.style.display = showNoResults ? "" : "none";
        }
    }

    searchInput.addEventListener("input", filterWorkers);
    searchInput.addEventListener("search", filterWorkers);

    filterWorkers();

    console.log(
        `Пошук ініціалізовано. Працівників: ${rows.length}`
    );
});