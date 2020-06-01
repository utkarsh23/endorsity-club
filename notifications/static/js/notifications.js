const notifSocket = new WebSocket(
    "wss://" + window.location.host + "/ws/notifications/"
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
