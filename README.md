# Guía de TiviMate

Guía de programación (XMLTV) para TiviMate, solo con los canales elegidos y con el nombre exacto que tienen en la
lista de IPTV, para que TiviMate los empareje sin asignarlos uno por uno.

- **Dirección para TiviMate:** `https://harmonix78.github.io/guia-tivimate/guide.xml.gz`
- **Se actualiza sola** todos los días a las 9:17 UTC (GitHub Actions), con datos de [epgshare01](https://epgshare01.online).
- **Canales:** `channels.json` — `"nombre en la lista": ["archivo de epgshare01", "id del canal"]`.
  Para agregar o quitar uno, edita ese archivo: la guía se regenera al guardar.
- **A mano:** pestaña *Actions* → *Guía diaria* → *Run workflow*.
