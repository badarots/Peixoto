var connection = null;
var ellog = null;
var wsuri = null;

window.onload = function(){
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
    //wsuri = 'ws://localhost:8010/ws'
    log("Protocol: " + window.location.protocol + " URL: " + wsuri);
};

function connect(user_id, user_secret) {
    //user_id = 'badaro';
    //user_secret = '1234';

    connection = new autobahn.Connection({
        url: wsuri,
        realm: "realm1",

        authmethods: ["wampcra"],
        authid: user_id,
        onchallenge: onchallenge
    });

    function onchallenge (session, method, extra) {
        //console.log("onchallenge", method, extra);
        if (method === "wampcra") {
            //console.log("authenticating via '" + method + "' and challenge '" + extra.challenge + "'");

            return autobahn.auth_cra.sign(user_secret, extra.challenge);
        } else {
            throw "don't know how to authenticate using '" + method + "'";
        }
    }

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
        $("#content").load('formularios.html');
        $("#status_conexao").html("Conectado");
    };

    connection.onclose = function(reason, details) {
        log("Desconectado ", reason, details)
        $("#content").load('login.html');
        $("#status_conexao").html("Desconectado");
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

function close_conection(){
    if (connection) connection.close();
}

function get_status() {
    if (connection.session != null){
        return(connection.session.call('com.exec.status', [], ));
    } else {
        log('Não conectado');
    }
};

function log(m) {
    ellog.innerHTML = m + '\n' + ellog.innerHTML;
    ellog.scrollTop = 0;
};
