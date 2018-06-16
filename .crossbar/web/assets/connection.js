var connection = null;
var ellog = null;

window.onload = function() {
    var wsuri = null;

    ellog = document.getElementById('log');

    var protocol = window.location.protocol;
    var hostname = window.location.hostname;
    var port = window.location.port;

    if (protocol === "file:") {
        wsuri = "ws://hackerspace.if.usp.br/crossbar/ws";
    } else {
        if (protocol == "https:"){
            wsuri = "wss://" + hostname;
        } else {
            wsuri = "ws://" + hostname;
        }
        if (hostname == "localhost" || hostname == "127.0.0.1" || hostname == "0.0.0.0") {
            wsuri += ":" + port;
        }
        wsuri += window.location.pathname + "ws";
    }

    log("Protocol: " + window.location.protocol + " URL: " + wsuri);


    connection = new autobahn.Connection({
        url: wsuri,
        realm: "realm1"
    });


    //inscrição no topico status para saber como anda os paranauês
    connection.onopen = function(session, details) {
        log("Conectado")

        function status (args) {
            log('Status: ' + args[0]);
        }
        session.subscribe('com.myapp.status', status).then(
            function (sub) {
                log('Inscrito no tópico status');
            },
            function (err) {
                log('Falha ao se inscrever no tópico status', err);
            }
        );
    };

    connection.onclose = function(reason, details) {
        log("Desconectado: ", reason, details)
    };

    log('Conectando...')
    connection.open();
 };

function send(msg) {
    if (connection.session != null){
        connection.session.call('com.exec.atualizar', [msg], ).then(
            function (res) {
                 log('Raspi - ' + res)
            }
        );
    } else {
        log('Não conectado');
    }
};

function log(m) {
    ellog.innerHTML += m + '\n';
    ellog.scrollTop = ellog.scrollHeight;
};
