var connection = null;
var ellog = null;
var dispositivo

window.onload = function(){ ellog = document.getElementById('log'); };

function connect(user_id, user_secret, disp) {
    dispositivo = disp;    

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
            throw "don't know how to authsenticate using '" + method + "'";
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

        setLink("ativar");
        $("#status_conexao").html("Conectado");
    };

    connection.onclose = function(reason, details) {
        log("Desconectado ", reason, details);
        
        setLink("login");
        $("#status_conexao").html("Desconectado");
    };

    log('Conectando...')
    connection.open();

    $(".pages").click(function(){ setLink($(this).attr('page')) });
    

};

// Define formulario inicio

// Quando algum elemento da classe link é clicado carrega formulario
// contido no atributo "page".
//https://stackoverflow.com/questions/8079618/how-can-we-change-only-inner-part-of-a-web-page

function setLink(page){
    if (page == "login") {
        var show = "none";
    } else {
        var show = "block";
    }
    document.getElementById("pages_header").style.display = show;

    $("#content").load(page + ".html");
    // muda a o cor dos botoes para sinalizar qual form. está aberto
    $(".pages").removeClass("active");
    $('#page_' + page).addClass("active");
    console.log(page);
};

function send(msg) {
    if (connection.session != null){
        connection.session.call('com.' + dispositivo + '.atualizar', [msg]).then(
            function (res) {
                 log('Raspi - ' + res);
            }
        );
    } else {
        log('Não conectado');
    }
};

function ativar(msg) {
    if (connection.session != null){
        return(connection.session.call('com.' + dispositivo + '.ativar', [msg]));
    } else {
        log('Não conectado');
    }
};

function get_status(info) {
    if (connection.session != null){
        return(connection.session.call('com.' + dispositivo + '.status', [info]));
    } else {
        log('Não conectado');
    }
};

function close_conection(){
    if (connection) connection.close();
}

function log(m) {
    ellog.innerHTML = m + '\n' + ellog.innerHTML;
    ellog.scrollTop = 0;
};
