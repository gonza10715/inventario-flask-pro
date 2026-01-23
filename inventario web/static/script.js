function enviarMensaje() {
    const input = document.getElementById("chat-input");
    const box = document.getElementById("chat-box");

    if (!input.value.trim()) return;

    box.innerHTML += "<p><b>Vos:</b> " + input.value + "</p>";

    let respuesta = "No entendí tu mensaje.";

    if (input.value.toLowerCase().includes("stock")) {
        respuesta = "Podés ver el stock en la sección Inventario.";
    }

    box.innerHTML += "<p><b>Bot:</b> " + respuesta + "</p>";

    input.value = "";
}
