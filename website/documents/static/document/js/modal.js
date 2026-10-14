
const COUNT_ONLY_WEEKDAYS = true; // true — робочі дні, false — календарні

function openModal() {
    const modal = document.getElementById("documentModal");
    if (modal) modal.classList.add("active");
}

function closeModal() {
    const modal = document.getElementById("documentModal");
    if (modal) modal.classList.remove("active");

    document.querySelectorAll(".error-msg").forEach(el => {
        el.classList.remove("show");
    });
}

window.addEventListener("click", function(event) {
    const modal = document.getElementById("documentModal");

    if (modal && event.target === modal) {
        closeModal();
    }
});

document.addEventListener("DOMContentLoaded", function() {

    // ==========================================
    // 1. ОТРИМАННЯ HTML-ЕЛЕМЕНТІВ
    // ==========================================

    const dateStartInput = document.getElementById("id_date_start");
    const dateEndInput = document.getElementById("id_date_end");
    const countDayInput = document.getElementById("id_count_day");

    const docForm = document.querySelector("#documentModal form");
    const formEl = document.getElementById("documentForm") || docForm;

    const typeInput = document.getElementById("id_type_missing");
    const limitWarning = document.getElementById("limit-warning");

    const filterTypeSelect = document.getElementById("filterType");
    const tbody = document.getElementById("documentTableBody");
    const sortableHeaders = document.querySelectorAll("th.sortable");

    let vacationLeft = parseInt(
        formEl?.getAttribute("data-vacation-left") || "0", 10
    ) || 0;

    let sickLeft = parseInt(
        formEl?.getAttribute("data-sick-left") || "0", 10
    ) || 0;


    // ==========================================
    // 2. ФІЛЬТРАЦІЯ ДОКУМЕНТІВ
    // ==========================================

    if (filterTypeSelect && typeInput) {
        Array.from(typeInput.options).forEach(option => {
            if (!option.value) return;

            const name = option.text.trim();

            const exists = Array.from(filterTypeSelect.options)
                .some(opt => opt.value === name);

            if (!exists) {
                const newOption = document.createElement("option");
                newOption.value = name;
                newOption.textContent = name;

                filterTypeSelect.appendChild(newOption);
            }
        });
    }

    if (filterTypeSelect && tbody) {
        filterTypeSelect.addEventListener("change", function() {
            const selected = this.value;

            tbody.querySelectorAll("tr").forEach(row => {
                if (!row.cells.length) return;

                const type = row.cells[0].textContent.trim();

                row.style.display =
                    selected === "all" || selected === type
                        ? ""
                        : "none";
            });
        });
    }


    // ==========================================
    // 3. СОРТУВАННЯ ТАБЛИЦІ
    // ==========================================

    function parseTableDate(value) {
        const parts = value.trim().split(".");

        if (parts.length !== 3) return 0;

        const [day, month, year] = parts.map(Number);

        return Date.UTC(year, month - 1, day);
    }

    sortableHeaders.forEach(header => {
        header.addEventListener("click", function() {

            if (!tbody) return;

            const colIndex = Number(this.dataset.column);
            const dataType = this.dataset.type;

            const currentOrder = this.dataset.order;
            const newOrder = currentOrder === "asc" ? "desc" : "asc";

            sortableHeaders.forEach(item => {
                item.removeAttribute("data-order");

                const icon = item.querySelector(".sort-icon");

                if (icon) icon.textContent = "↕";
            });

            this.dataset.order = newOrder;

            const currentIcon = this.querySelector(".sort-icon");

            if (currentIcon) {
                currentIcon.textContent =
                    newOrder === "asc" ? "↑" : "↓";
            }

            const rows = Array.from(tbody.querySelectorAll("tr"));

            rows.sort((rowA, rowB) => {
                const cellA = rowA.cells[colIndex];
                const cellB = rowB.cells[colIndex];

                if (!cellA || !cellB) return 0;

                let valueA = cellA.textContent.trim();
                let valueB = cellB.textContent.trim();

                if (dataType === "number") {
                    valueA = Number(valueA) || 0;
                    valueB = Number(valueB) || 0;
                } else if (dataType === "date") {
                    valueA = parseTableDate(valueA);
                    valueB = parseTableDate(valueB);
                } else {
                    valueA = valueA.toLocaleLowerCase("uk");
                    valueB = valueB.toLocaleLowerCase("uk");
                }

                if (valueA < valueB) {
                    return newOrder === "asc" ? -1 : 1;
                }

                if (valueA > valueB) {
                    return newOrder === "asc" ? 1 : -1;
                }

                return 0;
            });

            rows.forEach(row => tbody.appendChild(row));
        });
    });


    // ==========================================
    // 4. ПЕРЕВІРКА ЛІМІТІВ ВІДСУТНОСТІ
    // ==========================================

    function checkLimits() {
        if (!typeInput || !countDayInput || !limitWarning) return;

        const selectedOption = typeInput.options[
            typeInput.selectedIndex
        ];

        const selectedType = selectedOption
            ? selectedOption.text.trim().toLowerCase()
            : "";

        const requestedDays = Number(countDayInput.value) || 0;

        let warningText = "";

        if (
            ["vacation", "відпустка"].includes(selectedType)
            && requestedDays > vacationLeft
        ) {
            const exceeded = requestedDays - vacationLeft;

            warningText =
                `⚠ У вас залишилося ${vacationLeft} дн. ` +
                `оплачуваної відпустки. Перевищення: ` +
                `${exceeded} дн.`;

        } else if (
            ["hospital", "лікарняний"].includes(selectedType)
            && requestedDays > sickLeft
        ) {
            warningText =
                `⚠ Залишок оплачуваних лікарняних — ` +
                `${sickLeft} дн.`;
        }

        limitWarning.textContent = warningText;

        if (warningText) {
            limitWarning.style.maxHeight = "100px";
            limitWarning.style.opacity = "1";
            limitWarning.style.marginTop = "10px";
        } else {
            limitWarning.style.maxHeight = "0";
            limitWarning.style.opacity = "0";
            limitWarning.style.marginTop = "0";
        }
    }

    if (typeInput) {
        typeInput.addEventListener("change", checkLimits);
    }


    // ==========================================
    // 5. ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ ДАТ
    // ==========================================

    // Перетворюємо YYYY-MM-DD у UTC Date.
    function readDate(value) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) {
            return null;
        }

        const [year, month, day] = value.split("-").map(Number);

        const result = new Date(
            Date.UTC(year, month - 1, day)
        );

        // Перевірка некоректних дат.
        if (
            result.getUTCFullYear() !== year ||
            result.getUTCMonth() !== month - 1 ||
            result.getUTCDate() !== day
        ) {
            return null;
        }

        return result;
    }

    // Перетворюємо дату назад у YYYY-MM-DD.
    function formatDate(date) {
        const year = date.getUTCFullYear();

        const month = String(
            date.getUTCMonth() + 1
        ).padStart(2, "0");

        const day = String(
            date.getUTCDate()
        ).padStart(2, "0");

        return `${year}-${month}-${day}`;
    }

    // Перевіряємо, чи враховувати день.
    function isCountedDay(date) {
        if (!COUNT_ONLY_WEEKDAYS) return true;

        const weekday = date.getUTCDay();

        // 0 — неділя, 6 — субота.
        return weekday !== 0 && weekday !== 6;
    }

    // Рахуємо кількість днів між двома датами включно.
    function countDays(start, end) {
        if (!start || !end || end < start) {
            return 0;
        }

        let total = 0;

        const current = new Date(start.getTime());

        while (current <= end) {
            if (isCountedDay(current)) {
                total++;
            }

            current.setUTCDate(current.getUTCDate() + 1);
        }

        return total;
    }

    // Знаходимо кінцеву дату за кількістю днів.
    function endDateForCount(start, days) {
        if (
            !start ||
            !Number.isInteger(days) ||
            days < 1
        ) {
            return null;
        }

        const current = new Date(start.getTime());

        let remaining = days;

        while (remaining > 0) {
            if (isCountedDay(current)) {
                remaining--;
            }

            if (remaining > 0) {
                current.setUTCDate(
                    current.getUTCDate() + 1
                );
            }
        }

        return current;
    }


    // ==========================================
    // 6. ІНІЦІАЛІЗАЦІЯ КАЛЕНДАРІВ
    // ==========================================

    if (!dateStartInput || !dateEndInput || !countDayInput) {
        console.warn("Поля дат або кількості днів не знайдено.");
        return;
    }

    if (typeof flatpickr !== "function") {
        console.error(
            "Flatpickr не завантажено. " +
            "Перевір підключення бібліотеки."
        );
        return;
    }

    // Мінімальна дата — 14 днів тому.
    const minDateObject = new Date();

    minDateObject.setDate(
        minDateObject.getDate() - 14
    );

    const minDateStr = [
        minDateObject.getFullYear(),
        String(minDateObject.getMonth() + 1).padStart(2, "0"),
        String(minDateObject.getDate()).padStart(2, "0")
    ].join("-");


    // ==========================================
    // 7. ЗАВАНТАЖЕННЯ ЗАЙНЯТИХ ДАТ
    // ==========================================

    let bookedDates = [];

    try {
        const bookedDatesStr =
            formEl?.getAttribute("data-booked-dates") || "[]";

        bookedDates = JSON.parse(bookedDatesStr);

        if (!Array.isArray(bookedDates)) {
            bookedDates = [];
        }

    } catch (error) {
        console.error(
            "Помилка обробки зайнятих дат:",
            error
        );

        bookedDates = [];
    }

    const disableRanges = bookedDates.map(range => ({
        from: range.start,
        to: range.end
    }));


    // ==========================================
    // 8. FLATPICKR
    // ==========================================

    const fpEnd = flatpickr(dateEndInput, {
        dateFormat: "Y-m-d",
        locale: "uk",
        minDate: minDateStr,
        disable: disableRanges,

        onChange: function() {
            updateDaysFromDates();
        }
    });

    const fpStart = flatpickr(dateStartInput, {
        dateFormat: "Y-m-d",
        locale: "uk",
        minDate: minDateStr,
        disable: disableRanges,

        onChange: function() {
            onStartDateChanged();
        }
    });


    // ==========================================
    // 9. РОЗРАХУНОК КІЛЬКОСТІ ДНІВ
    // ==========================================

    function updateDaysFromDates() {
        const start = readDate(dateStartInput.value);
        const end = readDate(dateEndInput.value);

        if (!start || !end) {
            countDayInput.value = "";
            checkLimits();
            return;
        }

        if (end < start) {
            countDayInput.value = "";
            checkLimits();
            return;
        }

        const days = countDays(start, end);

        countDayInput.value = days > 0 ? days : "";

        checkLimits();
    }


    // ==========================================
    // 10. РОЗРАХУНОК КІНЦЕВОЇ ДАТИ
    // ==========================================

    function updateEndDateFromDays() {
        const start = readDate(dateStartInput.value);

        const days = Number(countDayInput.value);

        if (
            !start ||
            countDayInput.value === "" ||
            !Number.isInteger(days) ||
            days < 1
        ) {
            fpEnd.clear(false);
            checkLimits();
            return;
        }

        const end = endDateForCount(start, days);

        if (!end) return;

        const formattedEnd = formatDate(end);

        // false — не викликає onChange повторно.
        fpEnd.setDate(formattedEnd, false);

        // Якщо дата заблокована Flatpickr,
        // він може не дозволити її встановити.
        if (dateEndInput.value !== formattedEnd) {
            countDayInput.setCustomValidity(
                "Розрахована кінцева дата недоступна."
            );
        } else {
            countDayInput.setCustomValidity("");
        }

        checkLimits();
    }


    // ==========================================
    // 11. ЗМІНА ПОЧАТКОВОЇ ДАТИ
    // ==========================================

    function onStartDateChanged() {
        const start = readDate(dateStartInput.value);

        if (!start) {
            fpEnd.clear(false);
            countDayInput.value = "";
            checkLimits();
            return;
        }

        fpEnd.set(
            "minDate",
            formatDate(start) > minDateStr
                ? formatDate(start)
                : minDateStr
        );

        if (
            countDayInput.value &&
            Number(countDayInput.value) > 0
        ) {
            // Кількість введена — оновлюємо кінцеву дату.
            updateEndDateFromDays();

        } else {
            const end = readDate(dateEndInput.value);

            if (end && end >= start) {
                updateDaysFromDates();
            } else {
                fpEnd.clear(false);
            }
        }
    }


    // ==========================================
    // 12. ОБРОБНИКИ ВВЕДЕННЯ
    // ==========================================

    countDayInput.addEventListener("input", function() {
        this.setCustomValidity("");
        updateEndDateFromDays();
    });

    countDayInput.addEventListener("change", function() {
        if (
            this.value !== "" &&
            Number(this.value) < 1
        ) {
            this.value = "1";
        }

        updateEndDateFromDays();
    });

    // Підтримка ручного введення дат.
    dateStartInput.addEventListener("change", function() {
        if (readDate(this.value)) {
            onStartDateChanged();
        }
    });

    dateEndInput.addEventListener("change", function() {
        updateDaysFromDates();
    });

    // Якщо значення вже задані під час відкриття сторінки.
    if (dateStartInput.value) {
        fpEnd.set("minDate", dateStartInput.value);

        if (dateEndInput.value) {
            updateDaysFromDates();

        } else if (countDayInput.value) {
            updateEndDateFromDays();
        }
    }


    // ==========================================
    // 13. ВАЛІДАЦІЯ ФОРМИ
    // ==========================================

    function showError(id, message) {
        const element = document.getElementById(id);

        if (element) {
            element.textContent = message;
            element.classList.add("show");
        }
    }

    function clearErrors() {
        document.querySelectorAll(".error-msg").forEach(el => {
            el.classList.remove("show");
        });
    }

    if (!docForm) return;

    docForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        clearErrors();

        let isValid = true;

        // Перевірка типу відсутності.
        if (!typeInput || !typeInput.value) {
            showError(
                "error_type_missing",
                "⚠ Будь ласка, оберіть причину."
            );

            isValid = false;
        }

        // Перевірка опису.
        const descInput = document.getElementById("id_description");

        if (descInput && !descInput.value.trim()) {
            showError(
                "error_description",
                "⚠ Заповніть опис."
            );

            isValid = false;
        }

        const start = readDate(dateStartInput.value);
        const end = readDate(dateEndInput.value);

        if (!start) {
            showError(
                "error_date_start",
                "⚠ Оберіть дату початку."
            );

            isValid = false;
        }

        if (!end) {
            showError(
                "error_date_end",
                "⚠ Оберіть кінцеву дату."
            );

            isValid = false;
        }

        if (start && end && end < start) {
            showError(
                "error_date_end",
                "⚠ Кінцева дата не може бути раніше початкової."
            );

            isValid = false;
        }

        if (start && end && end >= start) {
            const calculatedDays = countDays(start, end);

            if (calculatedDays < 1) {
                showError(
                    "error_count_day",
                    "⚠ За цей період немає робочих днів."
                );

                isValid = false;
            } else {
                countDayInput.value = calculatedDays;
            }
        }

        if (
            !countDayInput.value ||
            Number(countDayInput.value) < 1
        ) {
            showError(
                "error_count_day",
                "⚠ Мінімальна кількість днів — 1."
            );

            isValid = false;
        }

        if (!isValid) return;

        const submitButton = docForm.querySelector(
            'button[type="submit"]'
        );

        if (submitButton) submitButton.disabled = true;

        try {
            const formData = new FormData(docForm);

            const response = await fetch(docForm.action, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            });

            const data = await response.json();

            if (!response.ok || data.status !== "success") {
                if (data.errors) {
                    Object.entries(data.errors).forEach(
                        ([field, messages]) => {
                            const text = Array.isArray(messages)
                                ? messages[0]
                                : messages;

                            showError(
                                `error_${field}`,
                                `⚠ ${text}`
                            );
                        }
                    );
                } else {
                    console.error(
                        "Сервер повернув помилку:",
                        data
                    );
                }

                return;
            }

            // ==========================================
            // 14. ДОДАВАННЯ ДОКУМЕНТА В ТАБЛИЦЮ
            // ==========================================

            const doc = data.document;

            const table = document.getElementById("documentTable");
            const tbody = document.getElementById("documentTableBody");
            const noDocsMsg = document.getElementById("noDocumuentMsg");

            if (noDocsMsg) {
                noDocsMsg.style.display = "none";
            }

            if (table) {
                table.style.display = "table";
            }

            if (tbody) {
                const newRow = document.createElement("tr");

                [
                    doc.type_missing,
                    doc.date_start_display,
                    doc.date_end_display,
                    doc.count_day,
                    doc.description
                ].forEach(value => {
                    const cell = document.createElement("td");
                    cell.textContent = value ?? "";
                    newRow.appendChild(cell);
                });

                tbody.prepend(newRow);

                // Скидаємо фільтр, щоб новий документ був видимий.
                const filter = document.getElementById("filterType");

                if (filter) {
                    filter.value = "all";
                    filter.dispatchEvent(new Event("change"));
                }
            } else {
                console.error("Не знайдено #documentTableBody");
            }


            // ==========================================
            // 15. ОНОВЛЕННЯ ЗАЙНЯТИХ ДАТ
            // ==========================================

            disableRanges.push({
                from: doc.date_start_raw,
                to: doc.date_end_raw
            });

            fpStart.set("disable", disableRanges);
            fpEnd.set("disable", disableRanges);


            // ==========================================
            // 16. ОНОВЛЕННЯ ЛІМІТІВ
            // ==========================================

            const daysUsed = Number(doc.count_day) || 0;

            const typeName = String(
                doc.type_missing || ""
            ).trim().toLowerCase();

            if (["vacation", "відпустка"].includes(typeName)) {
                vacationLeft = Math.max(
                    0,
                    vacationLeft - daysUsed
                );

            } else if (
                ["hospital", "лікарняний"].includes(typeName)
            ) {
                sickLeft = Math.max(
                    0,
                    sickLeft - daysUsed
                );
            }


            // ==========================================
            // 17. ОЧИЩЕННЯ ФОРМИ
            // ==========================================

            docForm.reset();

            fpStart.clear(false);
            fpEnd.clear(false);

            countDayInput.setCustomValidity("");

            checkLimits();
            clearErrors();
            closeModal();

        } catch (error) {
            console.error(
                "Помилка під час збереження документа:",
                error
            );

        } finally {
            if (submitButton) {
                submitButton.disabled = false;
            }
        }
    });
});
