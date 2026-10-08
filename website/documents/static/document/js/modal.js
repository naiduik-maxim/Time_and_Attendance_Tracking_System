function openModal(){
    document.getElementById('documentModal').classList.add('active');
}

function closeModal(){
    document.getElementById('documentModal').classList.remove('active');
    document.querySelectorAll('.error-msg').forEach(el => el.classList.remove('show'));
}

window.onclick = function(event) {
    let modal = document.getElementById('documentModal');
    if (event.target === modal){
        closeModal();
    }
}

document.addEventListener("DOMContentLoaded", function(){
    const dateStartInput = document.getElementById('id_date_start');
    const dateEndInput = document.getElementById('id_date_end');
    const countDayInput = document.getElementById('id_count_day');
    const docForm = document.querySelector('#documentModal form');
    const typeInput = document.getElementById('id_type_missing');
    const limitWarning = document.getElementById('limit-warning');
    const formEl = document.getElementById('documentForm');
    if (!formEl) return;

    let vacationLeft = parseInt(formEl.getAttribute('data-vacation-left')) || 0;
    let sickLeft = parseInt(formEl.getAttribute('data-sick-left')) || 0;

    function checkLimits() {
        if (!typeInput || !countDayInput || !limitWarning) return;
        
        const selectedType = typeInput.options[typeInput.selectedIndex].text; 
        const requestedDays = parseInt(countDayInput.value) || 0;
        
        let warningText = '';

        if (selectedType === 'vacation' && requestedDays > vacationLeft) {
            warningText = `⚠ Увага: У вас залишилося ${vacationLeft} дн. оплачуваної відпустки. Перевищення (${requestedDays - vacationLeft} дн.) буде за власний рахунок.`;
        } else if (selectedType === 'hospital' && requestedDays > sickLeft) {
            warningText = `⚠ Увага: Залишок оплачуваних лікарняних — ${sickLeft} дн.`;
        }

        if (warningText) {
            limitWarning.textContent = warningText;
            limitWarning.style.maxHeight = '40px';
            limitWarning.style.opacity = '1';
            limitWarning.style.marginTop = '10px';
        } else {
            limitWarning.style.maxHeight = '0';
            limitWarning.style.opacity = '0';
            limitWarning.style.marginTop = '0';
        }
    }

    if (typeInput) typeInput.addEventListener('change', checkLimits);
    if (countDayInput) {
        countDayInput.addEventListener('input', checkLimits);
        countDayInput.addEventListener('change', checkLimits);
    }

    if (dateStartInput && dateEndInput && countDayInput) {

        // 1. Визначаємо мінімальну дату (2 тижні тому)
        const minDateObj = new Date();
        minDateObj.setDate(minDateObj.getDate() - 14);
        const minYear = minDateObj.getFullYear();
        const minMonth = String(minDateObj.getMonth() + 1).padStart(2, '0');
        const minDay = String(minDateObj.getDate()).padStart(2, '0'); 
        const minDateStr = `${minYear}-${minMonth}-${minDay}`;

        // 2. Готуємо зайняті дати для Flatpickr (формат from/to)
        const bookedDatesStr = formEl.getAttribute('data-booked-dates');
        const bookedDates = JSON.parse(bookedDatesStr || '[]');
        const disableRanges = bookedDates.map(range => ({
            from: range.start,
            to: range.end
        }));

        // 3. Функція перерахунку днів
        function calculateDays() {
            if(dateStartInput.value && dateEndInput.value){
                const start = new Date(dateStartInput.value);
                const end = new Date(dateEndInput.value);
                if (end >= start){
                    const diffTime = end - start;
                    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24)) + 1;
                    countDayInput.value = diffDays;
                    checkLimits(); // Перевіряємо ліміти при автоматичній зміні
                } else {
                    countDayInput.value = ''; 
                }
            }
        }

        // 4. Ініціалізуємо Flatpickr для дати початку
        const fpStart = flatpickr(dateStartInput, {
            dateFormat: "Y-m-d",
            locale: "uk",
            minDate: minDateStr,
            disable: disableRanges,
            onChange: function(selectedDates, dateStr) {
                fpEnd.set('minDate', dateStr);
                calculateDays();
            }
        });

        // 5. Ініціалізуємо Flatpickr для дати кінця
        const fpEnd = flatpickr(dateEndInput, {
            dateFormat: "Y-m-d",
            locale: "uk",
            minDate: minDateStr,
            disable: disableRanges,
            onChange: function() {
                calculateDays();
            }
        });

        // 6. Розрахунок кінцевої дати, якщо кількість днів ввели вручну
        function calculateEndDate(event){
            if (event && !event.isTrusted) return;

            if(dateStartInput.value && countDayInput.value){
                const start = new Date(dateStartInput.value);
                const days = parseInt(countDayInput.value, 10);

                if (days > 0){
                    start.setDate(start.getDate() + (days -1));
                }

                const year = start.getFullYear();
                const month = String(start.getMonth() + 1).padStart(2, '0');
                const day = String(start.getDate()).padStart(2, '0');
                const calcEnd = `${year}-${month}-${day}`;
                
                fpEnd.setDate(calcEnd, true); 
            }
        }

        countDayInput.addEventListener('input', calculateEndDate);
        countDayInput.addEventListener('change', function(event) {
            if (this.value !== '' && parseInt(this.value, 10) < 1) {
                this.value = 1;
                calculateEndDate(event); 
            }
        });

        // 7. Валідація перед відправкою форми
        if (docForm) {
            docForm.addEventListener('submit', function(event){
                event.preventDefault();
                let isValid = true;

                document.querySelectorAll('.error-msg').forEach(el => el.classList.remove('show'));

                function showError(id, message) {
                    const el = document.getElementById(id);
                    if (el) {
                        el.textContent = message;
                        el.classList.add('show');
                    }
                }

                if(typeInput && (!typeInput.value || typeInput.value === '')) {
                    showError('error_type_missing', '⚠ Будь ласка, оберіть причину.');
                    isValid = false;
                }

                const descInput = document.getElementById('id_description');
                if (descInput && descInput.value.trim() === '') {
                    showError('error_description', '⚠ Це поле обов\'язкове для заповнення.');
                    isValid = false;
                }

                if (!dateStartInput.value) {
                    showError('error_date_start', '⚠ Оберіть дату початку.');
                    isValid = false;
                }

                if (!dateEndInput.value) {
                    showError('error_date_end', '⚠ Оберіть дату кінця.');
                    isValid = false;
                }

                if (!countDayInput.value || parseInt(countDayInput.value, 10) < 1) {
                    showError('error_count_day', '⚠ Мінімальна кількість днів — 1.');
                    isValid = false;
                }

                if (!isValid) return;
                
                const formData = new FormData(docForm);

                fetch(docForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                }).then(response => response.json())
                  .then(data => {
                    if(data.status === 'success') {
                        console.log(data);
                        const doc = data.document;

                        const table = document.getElementById('documentTable');
                        const tbody = document.getElementById('documentTableBody');
                        const noDocsMsg = document.getElementById('noDocumuentMsg');

                        if (noDocsMsg) noDocsMsg.style.display = 'none';
                        if (table) table.style.display = 'table';
                        
                        console.log(table, tbody);
                        if(tbody) {
                            const newRow = document.createElement('tr');
                            newRow.innerHTML = `
                                <td>${doc.type_missing}</td>
                                <td>${doc.date_start_display}</td>
                                <td>${doc.date_end_display}</td>
                                <td>${doc.count_day}</td>
                                <td>${doc.description}</td>
                            `;
                            
                            tbody.prepend(newRow);
                        }

                        disableRanges.push({
                            from: doc.date_start_raw,
                            to: doc.date_end_raw
                        });
                        fpStart.set('disable', disableRanges);
                        fpEnd.set('disable', disableRanges);

                        const daysUsed = parseInt(doc.count_day) || 0;
                        if (doc.type_missing.trim() === 'vacation') {
                            vacationLeft = Math.max(0, vacationLeft - daysUsed);
                        } else if (doc.type_missing.trim() === 'hospital') {
                            sickLeft = Math.max(0, sickLeft - daysUsed);
                        }

                        docForm.reset();
                        fpStart.clear();
                        fpEnd.clear();
                        checkLimits();
                        closeModal();
                    } else if (data.status === 'error') {
                        for (const [field, messages] of Object.entries(data.errors)) {
                            showError(`error_${field}`, `⚠ ${messages[0]}`);
                        }
                    }
                  })
                  .catch(error => {
                    console.error('Помилка під час збереження:', error);
                  });
            });
        }
    }
});