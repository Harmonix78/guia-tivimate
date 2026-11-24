# Guía de TiviMate

Guía de programación (XMLTV) para TiviMate, solo con los canales elegidos y con el nombre exacto que tienen en la
lista de IPTV, para que TiviMate los empareje sin asignarlos uno por uno.

- **Dirección para TiviMate:** `https://harmonix78.github.io/guia-tivimate/guide.xml.gz`
- **Se actualiza sola** todos los días a las 9:17 UTC (GitHub Actions), con datos de [epgshare01](https://epgshare01.online).
- **Fuentes:** [epgshare01](https://epgshare01.online) y, para los canales que esta no trae (Fox Sports Latinoamérica,
  Canal 26, Crónica, America TeVe…), el recolector de [iptv-org/epg](https://github.com/iptv-org/epg) (`iptvorg.channels.xml`).
- **Canales:** `channels.json` — `"nombre en la lista": ["archivo de epgshare01", "id del canal"]`.
  Para agregar o quitar uno, edita ese archivo: la guía se regenera al guardar.
- **Siempre activa:** GitHub apaga las tareas programadas tras 60 días sin cambios en el repositorio; el trabajo
  *mantener-activo* hace un cambio fechado (`.ultima-actividad`) cuando el último tiene más de 40 días.
- **A mano:** pestaña *Actions* → *Guía diaria* → *Run workflow*.
