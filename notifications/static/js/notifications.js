const notifSocket = new WebSocket(
    "ws://" + window.location.host + "/ws/notifications/" // protocol -> ws:// ---> In Current Development
),
notif_functions = {
    new_notifications_received: new_notifications_received,
};

function parse_html(notif) {
    return `
        <a href="${ notif.fields.link }">
            <li class="mdl-menu__item">${ notif.fields.message }</li>
        </a>
    `;
}

notifSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    notif_functions[data.function](data.arguments);
};

function new_notifications_received(args) {
    let html = "",
        notifs = JSON.parse(args.notifs);

    notifs.forEach((notif) => {
        html += parse_html(notif);
    });

    document.querySelector("#notif-log").innerHTML =
        html + document.querySelector("#notif-log").innerHTML;
    $('#notif-log').html($('#notif-log>a:not(.all-notifs-link)').slice(0, 8));
    $('#notif-log').append(`
        <a class="all-notifs-link" href="/notifications/">
            <li class="mdl-menu__item view-all-notifs">View All Notifications</li>
        </a>
    `);
    if (!$('#notifications').hasClass('mdl-badge')) $('#notifications').addClass('mdl-badge');
    $('#notifications').attr('data-badge', parseInt($('#notifications').attr('data-badge'), 10) + 1);
}

$('#notifications').click(function() {
    $(this).removeClass('mdl-badge');
    $('#notifications').attr('data-badge', 0);
    notifSocket.send(
        JSON.stringify({
            function: "all_seen",
            arguments: {},
        })
    );
});
