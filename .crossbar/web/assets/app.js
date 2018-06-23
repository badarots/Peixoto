/*
 * Adcionada a opção de ler mais de um formulário.
 * Cada formulário da página que tenha nome será adcionado dentro de um
 * json pai com seu nome como chave:
 * {
 * 'form1': {...},
 * 'form2': {...}
 * }
*/

/**
 * A handler function to prevent default submission and run our custom script.
 * @param  {Event} event  the submit event triggered by the user
 * @return {void}
 */
var handleFormSubmit = function handleFormSubmit(event) {

  /*
   * Encontra todos os formulários da página usando o nome da classe:
   * 'contact-form', e extrai seus dados quando o botão 'submit' é clicado.
  */
  var forms = document.getElementsByClassName('form-basic');

  // Stop the form from submitting since we’re handling that with AJAX.
  event.preventDefault();

  // Cria o jason pai
  var data = {};

  for (var i = 0; i < forms.length; i++){
    //adciona o json filho se formulário possui um nome
    if (forms[i].name) {
      data[forms[i].name] = formToJSON(forms[i].elements);
    }
  }

  // Use `JSON.stringify()` to make the output valid, human-readable JSON.
  var msg = JSON.stringify(data, null, "  ");

  // Demo only: print the form data onscreen as a formatted JSON object.
  /*
  var dataContainer = document.getElementById("result");
  dataContainer.textContent = msg;
  */
  // Mostra msg no console
  console.log('Mensagem:\n' + msg)

  // ...this is where we’d actually do something with the form data...
  // Envia os dados como um string em formato json
  send(msg);
};

var ativar_tratador = function ativar_tratador(event) {
  forms[1].prop('disabled', tratador.checked);
};

var ola = function ola(event) {
  // body...
  console.log('Click');
};

/*
 * Usa jquery para carregar dinamicamente diferentes formulários
*/
$(document).ready(function(){
    connect();
    // Define forumario aerador como inicial
    setPage('tratador')

    // Quando algum elemento da classe link é clicado carrega formulario
    // contido no atributo "page".
    //https://stackoverflow.com/questions/8079618/how-can-we-change-only-inner-part-of-a-web-page
    $(".links").click(function(){setPage($(this).attr('page'))});

    function setPage(page){
        $("#content").load(page + ".html");

        // muda a o cor dos botoes para sinalizar qual form. está aberto
        $(".links").removeClass("active");
        $('#' + page).addClass("active")
     };

    // Gera e envia json ou clicar em Enviar
    $("#envia").on('click', handleFormSubmit);


});
