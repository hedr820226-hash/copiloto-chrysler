const express = require("express");
const app = express();

app.use(express.json());

// ✅ ESTA ES LA RUTA QUE TE FALTA
app.post("/chat", (req, res) => {

    const mensaje = req.body.message;

    const respuesta = `Inés 🌷 escuché: ${mensaje}. ¿Cómo te sientes hoy?`;

    res.json({ response: respuesta });
});

// opcional (para probar en navegador)
app.get("/", (req, res) => {
    res.send("Nova servidor activo 💙");
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log("Servidor corriendo en puerto " + PORT);
});
