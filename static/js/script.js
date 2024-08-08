// Открытие формы для добавления пробега
function openForm(pvmNumber) {
    console.log('Open form for PVM:', pvmNumber);
    document.getElementById('formPopup').style.display = 'block';
    document.getElementById('formPvmNumber').innerText = pvmNumber;
    document.getElementById('pvm_number').value = pvmNumber;
}

function closeForm() {
    document.getElementById('formPopup').style.display = 'none';
}

// Открытие меню для ПВМ
function openMenu(pvmNumber, run) {
    console.log('Open menu for PVM:', pvmNumber, 'with run:', run);
    document.getElementById('menuPopup').style.display = 'block';
    document.getElementById('menuPvmNumber').innerText = pvmNumber;
    document.getElementById('menu_pvm_number').value = pvmNumber;

    const pvmElement = document.getElementById(`pvm_${pvmNumber}`);
    const isInWork = !pvmElement.classList.contains('inStock') && !pvmElement.classList.contains('inRepair');
    const isInStock = pvmElement.classList.contains('inStock') || pvmElement.classList.contains('inRepair');
    
    if (isInWork) {
        document.getElementById('addRunButton').style.display = 'block';
        document.getElementById('returnToWorkButton').style.display = 'none';
    } else {
        document.getElementById('addRunButton').style.display = 'none';
        if (isInStock) {
            document.getElementById('returnToWorkButton').style.display = 'block';
        } else {
            document.getElementById('returnToWorkButton').style.display = 'none';
        }
    }
}

function closeMenu() {
    document.getElementById('menuPopup').style.display = 'none';
}

function openSubMenu(action) {
    closeMenu();
    if (action === 'addRun') {
        openForm(document.getElementById('menu_pvm_number').value);
    }
}

function openMoveMenu() {
    document.getElementById('movePopup').style.display = 'block';
    document.getElementById('movePvmNumber').innerText = document.getElementById('menu_pvm_number').value;
    document.getElementById('move_pvm_number').value = document.getElementById('menu_pvm_number').value;
    closeMenu();
}

function closeMoveForm() {
    document.getElementById('movePopup').style.display = 'none';
}

function moveMachine() {
    const pvmNumber = document.getElementById('move_pvm_number').value;
    const newLocation = document.getElementById('move_location').value;
    console.log('Moving PVM:', pvmNumber, 'to:', newLocation);

    const pvmElement = document.getElementById(`pvm_${pvmNumber}`);
    if (!pvmElement) {
        console.error('PVM element not found:', pvmNumber);
        return;
    }

    if (newLocation === 'inStock') {
        pvmElement.classList.add('inStock');
        pvmElement.classList.remove('inRepair');
        document.getElementById('inStockContainer').appendChild(pvmElement);
    } else if (newLocation === 'inRepair') {
        pvmElement.classList.add('inRepair');
        pvmElement.classList.remove('inStock');
        document.getElementById('inRepairContainer').appendChild(pvmElement);
    } else if (newLocation === 'inWork') {
        pvmElement.classList.remove('inStock', 'inRepair');
        document.getElementById('inWorkContainer').appendChild(pvmElement);
    }
    
    fetch('/move_pvm', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pvm_number: pvmNumber, new_location: newLocation }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            alert(`ПВМ №${pvmNumber} перемещена ${newLocation === 'inStock' ? 'на склад' : 'в ремонт'}`);
        } else {
            console.log('Move error:', data);
            alert('Ошибка перемещения ПВМ');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
    closeMoveForm();
}

function returnToWork() {
    const pvmNumber = document.getElementById('menu_pvm_number').value;
    console.log('Returning PVM to work:', pvmNumber);

    const pvmElement = document.getElementById(`pvm_${pvmNumber}`);
    if (!pvmElement) {
        console.error('PVM element not found:', pvmNumber);
        return;
    }

    pvmElement.classList.remove('inStock', 'inRepair');
    document.getElementById('inWorkContainer').appendChild(pvmElement);

    fetch('/move_pvm', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pvm_number: pvmNumber, new_location: 'inWork' }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            alert(`ПВМ №${pvmNumber} возвращена в работу`);
            // Обнуляем пробег в квадратике ПВМ
            const runElement = pvmElement.querySelector('.pvm-run');
            if (runElement) {
                runElement.textContent = 'Текущий пробег: 0 тонн';
            }
        } else {
            console.log('Move error:', data);
            alert('Ошибка возврата ПВМ в работу');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
    closeMenu();
}

function resetRun() {
    const pvmNumber = document.getElementById('menu_pvm_number').value;
    const password = prompt('Введите пароль для обнуления пробега:');
    if (password === '447') {
        fetch('/reset_run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ pvm_number: pvmNumber, password: password }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Response data:', data);
            if (data.success) {
                alert(`Пробег для ПВМ №${pvmNumber} обнулен`);
                window.location.reload();
            } else {
                alert('Ошибка обнуления пробега');
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });
    } else {
        alert('Неверный пароль');
    }
}

function openStatistics() {
    const password = prompt('Введите пароль для доступа к статистике:');
    if (password === '447') {
        window.location.href = '/statistics';
    } else {
        alert('Неверный пароль');
    }
}

function updateDateTime() {
    const now = new Date();
    const formattedDate = now.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
    const formattedTime = now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    document.getElementById('datetime').textContent = `${formattedDate} ${formattedTime}`;
}

setInterval(updateDateTime, 1000);

$(document).ready(function() {
    updateDateTime();
    $(".menu-button").on("click", function() {
        const action = $(this).attr("onclick").split("'")[1];
        openSubMenu(action);
    });
});

function exportToExcel() {
    window.location.href = "/export_excel";
}

function resetMileage(period) {
    fetch('/reset_mileage', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ period: period }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Пробеги успешно обнулены');
            window.location.reload();
        } else {
            alert('Ошибка обнуления пробегов');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        alert('Ошибка обнуления пробегов');
    });
}

function addRun(pvmNumber) {
    // Получение данных формы
    const numBlanks = document.getElementById('num_blanks').value;
    const blankSize = document.getElementById('blank_size').value;
    const techScrap = document.getElementById('tech_scrap').value;

    const runData = {
        pvm_number: pvmNumber,
        num_blanks: numBlanks,
        blank_size: blankSize,
        tech_scrap: techScrap
    };

    fetch('/add_run', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(runData),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCurrentRun(pvmNumber);
        } else {
            alert('Ошибка добавления пробега');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        alert('Ошибка добавления пробега');
    });
}

function updateCurrentRun(pvmNumber) {
    fetch(`/current_run/${pvmNumber}`)
    .then(response => response.json())
    .then(data => {
        const pvmElement = document.getElementById(`pvm_${pvmNumber}`);
        const runElement = pvmElement.querySelector('.pvm-run');
        if (runElement) {
            runElement.textContent = `Текущий пробег: ${data.current_run} тонн`;
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
}
