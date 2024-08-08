$(document).ready(function() {
    $('.tab-list a').click(function(e) {
        e.preventDefault();
        var tabId = $(this).attr('href');
        $('.tab-list a').removeClass('active');
        $(this).addClass('active');
        $('.tab-pane').removeClass('active');
        $(tabId).addClass('active');
    });

    $('.tab-list a:first').click();
});
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


